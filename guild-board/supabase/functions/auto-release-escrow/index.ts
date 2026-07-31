/**
 * Scheduled escrow auto-release.
 *
 * Deploy:
 *   supabase functions deploy auto-release-escrow
 *   supabase secrets set APP_URL=https://guildboard.app ESCROW_CRON_SECRET=...
 *
 * Schedule hourly with pg_cron:
 *   select cron.schedule(
 *     'escrow-auto-release', '0 * * * *',
 *     $$select net.http_post(
 *         url := 'https://<project-ref>.functions.supabase.co/auto-release-escrow',
 *         headers := '{"Content-Type":"application/json"}'::jsonb
 *       )$$
 *   );
 *
 * The function holds no payment logic of its own. It is a scheduler that
 * calls the one release path in the app, so that "capture funds" exists in
 * exactly one place and is audited in exactly one place.
 *
 * Runs on Deno (Supabase Edge Runtime), not on the Next.js Node build — hence
 * the `supabase/functions` exclusion in tsconfig.json.
 */

// @ts-nocheck -- Deno globals and remote imports; type-checked by `deno check`.
import { serve } from 'https://deno.land/std@0.208.0/http/server.ts';

serve(async (request: Request) => {
  const appUrl = Deno.env.get('APP_URL');
  const cronSecret = Deno.env.get('ESCROW_CRON_SECRET');

  if (!appUrl || !cronSecret) {
    return new Response(
      JSON.stringify({ error: 'APP_URL and ESCROW_CRON_SECRET must be set' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }

  // Allow a manual trigger only with the same shared secret.
  if (request.method === 'POST') {
    const provided = request.headers.get('x-escrow-cron-secret');
    if (provided && provided !== cronSecret) {
      return new Response(JSON.stringify({ error: 'Forbidden' }), { status: 403 });
    }
  }

  const started = Date.now();

  const response = await fetch(`${appUrl}/api/stripe/escrow/release`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-escrow-cron-secret': cronSecret,
    },
    body: JSON.stringify({ reason: 'auto_release_72h' }),
  });

  const result = await response.json().catch(() => ({}));

  console.log(
    JSON.stringify({
      event: 'escrow_auto_release_sweep',
      ok: response.ok,
      status: response.status,
      duration_ms: Date.now() - started,
      result,
    })
  );

  return new Response(JSON.stringify(result), {
    status: response.ok ? 200 : 502,
    headers: { 'Content-Type': 'application/json' },
  });
});
