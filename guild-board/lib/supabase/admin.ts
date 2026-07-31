import 'server-only';

import { createClient } from '@supabase/supabase-js';

import type { Database } from '@/types/database';

/**
 * Service-role client. Bypasses RLS entirely.
 *
 * Legitimate callers are narrow, and worth naming: the Stripe webhook (sole
 * writer of `transactions`), the escrow release path, the verification
 * webhooks that set `is_id_verified` / `licensed_trades`, and admin tooling.
 * If you reach for this anywhere else, the RLS policy is probably the thing
 * that needs changing.
 *
 * The `server-only` import above makes importing this from a Client Component
 * a build error rather than a leaked key.
 */
export function createAdminClient() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!url || !serviceKey) {
    throw new Error(
      'Supabase admin client requires NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY'
    );
  }

  return createClient<Database>(url, serviceKey, {
    auth: { autoRefreshToken: false, persistSession: false },
  });
}
