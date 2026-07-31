'use client';

import * as React from 'react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { Filter, Map as MapIcon, RotateCcw, Rows3 } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import {
  BOARD_SORTS,
  RADIUS_DEFAULT_MILES,
  RADIUS_MAX_MILES,
  RADIUS_MIN_MILES,
} from '@/lib/constants';
import { cn } from '@/lib/utils';
import type { Category } from '@/types/database';

export interface BoardFiltersProps {
  categories: Pick<Category, 'id' | 'name' | 'slug' | 'is_licensed_trade_required'>[];
  view: 'grid' | 'map';
  onViewChange: (view: 'grid' | 'map') => void;
  resultCount: number;
}

/**
 * Every filter is a URL search param.
 *
 * That costs a navigation per change, which is why the radius slider commits
 * on release rather than on every pixel — but it buys shareable board states,
 * a working back button, and server-rendered results with no client fetch.
 */
export function BoardFilters({
  categories,
  view,
  onViewChange,
  resultCount,
}: BoardFiltersProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [pending, startTransition] = React.useTransition();

  const selectedCategories = React.useMemo(
    () => new Set(searchParams.get('categories')?.split(',').filter(Boolean) ?? []),
    [searchParams]
  );

  const radius = Number(searchParams.get('radius') ?? RADIUS_DEFAULT_MILES);
  const sort = searchParams.get('sort') ?? 'nearest';
  const minReward = searchParams.get('min') ?? '';
  const maxReward = searchParams.get('max') ?? '';

  // Local mirror so the slider tracks the drag without a navigation per frame.
  const [radiusDraft, setRadiusDraft] = React.useState(radius);
  React.useEffect(() => setRadiusDraft(radius), [radius]);

  const push = React.useCallback(
    (mutate: (params: URLSearchParams) => void) => {
      const params = new URLSearchParams(searchParams.toString());
      mutate(params);
      startTransition(() => {
        router.replace(`${pathname}?${params.toString()}`, { scroll: false });
      });
    },
    [pathname, router, searchParams]
  );

  function toggleCategory(slug: string) {
    push((params) => {
      const next = new Set(selectedCategories);
      if (next.has(slug)) next.delete(slug);
      else next.add(slug);

      if (next.size) params.set('categories', [...next].join(','));
      else params.delete('categories');
    });
  }

  function setParam(key: string, value: string | number | null) {
    push((params) => {
      if (value === null || value === '') params.delete(key);
      else params.set(key, String(value));
    });
  }

  const hasFilters =
    selectedCategories.size > 0 ||
    Boolean(minReward) ||
    Boolean(maxReward) ||
    radius !== RADIUS_DEFAULT_MILES ||
    sort !== 'nearest';

  return (
    <div
      className={cn(
        'space-y-5 rounded-lg border bg-card p-5',
        pending && 'opacity-70 transition-opacity'
      )}
    >
      <div className="flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-sm font-semibold">
          <Filter className="h-4 w-4" />
          Filters
        </h2>
        <div className="flex items-center gap-1 rounded-md border p-0.5">
          <Button
            type="button"
            size="sm"
            variant={view === 'grid' ? 'secondary' : 'ghost'}
            className="h-7 px-2"
            onClick={() => onViewChange('grid')}
            aria-pressed={view === 'grid'}
          >
            <Rows3 className="h-3.5 w-3.5" />
            <span className="sr-only sm:not-sr-only">Grid</span>
          </Button>
          <Button
            type="button"
            size="sm"
            variant={view === 'map' ? 'secondary' : 'ghost'}
            className="h-7 px-2"
            onClick={() => onViewChange('map')}
            aria-pressed={view === 'map'}
          >
            <MapIcon className="h-3.5 w-3.5" />
            <span className="sr-only sm:not-sr-only">Map</span>
          </Button>
        </div>
      </div>

      {/* --- Categories ---------------------------------------------------- */}
      <fieldset className="space-y-2">
        <legend className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Category
        </legend>
        <div className="flex flex-wrap gap-1.5">
          {categories.map((category) => {
            const active = selectedCategories.has(category.slug);
            return (
              <button
                key={category.id}
                type="button"
                onClick={() => toggleCategory(category.slug)}
                aria-pressed={active}
                className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded-full"
              >
                <Badge
                  variant={active ? 'default' : 'outline'}
                  className="cursor-pointer font-normal"
                >
                  {category.name}
                  {category.is_licensed_trade_required && ' ·  licensed'}
                </Badge>
              </button>
            );
          })}
        </div>
      </fieldset>

      {/* --- Radius -------------------------------------------------------- */}
      <div className="space-y-2">
        <div className="flex items-baseline justify-between">
          <Label htmlFor="radius" className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Within
          </Label>
          <span className="text-sm font-medium tabular-nums">
            {radiusDraft} {radiusDraft === 1 ? 'mile' : 'miles'}
          </span>
        </div>
        <Slider
          id="radius"
          min={RADIUS_MIN_MILES}
          max={RADIUS_MAX_MILES}
          step={1}
          value={[radiusDraft]}
          onValueChange={([value]) => setRadiusDraft(value)}
          onValueCommit={([value]) => setParam('radius', value)}
          aria-label={`Search radius, ${radiusDraft} miles`}
        />
        <div className="flex justify-between text-[10px] text-muted-foreground">
          <span>{RADIUS_MIN_MILES} mi</span>
          <span>{RADIUS_MAX_MILES} mi</span>
        </div>
      </div>

      {/* --- Budget -------------------------------------------------------- */}
      <div className="space-y-2">
        <Label className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Reward
        </Label>
        <div className="flex items-center gap-2">
          <Input
            type="number"
            inputMode="numeric"
            min={0}
            placeholder="Min"
            defaultValue={minReward}
            onBlur={(event) => setParam('min', event.target.value)}
            aria-label="Minimum reward"
          />
          <span className="text-muted-foreground">–</span>
          <Input
            type="number"
            inputMode="numeric"
            min={0}
            placeholder="Max"
            defaultValue={maxReward}
            onBlur={(event) => setParam('max', event.target.value)}
            aria-label="Maximum reward"
          />
        </div>
      </div>

      {/* --- Sort ---------------------------------------------------------- */}
      <div className="space-y-2">
        <Label className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Sort by
        </Label>
        <Select value={sort} onValueChange={(value) => setParam('sort', value)}>
          <SelectTrigger aria-label="Sort tasks">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {BOARD_SORTS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="flex items-center justify-between border-t pt-4 text-xs text-muted-foreground">
        <span>
          {resultCount} {resultCount === 1 ? 'task' : 'tasks'}
        </span>
        {hasFilters && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-7 gap-1 px-2 text-xs"
            onClick={() => startTransition(() => router.replace(pathname, { scroll: false }))}
          >
            <RotateCcw className="h-3 w-3" />
            Reset
          </Button>
        )}
      </div>
    </div>
  );
}
