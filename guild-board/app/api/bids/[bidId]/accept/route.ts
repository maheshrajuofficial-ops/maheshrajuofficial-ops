import { NextRequest } from 'next/server';

import { fail, ok, withErrorHandling } from '@/lib/api/response';
import { createEscrowHold } from '@/lib/stripe/escrow';
import { getStripe } from '@/lib/stripe/server';
import { createAdminClient } from '@/lib/supabase/admin';
import { createClient } from '@/lib/supabase/server';

export const runtime = 'nodejs';

/**
 * Accept a bid and open escrow.
 *
 * The ordering below is the whole design, so it's worth stating:
 *
 *   1. authorise the caller and re-read the task and bid server-side
 *   2. create the manual-capture PaymentIntent
 *   3. write the `pending_hold` transaction row
 *   4. flip the bid to 'accepted' (the trigger assigns the task)
 *
 * If step 4 fails we cancel the intent in step 2 and mark the row refunded,
 * because the alternative — a task assigned with no escrow behind it — is the
 * one state neither party can recover from on their own.
 */
export const POST = withErrorHandling(
  async (_request: NextRequest, { params }: { params: { bidId: string } }) => {
    const supabase = createClient();

    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) return fail('unauthorized', 'Log in to accept a bid.');

    const { data: bid } = await supabase
      .from('bids')
      .select(
        `id, task_id, member_id, amount, status,
         task:tasks!bids_task_id_fkey (id, requester_id, status, title, currency, risk_tier, category_id),
         member:users!bids_member_id_fkey (id, stripe_account_id, stripe_payouts_enabled, is_id_verified, licensed_trades)`
      )
      .eq('id', params.bidId)
      .single();

    if (!bid) return fail('not_found', 'That bid no longer exists.');

    const task = bid.task as unknown as {
      id: string;
      requester_id: string;
      status: string;
      title: string;
      currency: string;
      risk_tier: string;
      category_id: string;
    };
    const member = bid.member as unknown as {
      id: string;
      stripe_account_id: string | null;
      stripe_payouts_enabled: boolean;
      is_id_verified: boolean;
      licensed_trades: string[];
    };

    if (task.requester_id !== user.id) {
      return fail('forbidden', 'Only the requester can accept a bid on this task.');
    }
    if (task.status !== 'open') {
      return fail('conflict', 'This task already has an accepted bid.');
    }
    if (bid.status !== 'pending') {
      return fail('conflict', 'That bid is no longer pending.');
    }
    if (!member.stripe_account_id || !member.stripe_payouts_enabled) {
      return fail(
        'payout_setup_required',
        'This worker has not finished payout setup yet, so funds could not be released to them.'
      );
    }

    // Licence gate, re-checked at the money boundary. The bid trigger already
    // enforced it, but a licence can be revoked between bid and acceptance.
    if (task.risk_tier === 'high_licensed') {
      const { data: category } = await supabase
        .from('categories')
        .select('slug')
        .eq('id', task.category_id)
        .single();

      const licensed =
        member.is_id_verified &&
        category &&
        member.licensed_trades.includes(category.slug);

      if (!licensed) {
        return fail(
          'verification_required',
          'This task requires a verified trade licence and this worker no longer holds one on file.'
        );
      }
    }

    /* --- 2. Authorise the hold ------------------------------------------ */
    const hold = await createEscrowHold({
      taskId: task.id,
      bidId: bid.id,
      requesterId: user.id,
      memberId: member.id,
      destinationAccountId: member.stripe_account_id,
      amount: Number(bid.amount),
      currency: task.currency,
      taskTitle: task.title,
    });

    /* --- 3. Ledger row (service role: clients never write this table) ---- */
    const admin = createAdminClient();

    const { error: ledgerError } = await admin.from('transactions').insert({
      task_id: task.id,
      bid_id: bid.id,
      payer_id: user.id,
      payee_id: member.id,
      stripe_payment_intent_id: hold.paymentIntent.id,
      stripe_destination_account: member.stripe_account_id,
      amount: hold.fees.amount,
      platform_fee: hold.fees.platformFee,
      currency: hold.fees.currency,
      escrow_status: 'pending_hold',
      authorized_at: new Date().toISOString(),
    });

    if (ledgerError) {
      await getStripe().paymentIntents.cancel(hold.paymentIntent.id).catch(() => {});
      console.error('[accept] ledger write failed', ledgerError);
      return fail('internal_error', 'Could not open escrow. Nothing was charged.');
    }

    /* --- 4. Assign the task --------------------------------------------- */
    const { data: accepted, error: acceptError } = await supabase
      .from('bids')
      .update({ status: 'accepted' })
      .eq('id', bid.id)
      .eq('status', 'pending')
      .select(
        `*, member:users!bids_member_id_fkey (id, full_name, avatar_url, rep_score, rep_count, tasks_completed, is_id_verified, is_background_checked, licensed_trades)`
      )
      .single();

    if (acceptError || !accepted) {
      await getStripe().paymentIntents.cancel(hold.paymentIntent.id).catch(() => {});
      await admin
        .from('transactions')
        .update({ escrow_status: 'refunded', failure_code: 'bid_accept_failed' })
        .eq('stripe_payment_intent_id', hold.paymentIntent.id);

      return fail('conflict', acceptError?.message ?? 'Could not accept that bid.');
    }

    return ok({
      bid: accepted,
      clientSecret: hold.clientSecret,
      paymentIntentId: hold.paymentIntent.id,
      amount: hold.fees.amount,
      platformFee: hold.fees.platformFee,
      payoutAmount: hold.fees.payoutAmount,
    });
  }
);
