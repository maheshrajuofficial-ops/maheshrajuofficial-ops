import { NextRequest, NextResponse } from 'next/server';
import type Stripe from 'stripe';

import { ESCROW_AUTO_RELEASE_HOURS } from '@/lib/constants';
import { getStripe } from '@/lib/stripe/server';
import { createAdminClient } from '@/lib/supabase/admin';

export const runtime = 'nodejs';
// The raw body is required for signature verification, so this route must not
// be statically analysed or cached.
export const dynamic = 'force-dynamic';

/**
 * Stripe webhook — the authority on escrow state.
 *
 * Everything that changes `transactions.escrow_status` lands here, because
 * Stripe is the only party that actually knows whether money moved. The API
 * routes write optimistic copies for UI freshness; this reconciles them.
 *
 * Three rules this handler follows, all of them learned the hard way in
 * payments work:
 *
 *   1. Verify the signature before parsing anything. An unverified body is
 *      attacker-controlled input.
 *   2. Return 2xx for events we don't handle. A 4xx makes Stripe retry
 *      forever and eventually disable the endpoint.
 *   3. Be idempotent. Stripe delivers at-least-once, and duplicates are
 *      normal, not exceptional.
 */
export async function POST(request: NextRequest) {
  const signature = request.headers.get('stripe-signature');
  const secret = process.env.STRIPE_WEBHOOK_SECRET;

  if (!signature || !secret) {
    return NextResponse.json({ error: 'Missing signature' }, { status: 400 });
  }

  const payload = await request.text();

  let event: Stripe.Event;
  try {
    event = getStripe().webhooks.constructEvent(payload, signature, secret);
  } catch (error) {
    console.error('[webhook] signature verification failed', error);
    return NextResponse.json({ error: 'Invalid signature' }, { status: 400 });
  }

  try {
    switch (event.type) {
      /* --- The requester's card was authorised: funds are now held ------- */
      case 'payment_intent.amount_capturable_updated':
        await onAmountCapturable(event.data.object as Stripe.PaymentIntent);
        break;

      /* --- Capture went through: the member has been paid --------------- */
      case 'payment_intent.succeeded':
        await onSucceeded(event.data.object as Stripe.PaymentIntent);
        break;

      case 'payment_intent.canceled':
        await onCanceled(event.data.object as Stripe.PaymentIntent);
        break;

      case 'payment_intent.payment_failed':
        await onFailed(event.data.object as Stripe.PaymentIntent);
        break;

      case 'charge.refunded':
        await onRefunded(event.data.object as Stripe.Charge);
        break;

      /* --- Connect account capability changes --------------------------- */
      case 'account.updated':
        await onAccountUpdated(event.data.object as Stripe.Account);
        break;

      case 'payout.paid':
      case 'payout.failed':
        await onPayout(event.data.object as Stripe.Payout, event.type);
        break;

      default:
        // Rule 2: acknowledge and move on.
        break;
    }
  } catch (error) {
    console.error(`[webhook] handler failed for ${event.type}`, error);
    // Signal Stripe to retry — the event was valid, our processing wasn't.
    return NextResponse.json({ error: 'Handler failed' }, { status: 500 });
  }

  return NextResponse.json({ received: true });
}

/* -------------------------------------------------------------------------- */

async function onAmountCapturable(intent: Stripe.PaymentIntent) {
  const admin = createAdminClient();

  const { data: transaction } = await admin
    .from('transactions')
    .select('id, task_id, escrow_status')
    .eq('stripe_payment_intent_id', intent.id)
    .maybeSingle();

  if (!transaction) {
    console.warn('[webhook] no transaction for intent', intent.id);
    return;
  }

  if (transaction.escrow_status === 'released') return;

  // The trigger on `transactions` moves the task to 'in_escrow'.
  await admin
    .from('transactions')
    .update({
      escrow_status: 'held',
      held_at: new Date().toISOString(),
      stripe_charge_id:
        typeof intent.latest_charge === 'string' ? intent.latest_charge : null,
    })
    .eq('id', transaction.id);

  // Start the dispute-free countdown from the moment funds are actually held.
  const releasesAt = new Date(
    Date.now() + ESCROW_AUTO_RELEASE_HOURS * 3_600_000
  ).toISOString();

  await admin
    .from('tasks')
    .update({ released_after: releasesAt })
    .eq('id', transaction.task_id)
    .is('released_after', null);
}

async function onSucceeded(intent: Stripe.PaymentIntent) {
  const admin = createAdminClient();

  await admin
    .from('transactions')
    .update({
      escrow_status: 'released',
      released_at: new Date().toISOString(),
      release_reason: intent.metadata?.release_reason ?? 'capture',
      stripe_charge_id:
        typeof intent.latest_charge === 'string' ? intent.latest_charge : null,
      stripe_transfer_id:
        typeof intent.transfer_data?.destination === 'string'
          ? (intent as unknown as { transfer?: string }).transfer ?? null
          : null,
    })
    .eq('stripe_payment_intent_id', intent.id)
    .neq('escrow_status', 'refunded');
}

async function onCanceled(intent: Stripe.PaymentIntent) {
  const admin = createAdminClient();

  const { data: transaction } = await admin
    .from('transactions')
    .update({
      escrow_status: 'refunded',
      refunded_at: new Date().toISOString(),
      release_reason: 'authorization_canceled',
    })
    .eq('stripe_payment_intent_id', intent.id)
    .select('task_id')
    .maybeSingle();

  if (!transaction) return;

  // The hold is gone, so the task goes back on the board rather than sitting
  // assigned to a worker who will never be paid.
  await admin
    .from('tasks')
    .update({ status: 'open', assigned_to: null, released_after: null })
    .eq('id', transaction.task_id)
    .in('status', ['assigned', 'in_escrow']);
}

async function onFailed(intent: Stripe.PaymentIntent) {
  const admin = createAdminClient();

  await admin
    .from('transactions')
    .update({
      failure_code:
        intent.last_payment_error?.code ?? intent.last_payment_error?.type ?? 'unknown',
    })
    .eq('stripe_payment_intent_id', intent.id);
}

async function onRefunded(charge: Stripe.Charge) {
  if (!charge.payment_intent) return;

  const admin = createAdminClient();
  const intentId =
    typeof charge.payment_intent === 'string'
      ? charge.payment_intent
      : charge.payment_intent.id;

  await admin
    .from('transactions')
    .update({
      escrow_status: 'refunded',
      refunded_at: new Date().toISOString(),
      release_reason: 'refund',
    })
    .eq('stripe_payment_intent_id', intentId);
}

/**
 * Connect capability changes.
 *
 * `payouts_enabled` is what actually gates bidding — a worker whose account
 * falls out of good standing (expired document, failed verification) stops
 * being biddable here, before a requester's money is committed to them.
 */
async function onAccountUpdated(account: Stripe.Account) {
  const admin = createAdminClient();

  const { error } = await admin
    .from('users')
    .update({
      stripe_payouts_enabled: account.payouts_enabled ?? false,
      stripe_charges_enabled: account.charges_enabled ?? false,
    })
    .eq('stripe_account_id', account.id);

  if (error) console.error('[webhook] account.updated write failed', error);
}

async function onPayout(payout: Stripe.Payout, eventType: string) {
  // Payout events belong to the connected account, not to a single task, so
  // there is nothing to reconcile on `transactions` — they are logged for
  // support and for the worker-facing payout history.
  console.info('[webhook] payout', eventType, payout.id, payout.status, payout.amount);
}
