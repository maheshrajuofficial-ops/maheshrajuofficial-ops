import { redirect } from 'next/navigation';

import { createClient } from '@/lib/supabase/server';

/**
 * The root has no board of its own — Guild Board is city-scoped by definition.
 * Send people to their profile city, else the first active city.
 */
export default async function RootPage() {
  const supabase = createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (user) {
    const { data: profile } = await supabase
      .from('users')
      .select('city_id, cities:city_id (slug)')
      .eq('id', user.id)
      .single();

    const slug = (profile as { cities?: { slug: string } | null } | null)?.cities?.slug;
    if (slug) redirect(`/${slug}`);
  }

  const { data: city } = await supabase
    .from('cities')
    .select('slug')
    .eq('active_status', true)
    .order('name')
    .limit(1)
    .single();

  redirect(city ? `/${city.slug}` : '/new-york');
}
