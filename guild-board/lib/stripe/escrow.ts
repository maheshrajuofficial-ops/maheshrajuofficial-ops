import 'server-only';

import { getStripe, type Stripe } from '@/lib/stripe/server';
import { calculateFees, type FeeBreakdown } from '@/lib/stripe/fees';

/**
 * Escrow, expressed in Stripe primitives.
 *
 * There is no "escrow" object in Stripe, so we build one out of a
 * manual-capture PaymentIntent on the platform account:
 *
 *   accept bid   -> create PaymentIntent, capture_method: 'manual'
 *                   -> customer authorises -> funds *held* on their card
 *   sign-off     -> capture, with transfer_data routing the member's share
 *                   to their Connect account and application_fee_amount
 *                   retaining ours
 *   dispute lost -> cancel (uncaptured) or refund (captured)
 *
 * Two properties this buys us: the requester's money is never in our custody
 * before the work is signed off, and the split is atomic with the capture, so
 * there's no window where we hold funds we owe a worker.
 *
 * Authorisations expire. Card holds last ~7 days; the auto-release window is
 * 72h, which keeps the whole lifecycle inside that budget.
 */

export interface CreateEscrowHoldParams {
  taskId: string;
  bidId: string;
  requesterId: string;
  memberId: string;
  /** The member's Connect account — funds are routed here on capture. */
  destinationAccountId: string;
  amount: number;
  currency: string;
  /** Stripe Customer for the requester, if one already exists. */
  customerId?: string;
  taskTitle: string;
}

export interface EscrowHold {
  paymentIntent: Stripe.PaymentIntent;
  clientSecret: string;
  fees: FeeBreakdown;
}

export async function createEscrowHold(
  params: CreateEscrowHoldParams
): Promise<EscrowHold> {
  const stripe = getStripe();
  const fees = calculateFees(params.amount, params.currency);

  const paymentIntent = await stripe.paymentIntents.create(
    {
      amount: fees.amountMinor,
      currency: fees.currency.toLowerCase(),
      // The whole mechanism turns on this one flag.
      capture_method: 'manual',
      customer: params.customerId,
      automatic_payment_methods: { enabled: true },
      application_fee_amount: fees.platformFeeMinor,
      transfer_data: { destination: params.destinationAccountId },
      description: `Guild Board escrow — ${params.taskTitle}`,
      statement_descriptor_suffix: 'GUILD BOARD',
      metadata: {
        task_id: params.taskId,
        bid_id: params.bidId,
        requester_id: params.requesterId,
        member_id: params.memberId,
        platform_fee_minor: String(fees.platformFeeMinor),
        payout_minor: String(fees.payoutAmountMinor),
      },
    },
    {
      // A double-click on "Accept bid" must not create two holds.
      idempotencyKey: `escrow_hold_${params.taskId}_${params.bidId}`,
    }
  );

  if (!paymentIntent.client_secret) {
    throw new Error(`PaymentIntent ${paymentIntent.id} has no client secret`);
  }

  return { paymentIntent, clientSecret: paymentIntent.client_secret, fees };
}

/**
 * Release escrow: capture the authorised funds. The transfer to the member
 * and our application fee were fixed at authorisation time, so this is the
 * only call needed.
 */
export async function releaseEscrow(
  paymentIntentId: string,
  reason: string
): Promise<Stripe.PaymentIntent> {
  const stripe = getStripe();

  const intent = await stripe.paymentIntents.retrieve(paymentIntentId);

  if (intent.status === 'succeeded') {
    // Already captured — auto-release and manual sign-off can race.
    return intent;
  }

  if (intent.status !== 'requires_capture') {
    throw new Error(
      `PaymentIntent ${paymentIntentId} is ${intent.status}; expected requires_capture`
    );
  }

  return stripe.paymentIntents.capture(
    paymentIntentId,
    { metadata: { ...intent.metadata, release_reason: reason } },
    { idempotencyKey: `escrow_release_${paymentIntentId}` }
  );
}

/**
 * Return the money. Cancels an uncaptured authorisation, or refunds a capture
 * that already went through (dispute resolved for the requester after
 * sign-off, for example).
 */
export async function refundEscrow(
  paymentIntentId: string,
  reason: string
): Promise<Stripe.PaymentIntent | Stripe.Refund> {
  const stripe = getStripe();
  const intent = await stripe.paymentIntents.retrieve(paymentIntentId);

  if (intent.status === 'requires_capture' || intent.status === 'requires_payment_method') {
    return stripe.paymentIntents.cancel(paymentIntentId, {
      cancellation_reason: 'requested_by_customer',
    });
  }

  if (intent.status === 'succeeded') {
    return stripe.refunds.create(
      {
        payment_intent: paymentIntentId,
        // Claw our fee back too: on a resolved dispute the platform does not
        // keep a cut of work that is being refunded.
        refund_application_fee: true,
        reverse_transfer: true,
        metadata: { release_reason: reason },
      },
      { idempotencyKey: `escrow_refund_${paymentIntentId}` }
    );
  }

  if (intent.status === 'canceled') return intent;

  throw new Error(`PaymentIntent ${paymentIntentId} is ${intent.status}; cannot refund`);
}

/** Create (or reuse) the Express account a member is paid out to. */
export async function ensureConnectAccount(params: {
  existingAccountId?: string | null;
  email?: string;
  country?: string;
  userId: string;
}): Promise<Stripe.Account> {
  const stripe = getStripe();

  if (params.existingAccountId) {
    return stripe.accounts.retrieve(params.existingAccountId);
  }

  return stripe.accounts.create({
    type: 'express',
    email: params.email,
    country: params.country ?? 'US',
    capabilities: {
      transfers: { requested: true },
      card_payments: { requested: true },
    },
    business_type: 'individual',
    settings: {
      payouts: { schedule: { interval: 'daily', delay_days: 'minimum' } },
    },
    metadata: { guild_board_user_id: params.userId },
  });
}

export async function createConnectOnboardingLink(
  accountId: string
): Promise<Stripe.AccountLink> {
  const stripe = getStripe();
  const base = process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000';

  return stripe.accountLinks.create({
    account: accountId,
    refresh_url:
      process.env.STRIPE_CONNECT_REFRESH_URL ?? `${base}/settings/payouts?refresh=1`,
    return_url:
      process.env.STRIPE_CONNECT_RETURN_URL ?? `${base}/settings/payouts?complete=1`,
    type: 'account_onboarding',
    collection_options: { fields: 'eventually_due' },
  });
}
