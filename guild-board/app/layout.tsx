import type { Metadata } from 'next';
import { Inter } from 'next/font/google';

import { Header } from '@/components/layout/header';
import { createClient } from '@/lib/supabase/server';

import './globals.css';

const inter = Inter({ subsets: ['latin'], variable: '--font-sans' });

export const metadata: Metadata = {
  title: {
    default: 'Guild Board — the local board for odd jobs',
    template: '%s · Guild Board',
  },
  description:
    'Post a task, take a job. Guild Board is a city-by-city marketplace for custom requests, odd jobs and the genuinely niche — with escrow, verified workers and a real dispute process.',
  openGraph: {
    title: 'Guild Board',
    description: 'The local board for odd jobs, custom requests and niche work.',
    type: 'website',
  },
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const supabase = createClient();

  const [{ data: cities }, { data: auth }] = await Promise.all([
    supabase
      .from('cities')
      .select('id, name, slug, country, lat, long, currency, radius_miles')
      .eq('active_status', true)
      .order('name'),
    supabase.auth.getUser(),
  ]);

  const profile = auth?.user
    ? (
        await supabase
          .from('users')
          .select('id, full_name, avatar_url, role, is_id_verified, city_id')
          .eq('id', auth.user.id)
          .single()
      ).data
    : null;

  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans`}>
        <Header cities={cities ?? []} profile={profile} />
        <main className="min-h-[calc(100vh-4rem)]">{children}</main>
        <footer className="border-t py-8 text-sm text-muted-foreground">
          <div className="container flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <p>
              Guild Board is a neutral venue. Workers are independent, not
              employees.
            </p>
            <p className="text-xs">
              Escrow held via Stripe · Licensed trades verified before work begins
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
