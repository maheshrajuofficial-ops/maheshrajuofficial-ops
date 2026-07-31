import { BadgeCheck, HardHat, ShieldCheck, Star, TriangleAlert } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { RISK_TIER_LABELS } from '@/lib/constants';
import { cn } from '@/lib/utils';
import type { RiskTier } from '@/types/database';

/**
 * Trust signals, deliberately kept literal.
 *
 * "Verified" here means one specific thing — a government ID was matched to a
 * selfie by Persona — and the tooltip says so. Vague trust badges are worse
 * than none: they transfer confidence the platform hasn't actually earned.
 */

export function IdVerifiedBadge({ className }: { className?: string }) {
  return (
    <Badge variant="success" className={className} title="Government ID matched to a selfie">
      <ShieldCheck className="h-3 w-3" />
      ID verified
    </Badge>
  );
}

export function BackgroundCheckedBadge({ className }: { className?: string }) {
  return (
    <Badge
      variant="info"
      className={className}
      title="Criminal background screening completed within the last 12 months"
    >
      <BadgeCheck className="h-3 w-3" />
      Background checked
    </Badge>
  );
}

export function LicenceBadge({
  trade,
  className,
}: {
  trade: string;
  className?: string;
}) {
  return (
    <Badge
      variant="info"
      className={cn('capitalize', className)}
      title={`Verified ${trade} licence on file`}
    >
      <HardHat className="h-3 w-3" />
      {trade} licensed
    </Badge>
  );
}

export function RiskBadge({
  tier,
  className,
}: {
  tier: RiskTier;
  className?: string;
}) {
  if (tier === 'low') return null;

  return (
    <Badge
      variant={tier === 'high_licensed' ? 'destructive' : 'warning'}
      className={className}
      title={
        tier === 'high_licensed'
          ? 'Only workers with a verified trade licence can bid on this task'
          : 'Elevated-risk work — read the hazard notice before bidding'
      }
    >
      <TriangleAlert className="h-3 w-3" />
      {RISK_TIER_LABELS[tier]}
    </Badge>
  );
}

export function RepScore({
  score,
  count,
  className,
}: {
  score: number;
  count: number;
  className?: string;
}) {
  if (count === 0) {
    return (
      <span className={cn('text-xs text-muted-foreground', className)}>
        No reviews yet
      </span>
    );
  }

  return (
    <span className={cn('flex items-center gap-1 text-xs', className)}>
      <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
      <span className="font-medium">{Number(score).toFixed(1)}</span>
      <span className="text-muted-foreground">({count})</span>
    </span>
  );
}
