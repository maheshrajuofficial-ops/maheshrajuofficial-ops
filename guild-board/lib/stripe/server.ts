import 'server-only';

import Stripe from 'stripe';

let cached: Stripe | null = null;

/**
 * Lazily constructed so that importing this module (for its types, or from a
 * route that never touches Stripe) doesn't require the key to be present.
 */
export function getStripe(): Stripe {
  if (cached) return cached;

  const key = process.env.STRIPE_SECRET_KEY;
  if (!key) throw new Error('STRIPE_SECRET_KEY is not set');

  cached = new Stripe(key, {
    apiVersion: '2025-02-24.acacia',
    appInfo: { name: 'Guild Board', version: '0.1.0' },
    // Escrow calls are money-moving; a short retry budget with idempotency
    // keys is safer than letting a transient 500 strand a hold.
    maxNetworkRetries: 2,
    timeout: 20_000,
  });

  return cached;
}

export type { Stripe };
