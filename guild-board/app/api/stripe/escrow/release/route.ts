import { NextRequest } from 'next/server';
import { z } from 'zod';

import { fail, ok, withErrorHandling } from '@/lib/api/response';
import { ESCROW_AUTO_RELEASE_HOURS } from '@/lib/constants';
import { releaseEscrow } from '@/lib/stripe/escrow';
import { createAdminClient } from '@/lib/supabase/admin';
import { createClient } from '@/lib/supabase/server';

export const runtime = 'nodejs';
export const maxDuration = 60;

const Schema = z.object({
  taskId: z.string().uuid().optional(),
  reason: z
    .enum(['manual_signoff', 'auto_release_72h', 'dispute_resolution', 'admin'])
    .default('manual_signoff'),
});

/**
 * Release escrowed funds.
 *
 * Two callers, two authorisation paths:
 *
 *   - a requester signing off, identified by their session; and
 *   - the scheduled sweep, identified by the `x-escrow-cron-secret` header,
 *     which releases every task whose dispute-free window has elapsed.
 *
 * The capture itself is idempotent (Stripe returns the succeeded intent if it
 * was already captured), so a sign-off racing the sweep is harmless — which
 * matters, because that race happens routinely at the 72-hour boundary.
 */
export const POST = withErrorHandling(async (request: NextRequest) => {
  const cronSecret = request.headers.get('x-escrow-cron-secret');
  const isCron =
    Boolean(process.env.ESCROW_CRON_SECRET) &&
    cronSecret === process.env.ESCROW_CRON_SECRET;

  const body = Schema.safeParse(await request.json().catch(() => ({})));
  if (!body.success) return fail('validation_failed', 'Invalid release request.');

  return isCron ? sweepDueReleases() : releaseOne(body.data.taskId, body.data.reason);
});

/* -------------------------------------------------------------------------- */

async function releaseOne(taskId: string | undefined, reason: string) {
  if (!taskId) return fail('validation_failed', 'Missing task id.');

  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) return fail('unauthorized', 'Log in to release funds.');

  const { data: transaction } = await supabase
    .from('transactions')
    .select('id, task_id, payer_id, payee_id, escrow_status, stripe_payment_intent_id')
    .eq('task_id', taskId)
    .eq('escrow_status', 'held')
    .maybeSingle();

  if (!transaction) return fail('not_found', 'No held escrow for that task.');
  if (transaction.payer_id !== user.id) {
    return fail('forbidden', 'Only the requester can sign off on this task.');
  }
  if (!transaction.stripe_payment_intent_id) {
    return fail('conflict', 'This escrow has no payment attached.');
  }

  // An open dispute freezes release — checked here as well as in the view the
  // sweep reads, so neither path can pay out over a live complaint.
  const { data: dispute } = await supabase
    .from('disputes')
    .select('id')
    .eq('task_id', taskId)
    .in('status', ['open', 'under_review'])
    .maybeSingle();

  if (dispute) {
    return fail(
      'conflict',
      'This task is under dispute. Funds stay held until an admin resolves it.'
    );
  }

  await supabase.rpc('sign_off_task', { p_task_id: taskId, p_hold_hours: 0 });

  const intent = await releaseEscrow(transaction.stripe_payment_intent_id, reason);

  // The webhook is the authority on escrow state; this write just avoids a
  // stale panel between the capture and the webhook landing.
  const admin = createAdminClient();
  await admin
    .from('transactions')
    .update({
      escrow_status: 'released',
      released_at: new Date().toISOString(),
      release_reason: reason,
      stripe_charge_id: typeof intent.latest_charge === 'string' ? intent.latest_charge : null,
    })
    .eq('id', transaction.id);

  return ok({ transactionId: transaction.id, escrowStatus: 'released', reason });
}

/**
 * The auto-release sweep. Runs from the Supabase Edge Function on a schedule;
 * see `supabase/functions/auto-release-escrow/`.
 */
async function sweepDueReleases() {
  const admin = createAdminClient();

  const { data: due, error } = await admin
    .from('escrow_auto_release_queue')
    .select('*')
    .limit(100);

  if (error) {
    console.error('[escrow] queue read failed', error);
    return fail('internal_error', 'Could not read the release queue.');
  }

  const released: string[] = [];
  const failed: { taskId: string; error: string }[] = [];

  for (const row of due ?? []) {
    if (!row.stripe_payment_intent_id) continue;

    try {
      const intent = await releaseEscrow(row.stripe_payment_intent_id, 'auto_release_72h');

      await admin
        .from('transactions')
        .update({
          escrow_status: 'released',
          released_at: new Date().toISOString(),
          release_reason: 'auto_release_72h',
          stripe_charge_id:
            typeof intent.latest_charge === 'string' ? intent.latest_charge : null,
        })
        .eq('id', row.transaction_id);

      released.push(row.task_id);
    } catch (releaseError) {
      const message =
        releaseError instanceof Error ? releaseError.message : 'unknown error';

      // Record and continue: one expired authorisation must not stall the
      // rest of the queue.
      await admin
        .from('transactions')
        .update({ failure_code: message.slice(0, 200) })
        .eq('id', row.transaction_id);

      failed.push({ taskId: row.task_id, error: message });
      console.error('[escrow] auto-release failed', row.task_id, releaseError);
    }
  }

  return ok({
    windowHours: ESCROW_AUTO_RELEASE_HOURS,
    considered: due?.length ?? 0,
    released,
    failed,
  });
}
