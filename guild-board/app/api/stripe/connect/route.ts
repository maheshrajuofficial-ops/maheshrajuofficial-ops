import { NextRequest } from 'next/server';

import { fail, ok, withErrorHandling } from '@/lib/api/response';
import { createConnectOnboardingLink, ensureConnectAccount } from '@/lib/stripe/escrow';
import { getStripe } from '@/lib/stripe/server';
import { createAdminClient } from '@/lib/supabase/admin';
import { createClient } from '@/lib/supabase/server';

export const runtime = 'nodejs';

/**
 * Create or resume Stripe Connect (Express) onboarding for a worker.
 *
 * Express rather than Custom: Stripe hosts the KYC flow and owns the identity
 * and tax data, which keeps a large compliance surface — and the PII that
 * comes with it — off our infrastructure. Revisit only if the onboarding
 * conversion rate demands a fully white-labelled flow, and budget for the
 * liability that shifts to us when it does.
 */
export const POST = withErrorHandling(async (request: NextRequest) => {
  const supabase = createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) return fail('unauthorized', 'Log in to set up payouts.');

  const { data: profile } = await supabase
    .from('users')
    .select('id, full_name, stripe_account_id')
    .eq('id', user.id)
    .single();

  const body = (await request.json().catch(() => ({}))) as { country?: string };

  const account = await ensureConnectAccount({
    existingAccountId: profile?.stripe_account_id,
    email: user.email,
    country: body.country,
    userId: user.id,
  });

  // stripe_account_id is server-owned (guard_user_privileges blocks the user
  // from writing it), so this goes through the service role.
  if (profile?.stripe_account_id !== account.id) {
    const admin = createAdminClient();
    const { error } = await admin
      .from('users')
      .update({
        stripe_account_id: account.id,
        role: 'member',
      })
      .eq('id', user.id);

    if (error) {
      console.error('[connect] could not persist account id', error);
      return fail('internal_error', 'Payout setup could not be saved.');
    }
  }

  const link = await createConnectOnboardingLink(account.id);

  return ok({
    accountId: account.id,
    onboardingUrl: link.url,
    payoutsEnabled: account.payouts_enabled ?? false,
    chargesEnabled: account.charges_enabled ?? false,
    requirementsDue: account.requirements?.currently_due ?? [],
  });
});

/** Current payout readiness, read straight from Stripe. */
export const GET = withErrorHandling(async () => {
  const supabase = createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) return fail('unauthorized', 'Log in to view payout status.');

  const { data: profile } = await supabase
    .from('users')
    .select('stripe_account_id')
    .eq('id', user.id)
    .single();

  if (!profile?.stripe_account_id) {
    return ok({
      accountId: null,
      onboardingUrl: null,
      payoutsEnabled: false,
      chargesEnabled: false,
      requirementsDue: [],
    });
  }

  const account = await getStripe().accounts.retrieve(profile.stripe_account_id);

  return ok({
    accountId: account.id,
    onboardingUrl: null,
    payoutsEnabled: account.payouts_enabled ?? false,
    chargesEnabled: account.charges_enabled ?? false,
    requirementsDue: account.requirements?.currently_due ?? [],
  });
});
