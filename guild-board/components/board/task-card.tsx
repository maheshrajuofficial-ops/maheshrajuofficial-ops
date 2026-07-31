'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import { Clock, MapPin, Users } from 'lucide-react';

import { RiskBadge } from '@/components/trust/verification-badge';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { cn, formatCurrency, formatDistance, formatRelativeTime, truncate } from '@/lib/utils';
import type { TaskWithDistance } from '@/types/database';

export interface TaskCardProps {
  task: TaskWithDistance;
  citySlug: string;
  categoryName?: string;
  currency?: string;
  /** Highlighted when the corresponding map pin is hovered. */
  isActive?: boolean;
  onHover?: (taskId: string | null) => void;
  index?: number;
}

export function TaskCard({
  task,
  citySlug,
  categoryName,
  currency = 'USD',
  isActive,
  onHover,
  index = 0,
}: TaskCardProps) {
  const deadlineSoon =
    task.deadline_at &&
    new Date(task.deadline_at).getTime() - Date.now() < 48 * 3_600_000;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18, delay: Math.min(index, 8) * 0.02 }}
      onMouseEnter={() => onHover?.(task.id)}
      onMouseLeave={() => onHover?.(null)}
    >
      <Link href={`/${citySlug}/tasks/${task.id}`} className="block h-full">
        <Card
          className={cn(
            'flex h-full flex-col transition-shadow hover:shadow-md',
            isActive && 'ring-2 ring-primary'
          )}
        >
          <CardHeader className="gap-2 pb-3">
            <div className="flex flex-wrap items-center gap-1.5">
              {categoryName && (
                <Badge variant="secondary" className="font-normal">
                  {categoryName}
                </Badge>
              )}
              <RiskBadge tier={task.risk_tier} />
            </div>
            <h3 className="text-base font-semibold leading-snug">{task.title}</h3>
          </CardHeader>

          <CardContent className="flex-1 pb-3">
            <p className="text-sm leading-relaxed text-muted-foreground">
              {truncate(task.description, 140)}
            </p>
          </CardContent>

          <CardFooter className="flex-col items-stretch gap-3 border-t pt-4">
            <div className="flex items-baseline justify-between">
              <span className="text-xl font-semibold tabular-nums">
                {formatCurrency(task.reward_amount, currency)}
              </span>
              <span className="flex items-center gap-1 text-xs text-muted-foreground">
                <Users className="h-3.5 w-3.5" />
                {task.bid_count === 0
                  ? 'No bids yet'
                  : `${task.bid_count} bid${task.bid_count === 1 ? '' : 's'}`}
              </span>
            </div>

            <div className="flex items-center gap-3 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <MapPin className="h-3.5 w-3.5" />
                {formatDistance(task.distance_miles)}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="h-3.5 w-3.5" />
                {formatRelativeTime(task.created_at)}
              </span>
              {deadlineSoon && (
                <Badge variant="warning" className="ml-auto">
                  Due soon
                </Badge>
              )}
            </div>
          </CardFooter>
        </Card>
      </Link>
    </motion.div>
  );
}

export function TaskCardSkeleton() {
  return (
    <Card className="h-[15.5rem] animate-pulse">
      <CardHeader className="gap-3">
        <div className="h-5 w-24 rounded-full bg-muted" />
        <div className="h-5 w-3/4 rounded bg-muted" />
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="h-3 w-full rounded bg-muted" />
        <div className="h-3 w-5/6 rounded bg-muted" />
      </CardContent>
      <CardFooter className="border-t pt-4">
        <div className="h-6 w-20 rounded bg-muted" />
      </CardFooter>
    </Card>
  );
}
