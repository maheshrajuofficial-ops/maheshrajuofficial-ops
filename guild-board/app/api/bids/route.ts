import { NextRequest } from 'next/server';
import { z } from 'zod';

import { fail, ok, withErrorHandling } from '@/lib/api/response';
import { REWARD_MAX, REWARD_MIN } from '@/lib/constants';
import { scanFreeText } from '@/lib/safety/prohibited-filter';
import { createClient } from '@/lib/supabase/server';

export const runtime = 'nodejs';

const BidSchema = z.object({
  taskId: z.string().uuid(),
  amount: z.number().min(REWARD_MIN).max(REWARD_MAX),
  proposalText: z.string().trim().min(20).max(2000),
  estimatedHours: z.number().positive().max(500).optional(),
  canStartAt: z.string().optional(),
});

const UpdateSchema = BidSchema.extend({ bidId: z.string().uuid() });

/**
 * Submit a bid.
 *
 * The licence gate, the "task must be open" check and the "no bidding on your
 * own task" rule all live in the `bids_guard_eligibility` trigger, not here —
 * so they hold for the Supabase client path too, not just this route.
 */
export const POST = withErrorHandling(async (request: NextRequest) => {
  const supabase = createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) return fail('unauthorized', 'Log in to bid.');

  const parsed = BidSchema.safeParse(await request.json());
  if (!parsed.success) {
    return fail('validation_failed', 'Check the amount and your proposal text.', {
      fields: Object.fromEntries(
        parsed.error.issues.map((issue) => [issue.path.join('.'), issue.message])
      ),
    });
  }

  const input = parsed.data;

  const verdict = scanFreeText(input.proposalText);
  if (verdict.action === 'block') {
    return fail('prohibited_content', verdict.reason ?? 'That proposal cannot be sent.', {
      safety: verdict,
    });
  }

  // A worker needs somewhere for the money to land before they can bid;
  // finding this out at acceptance time would strand the requester.
  const { data: profile } = await supabase
    .from('users')
    .select('stripe_account_id, stripe_payouts_enabled')
    .eq('id', user.id)
    .single();

  if (!profile?.stripe_payouts_enabled) {
    return fail(
      'payout_setup_required',
      'Finish payout setup before bidding — it takes about two minutes and means we can pay you the moment a task is signed off.'
    );
  }

  const { data: bid, error } = await supabase
    .from('bids')
    .insert({
      task_id: input.taskId,
      member_id: user.id,
      amount: input.amount,
      proposal_text: input.proposalText,
      estimated_hours: input.estimatedHours ?? null,
      can_start_at: input.canStartAt ? new Date(input.canStartAt).toISOString() : null,
    })
    .select()
    .single();

  if (error) {
    // The database's own guards produce readable messages; surface them.
    if (error.code === '23505') {
      return fail('conflict', 'You already have a bid on this task — update it instead.');
    }
    return fail('forbidden', error.message);
  }

  return ok({ bid }, 201);
});

/** Revise a pending bid. RLS restricts this to the bidder while pending. */
export const PATCH = withErrorHandling(async (request: NextRequest) => {
  const supabase = createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) return fail('unauthorized', 'Log in to update your bid.');

  const parsed = UpdateSchema.safeParse(await request.json());
  if (!parsed.success) {
    return fail('validation_failed', 'Check the amount and your proposal text.');
  }

  const input = parsed.data;

  const verdict = scanFreeText(input.proposalText);
  if (verdict.action === 'block') {
    return fail('prohibited_content', verdict.reason ?? 'That proposal cannot be sent.', {
      safety: verdict,
    });
  }

  const { data: bid, error } = await supabase
    .from('bids')
    .update({
      amount: input.amount,
      proposal_text: input.proposalText,
      estimated_hours: input.estimatedHours ?? null,
    })
    .eq('id', input.bidId)
    .eq('member_id', user.id)
    .eq('status', 'pending')
    .select()
    .single();

  if (error) return fail('forbidden', error.message);
  if (!bid) return fail('not_found', 'That bid is no longer editable.');

  return ok({ bid });
});
