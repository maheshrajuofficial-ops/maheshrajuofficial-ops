'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { Clock, Loader2, ShieldCheck } from 'lucide-react';

import {
  BackgroundCheckedBadge,
  IdVerifiedBadge,
  LicenceBadge,
  RepScore,
} from '@/components/trust/verification-badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { getStripeClient } from '@/lib/stripe/client';
import { formatCurrency, formatRelativeTime, initials } from '@/lib/utils';
import type { AcceptBidResponse, ApiResponse } from '@/types/api';
import type { BidWithMember } from '@/types/database';

/**
 * The requester's view of incoming bids.
 *
 * Accepting is the moment money enters the picture: the API creates a
 * manual-capture PaymentIntent and hands back a client secret, which we
 * confirm here. The card is authorised, not charged — funds stay with the
 * requester's bank until sign-off.
 */
export function BidList({
  bids,
  currency = 'USD',
  canAccept,
}: {
  bids: BidWithMember[];
  currency?: string;
  canAccept: boolean;
}) {
  const router = useRouter();
  const [busyBidId, setBusyBidId] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  async function accept(bid: BidWithMember) {
    setBusyBidId(bid.id);
    setError(null);

    try {
      const response = await fetch(`/api/bids/${bid.id}/accept`, { method: 'POST' });
      const payload = (await response.json()) as ApiResponse<AcceptBidResponse>;

      if (!payload.ok) {
        setError(payload.error.message);
        return;
      }

      const stripe = await getStripeClient();
      if (!stripe) {
        setError('Payments are unavailable right now.');
        return;
      }

      const { error: stripeError } = await stripe.confirmPayment({
        clientSecret: payload.data.clientSecret,
        confirmParams: {
          return_url: `${window.location.origin}${window.location.pathname}?escrow=authorized`,
        },
        // Stripe redirects for 3DS; for cards that don't need it we stay put.
        redirect: 'if_required',
      });

      if (stripeError) {
        setError(stripeError.message ?? 'Card authorisation failed.');
        return;
      }

      router.refresh();
    } catch {
      setError('Could not accept that bid. Nothing was charged.');
    } finally {
      setBusyBidId(null);
    }
  }

  if (bids.length === 0) {
    return (
      <p className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
        No bids yet. Tasks with a clear description and a photo typically get
        their first bid within a few hours.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {error && (
        <p role="alert" className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </p>
      )}

      {bids.map((bid) => (
        <Card key={bid.id}>
          <CardHeader className="flex-row items-start gap-3 space-y-0 pb-3">
            <Avatar className="h-10 w-10 border">
              {bid.member.avatar_url && <AvatarImage src={bid.member.avatar_url} alt="" />}
              <AvatarFallback>{initials(bid.member.full_name)}</AvatarFallback>
            </Avatar>

            <div className="min-w-0 flex-1">
              <p className="font-medium leading-tight">
                {bid.member.full_name ?? 'Guild member'}
              </p>
              <div className="mt-1 flex flex-wrap items-center gap-2">
                <RepScore score={bid.member.rep_score} count={bid.member.rep_count} />
                <span className="text-xs text-muted-foreground">
                  {bid.member.tasks_completed} completed
                </span>
              </div>
            </div>

            <div className="text-right">
              <p className="text-lg font-semibold tabular-nums">
                {formatCurrency(bid.amount, currency)}
              </p>
              {bid.estimated_hours && (
                <p className="flex items-center justify-end gap-1 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  ~{bid.estimated_hours}h
                </p>
              )}
            </div>
          </CardHeader>

          <CardContent className="space-y-3 pb-3">
            <div className="flex flex-wrap gap-1.5">
              {bid.member.is_id_verified && <IdVerifiedBadge />}
              {bid.member.is_background_checked && <BackgroundCheckedBadge />}
              {bid.member.licensed_trades.map((trade) => (
                <LicenceBadge key={trade} trade={trade} />
              ))}
            </div>
            <p className="whitespace-pre-line text-sm leading-relaxed">
              {bid.proposal_text}
            </p>
          </CardContent>

          <CardFooter className="justify-between border-t pt-4">
            <span className="text-xs text-muted-foreground">
              {formatRelativeTime(bid.created_at)}
            </span>

            {canAccept && bid.status === 'pending' && (
              <Button
                size="sm"
                disabled={busyBidId !== null}
                onClick={() => accept(bid)}
              >
                {busyBidId === bid.id ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <ShieldCheck className="h-4 w-4" />
                )}
                Accept &amp; hold {formatCurrency(bid.amount, currency)}
              </Button>
            )}

            {bid.status === 'accepted' && (
              <span className="text-sm font-medium text-emerald-600">Accepted</span>
            )}
          </CardFooter>
        </Card>
      ))}
    </div>
  );
}
