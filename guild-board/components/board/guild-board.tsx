'use client';

import * as React from 'react';
import dynamic from 'next/dynamic';
import { AnimatePresence } from 'framer-motion';
import { SearchX } from 'lucide-react';

import { BoardFilters } from '@/components/board/board-filters';
import { TaskCard } from '@/components/board/task-card';
import { CreateTaskModal } from '@/components/tasks/create-task-modal';
import type { Category, City, TaskWithDistance } from '@/types/database';

// Mapbox GL touches `window` at import time and ships ~200kB, so it stays out
// of the initial bundle and off the server.
const TaskMap = dynamic(
  () => import('@/components/board/task-map').then((mod) => mod.TaskMap),
  {
    ssr: false,
    loading: () => (
      <div className="h-[28rem] animate-pulse rounded-lg border bg-muted/40 lg:h-[calc(100vh-12rem)]" />
    ),
  }
);

export interface GuildBoardProps {
  city: Pick<City, 'id' | 'name' | 'slug' | 'lat' | 'long' | 'currency'>;
  categories: Pick<Category, 'id' | 'name' | 'slug' | 'is_licensed_trade_required'>[];
  tasks: TaskWithDistance[];
  radiusMiles: number;
  isAuthenticated: boolean;
}

export function GuildBoard({
  city,
  categories,
  tasks,
  radiusMiles,
  isAuthenticated,
}: GuildBoardProps) {
  const [view, setView] = React.useState<'grid' | 'map'>('grid');
  const [activeTaskId, setActiveTaskId] = React.useState<string | null>(null);

  const categoryNames = React.useMemo(
    () => new Map(categories.map((category) => [category.id, category.name])),
    [categories]
  );

  return (
    <div className="container py-8">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
            The {city.name} board
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {tasks.length === 0
              ? 'Nothing posted in this radius yet.'
              : `${tasks.length} open ${tasks.length === 1 ? 'task' : 'tasks'} within ${radiusMiles} miles.`}
          </p>
        </div>

        <CreateTaskModal
          city={city}
          categories={categories}
          isAuthenticated={isAuthenticated}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-[18rem_1fr]">
        <aside className="lg:sticky lg:top-24 lg:self-start">
          <BoardFilters
            categories={categories}
            view={view}
            onViewChange={setView}
            resultCount={tasks.length}
          />
        </aside>

        <section aria-label="Task board" className="min-w-0">
          {tasks.length === 0 ? (
            <EmptyBoard cityName={city.name} />
          ) : view === 'map' ? (
            <TaskMap
              tasks={tasks}
              center={{ lat: city.lat, long: city.long }}
              radiusMiles={radiusMiles}
              currency={city.currency}
              activeTaskId={activeTaskId}
              onSelect={setActiveTaskId}
            />
          ) : (
            <div className="board-grid board-surface -m-2 rounded-lg p-2">
              <AnimatePresence mode="popLayout">
                {tasks.map((task, index) => (
                  <TaskCard
                    key={task.id}
                    task={task}
                    index={index}
                    citySlug={city.slug}
                    currency={city.currency}
                    categoryName={categoryNames.get(task.category_id)}
                    isActive={activeTaskId === task.id}
                    onHover={setActiveTaskId}
                  />
                ))}
              </AnimatePresence>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

function EmptyBoard({ cityName }: { cityName: string }) {
  return (
    <div className="grid place-items-center rounded-lg border border-dashed py-24 text-center">
      <SearchX className="mb-3 h-8 w-8 text-muted-foreground" />
      <p className="font-medium">No tasks match these filters</p>
      <p className="mt-1 max-w-sm text-sm text-muted-foreground">
        Widen the radius or clear a category — {cityName} is still filling up.
        Posting the first task in a category tends to get a fast response.
      </p>
    </div>
  );
}
