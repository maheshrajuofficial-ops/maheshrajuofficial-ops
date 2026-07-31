import Link from 'next/link';
import { Hammer, ShieldCheck } from 'lucide-react';

import { CitySelector, type CityOption } from '@/components/layout/city-selector';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { initials } from '@/lib/utils';

interface HeaderProfile {
  id: string;
  full_name: string | null;
  avatar_url: string | null;
  role: string;
  is_id_verified: boolean;
  city_id: string | null;
}

export function Header({
  cities,
  profile,
}: {
  cities: CityOption[];
  profile: HeaderProfile | null;
}) {
  const homeCity =
    cities.find((city) => city.id === profile?.city_id)?.slug ?? cities[0]?.slug;

  return (
    <header className="sticky top-0 z-40 border-b bg-background/85 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center gap-4">
        <Link
          href={homeCity ? `/${homeCity}` : '/'}
          className="flex items-center gap-2 font-semibold tracking-tight"
        >
          <span className="grid h-8 w-8 place-items-center rounded-md bg-primary text-primary-foreground">
            <Hammer className="h-4 w-4" />
          </span>
          <span className="hidden sm:inline">Guild Board</span>
        </Link>

        <CitySelector cities={cities} className="w-[11rem] sm:w-[13rem]" />

        <nav className="ml-auto flex items-center gap-2">
          {profile ? (
            <>
              <Button asChild variant="ghost" size="sm" className="hidden sm:inline-flex">
                <Link href="/dashboard/tasks">My tasks</Link>
              </Button>
              <Button asChild variant="ghost" size="sm" className="hidden sm:inline-flex">
                <Link href="/dashboard/bids">My bids</Link>
              </Button>
              {profile.is_id_verified && (
                <Badge variant="success" className="hidden md:inline-flex">
                  <ShieldCheck className="h-3 w-3" />
                  Verified
                </Badge>
              )}
              <Link href="/settings" aria-label="Account settings">
                <Avatar className="h-9 w-9 border">
                  {profile.avatar_url && (
                    <AvatarImage src={profile.avatar_url} alt="" />
                  )}
                  <AvatarFallback>{initials(profile.full_name)}</AvatarFallback>
                </Avatar>
              </Link>
            </>
          ) : (
            <>
              <Button asChild variant="ghost" size="sm">
                <Link href="/login">Log in</Link>
              </Button>
              <Button asChild size="sm">
                <Link href="/signup">Join the guild</Link>
              </Button>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
