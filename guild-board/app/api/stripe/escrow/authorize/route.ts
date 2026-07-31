import { NextRequest } from 'next/server';
import { z } from 'zod';

import { fail, ok, withErrorHandling } from '@/lib/api/response';
import { getStripe } from '@/lib/stripe/server';
import { createClient } from '@/lib/supabase/server';

export const runtime = 'nodejs';

const Schema = z.object({ taskId: z.string().uuid() });

/**
 * Re-issue the client secret for an escrow hold that was created but never
 * confirmed — the requester closed the tab mid-3DS, or the card was declined
 * and they want to retry with another one.
 *
 * The hold itself is opened by `POST /api/bids/[bidId]/accept`; this route
 * deliberately cannot create one, so there is exactly one code path that can
 * put a task into escrow.
 */
export const POST = withErrorHandling(async (request: NextRequest) => {
  const supabase = createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) return fail('unauthorized', 'Log in to continue.');

  const parsed = Schema.safeParse(await request.json());
  if (!parsed.success) return fail('validation_failed', 'Missing task id.');

  const { data: transaction } = await supabase
    .from('transactions')
    .select('id, payer_id, escrow_status, stripe_payment_intent_id, amount, platform_fee, payout_amount, currency')
    .eq('task_id', parsed.data.taskId)
    .in('escrow_status', ['pending_hold', 'held'])
    .order('created_at', { ascending: false })
    .limit(1)
    .maybeSingle();

  if (!transaction) return fail('not_found', 'No open escrow for that task.');
  if (transaction.payer_id !== user.id) {
    return fail('forbidden', 'Only the requester can authorise this payment.');
  }
  if (!transaction.stripe_payment_intent_id) {
    return fail('conflict', 'This escrow has no payment attached.');
  }

  const intent = await getStripe().paymentIntents.retrieve(
    transaction.stripe_payment_intent_id
  );

  if (intent.status === 'requires_capture' || intent.status === 'succeeded') {
    return ok({
      alreadyAuthorized: true,
      clientSecret: null,
      transactionId: transaction.id,
      escrowStatus: transaction.escrow_status,
    });
  }

  if (!intent.client_secret) {
    return fail('payment_failed', 'This payment can no longer be completed.');
  }

  return ok({
    alreadyAuthorized: false,
    clientSecret: intent.client_secret,
    transactionId: transaction.id,
    escrowStatus: transaction.escrow_status,
    amount: Number(transaction.amount),
    platformFee: Number(transaction.platform_fee),
    payoutAmount: Number(transaction.payout_amount),
    currency: transaction.currency,
  });
});
