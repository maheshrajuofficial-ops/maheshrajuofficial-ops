import { NextRequest } from 'next/server';
import { z } from 'zod';

import { fail, ok, withErrorHandling } from '@/lib/api/response';
import { REWARD_MAX, REWARD_MIN, SAFETY_DISCLAIMER_VERSION } from '@/lib/constants';
import { scanTaskContent } from '@/lib/safety/prohibited-filter';
import { createClient } from '@/lib/supabase/server';

export const runtime = 'nodejs';

const CreateTaskSchema = z.object({
  title: z.string().trim().min(8).max(140),
  description: z.string().trim().min(20).max(5000),
  citySlug: z.string().trim().min(1),
  categoryId: z.string().uuid(),
  rewardAmount: z.number().min(REWARD_MIN).max(REWARD_MAX),
  lat: z.number().min(-90).max(90),
  long: z.number().min(-180).max(180),
  addressLine: z.string().trim().max(240).optional(),
  deadlineAt: z.string().datetime({ offset: true }).or(z.string().min(1)).optional(),
  imageUrls: z.array(z.string().url()).max(6).optional(),
  safetyAckVersion: z.string().min(1),
});

/**
 * Create a task.
 *
 * Order matters here: validate, then scan, then write. The safety filter runs
 * before anything is persisted, so a blocked submission leaves no row behind —
 * there is no "pending" state a determined poster could get flipped later.
 */
export const POST = withErrorHandling(async (request: NextRequest) => {
  const supabase = createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) return fail('unauthorized', 'Log in to post a task.');

  const parsed = CreateTaskSchema.safeParse(await request.json());
  if (!parsed.success) {
    return fail('validation_failed', 'Some fields need attention.', {
      fields: Object.fromEntries(
        parsed.error.issues.map((issue) => [issue.path.join('.'), issue.message])
      ),
    });
  }

  const input = parsed.data;

  if (input.safetyAckVersion !== SAFETY_DISCLAIMER_VERSION) {
    return fail(
      'validation_failed',
      'The safety terms have been updated. Reopen the form and read the current version.'
    );
  }

  const [{ data: city }, { data: category }, { data: profile }] = await Promise.all([
    supabase
      .from('cities')
      .select('id, slug, currency, active_status')
      .eq('slug', input.citySlug)
      .single(),
    supabase
      .from('categories')
      .select('id, slug, is_licensed_trade_required, default_risk_tier')
      .eq('id', input.categoryId)
      .single(),
    supabase
      .from('users')
      .select('id, is_suspended, is_id_verified')
      .eq('id', user.id)
      .single(),
  ]);

  if (!city || !city.active_status) return fail('not_found', 'That city is not open yet.');
  if (!category) return fail('not_found', 'Unknown category.');
  if (profile?.is_suspended) {
    return fail('forbidden', 'Your account cannot post tasks right now.');
  }

  /* --- Safety gate ------------------------------------------------------- */
  const verdict = scanTaskContent({
    title: input.title,
    description: input.description,
    categorySlug: category.slug,
    categoryRequiresLicence: category.is_licensed_trade_required,
  });

  if (verdict.action === 'block') {
    return fail(
      'prohibited_content',
      verdict.reason ?? 'This task cannot be posted on Guild Board.',
      { safety: verdict }
    );
  }

  // A licensed-trade task from an unverified requester is held for review
  // rather than refused: the requester is usually legitimate and simply has
  // to verify, and an outright block here teaches them to reword instead.
  const needsReview =
    verdict.action === 'review' ||
    (verdict.requiredLicences.length > 0 && !profile?.is_id_verified);

  const { data: task, error } = await supabase
    .from('tasks')
    .insert({
      requester_id: user.id,
      city_id: city.id,
      category_id: category.id,
      title: input.title,
      description: input.description,
      reward_amount: input.rewardAmount,
      currency: city.currency,
      lat: input.lat,
      long: input.long,
      address_line: input.addressLine ?? null,
      deadline_at: input.deadlineAt ? new Date(input.deadlineAt).toISOString() : null,
      image_urls: input.imageUrls ?? [],
      status: 'open',
      risk_tier:
        verdict.riskTier === 'low' ? category.default_risk_tier : verdict.riskTier,
      flagged_terms: verdict.matches.map((match) => `${match.rule}:${match.term}`),
      requires_admin_review: needsReview,
      safety_ack_at: new Date().toISOString(),
      safety_ack_version: input.safetyAckVersion,
    })
    .select(
      `*,
       category:categories!tasks_category_id_fkey (id, name, slug, icon, is_licensed_trade_required),
       city:cities!tasks_city_id_fkey (id, name, slug, currency),
       requester:users!tasks_requester_id_fkey (id, full_name, avatar_url, rep_score, rep_count, is_id_verified)`
    )
    .single();

  if (error) {
    console.error('[tasks] insert failed', error);
    return fail('internal_error', 'Could not save that task. Please try again.');
  }

  return ok({ task, safety: verdict }, 201);
});
