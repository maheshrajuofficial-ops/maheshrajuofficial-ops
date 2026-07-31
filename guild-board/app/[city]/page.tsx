import { notFound } from 'next/navigation';
import type { Metadata } from 'next';

import { GuildBoard } from '@/components/board/guild-board';
import { BOARD_PAGE_SIZE, RADIUS_DEFAULT_MILES, RADIUS_MAX_MILES } from '@/lib/constants';
import { createClient } from '@/lib/supabase/server';
import { numParam } from '@/lib/utils';
import type { TaskWithDistance } from '@/types/database';

interface PageProps {
  params: { city: string };
  searchParams: Record<string, string | string[] | undefined>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const supabase = createClient();
  const { data: city } = await supabase
    .from('cities')
    .select('name')
    .eq('slug', params.city)
    .single();

  return {
    title: city ? `${city.name} board` : 'Board',
    description: city
      ? `Open tasks near you in ${city.name} — post a request or bid on local work.`
      : undefined,
  };
}

export default async function CityBoardPage({ params, searchParams }: PageProps) {
  const supabase = createClient();

  const [{ data: city }, { data: categories }, { data: auth }] = await Promise.all([
    supabase
      .from('cities')
      .select('id, name, slug, lat, long, currency, radius_miles, active_status')
      .eq('slug', params.city)
      .single(),
    supabase
      .from('categories')
      .select('id, name, slug, is_licensed_trade_required')
      .order('sort_order'),
    supabase.auth.getUser(),
  ]);

  if (!city || !city.active_status) notFound();

  const single = (key: string) =>
    Array.isArray(searchParams[key]) ? searchParams[key]![0] : (searchParams[key] as string | undefined);

  const radius = Math.min(
    numParam(single('radius')) ?? RADIUS_DEFAULT_MILES,
    RADIUS_MAX_MILES
  );

  const categorySlugs = single('categories')?.split(',').filter(Boolean) ?? [];
  const categoryIds = categorySlugs.length
    ? (categories ?? [])
        .filter((category) => categorySlugs.includes(category.slug))
        .map((category) => category.id)
    : null;

  // Discovery runs through the PostGIS RPC so the radius filter happens in the
  // index rather than by pulling the city's tasks into Node and measuring here.
  const { data: rows, error } = await supabase.rpc('tasks_within_radius', {
    p_city_slug: city.slug,
    p_lat: city.lat,
    p_long: city.long,
    p_radius_miles: radius,
    p_category_ids: categoryIds,
    p_min_reward: numParam(single('min')) ?? null,
    p_max_reward: numParam(single('max')) ?? null,
    p_limit: BOARD_PAGE_SIZE,
    p_offset: 0,
  });

  if (error) {
    console.error('[board] radius query failed', error);
  }

  const tasks = sortTasks((rows ?? []) as TaskWithDistance[], single('sort'));

  return (
    <GuildBoard
      city={city}
      categories={categories ?? []}
      tasks={tasks}
      radiusMiles={radius}
      isAuthenticated={Boolean(auth?.user)}
    />
  );
}

/**
 * The RPC returns nearest-first because that's what its index ordering gives
 * for free; the other three orderings are a cheap in-memory sort over a single
 * page rather than four variants of the query.
 */
function sortTasks(tasks: TaskWithDistance[], sort?: string): TaskWithDistance[] {
  switch (sort) {
    case 'newest':
      return [...tasks].sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
    case 'reward_desc':
      return [...tasks].sort((a, b) => b.reward_amount - a.reward_amount);
    case 'reward_asc':
      return [...tasks].sort((a, b) => a.reward_amount - b.reward_amount);
    default:
      return tasks;
  }
}
