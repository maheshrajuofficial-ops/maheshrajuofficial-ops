'use client';

import * as React from 'react';
import { useParams, usePathname, useRouter } from 'next/navigation';
import { Globe2, MapPin } from 'lucide-react';

import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

export interface CityOption {
  id: string;
  name: string;
  slug: string;
  country: string;
  lat: number;
  long: number;
  currency: string;
  radius_miles: number;
}

/**
 * The global city switch.
 *
 * City lives in the URL (`/[city]/...`), not in React state, so a board view
 * is linkable and the server can render it without a client round-trip.
 * Switching rewrites the first path segment and preserves the rest of the
 * route where that makes sense — a filtered board stays filtered when you hop
 * from Chicago to London.
 */
export function CitySelector({
  cities,
  className,
}: {
  cities: CityOption[];
  className?: string;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useParams<{ city?: string }>();
  const [pending, startTransition] = React.useTransition();

  const current = params?.city ?? cities[0]?.slug;

  const byCountry = React.useMemo(() => {
    return cities.reduce<Record<string, CityOption[]>>((acc, city) => {
      (acc[city.country] ??= []).push(city);
      return acc;
    }, {});
  }, [cities]);

  function onChange(slug: string) {
    // A task id from one city is meaningless in another, so switching away
    // from a detail page drops back to that city's board.
    const segments = (pathname ?? '/').split('/').filter(Boolean);
    const isDetail = segments.length > 1 && segments[1] === 'tasks';
    const rest = isDetail ? [] : segments.slice(1);

    startTransition(() => {
      router.push(`/${[slug, ...rest].join('/')}`);
    });
  }

  return (
    <Select value={current} onValueChange={onChange}>
      <SelectTrigger
        className={className}
        aria-label="Choose your city"
        data-pending={pending || undefined}
      >
        <span className="flex items-center gap-2 truncate">
          <MapPin className="h-4 w-4 shrink-0 text-primary" />
          <SelectValue placeholder="Choose a city" />
        </span>
      </SelectTrigger>
      <SelectContent>
        {Object.entries(byCountry).map(([country, list]) => (
          <SelectGroup key={country}>
            <SelectLabel className="flex items-center gap-1.5 pl-2 text-xs uppercase tracking-wide text-muted-foreground">
              <Globe2 className="h-3 w-3" />
              {country}
            </SelectLabel>
            {list.map((city) => (
              <SelectItem key={city.id} value={city.slug}>
                {city.name}
              </SelectItem>
            ))}
          </SelectGroup>
        ))}
      </SelectContent>
    </Select>
  );
}
