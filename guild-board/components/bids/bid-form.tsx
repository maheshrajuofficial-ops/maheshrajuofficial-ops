'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { Loader2, Send } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { formatCurrency } from '@/lib/utils';
import type { ApiResponse } from '@/types/api';
import type { Bid } from '@/types/database';

/**
 * Worker proposal form.
 *
 * The counter-price is the point: the requester's number is an anchor, not a
 * fixed fee, and a worker who explains why the job is worth more than the
 * anchor is the whole value of a bidding board over a fixed-rate one.
 */
export function BidForm({
  taskId,
  suggestedAmount,
  currency = 'USD',
  existingBid,
  disabledReason,
}: {
  taskId: string;
  suggestedAmount: number;
  currency?: string;
  existingBid?: Pick<Bid, 'id' | 'amount' | 'proposal_text' | 'estimated_hours'> | null;
  disabledReason?: string | null;
}) {
  const router = useRouter();
  const [amount, setAmount] = React.useState(
    String(existingBid?.amount ?? suggestedAmount)
  );
  const [proposal, setProposal] = React.useState(existingBid?.proposal_text ?? '');
  const [hours, setHours] = React.useState(
    existingBid?.estimated_hours ? String(existingBid.estimated_hours) : ''
  );
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const delta = Number(amount) - suggestedAmount;
  const valid = Number(amount) >= 5 && proposal.trim().length >= 20;

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const response = await fetch('/api/bids', {
        method: existingBid ? 'PATCH' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bidId: existingBid?.id,
          taskId,
          amount: Number(amount),
          proposalText: proposal.trim(),
          estimatedHours: hours ? Number(hours) : undefined,
        }),
      });

      const payload = (await response.json()) as ApiResponse<{ bid: Bid }>;

      if (!payload.ok) {
        setError(payload.error.message);
        return;
      }

      router.refresh();
    } catch {
      setError('Could not submit your bid. Try again.');
    } finally {
      setSubmitting(false);
    }
  }

  if (disabledReason) {
    return (
      <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
        {disabledReason}
      </div>
    );
  }

  return (
    <form onSubmit={submit} className="space-y-4 rounded-lg border p-5">
      <div>
        <h3 className="font-semibold">
          {existingBid ? 'Update your proposal' : 'Bid on this task'}
        </h3>
        <p className="text-sm text-muted-foreground">
          Only the requester sees your bid — this is a sealed board.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="bid-amount">Your price</Label>
          <Input
            id="bid-amount"
            type="number"
            min={5}
            step="1"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />
          {Number.isFinite(delta) && delta !== 0 && (
            <p className="text-xs text-muted-foreground">
              {delta > 0 ? '+' : '−'}
              {formatCurrency(Math.abs(delta), currency)}{' '}
              {delta > 0 ? 'above' : 'below'} the posted budget
            </p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="bid-hours">Estimated hours (optional)</Label>
          <Input
            id="bid-hours"
            type="number"
            min={0.5}
            step="0.5"
            value={hours}
            placeholder="2.5"
            onChange={(e) => setHours(e.target.value)}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="bid-proposal">Your proposal</Label>
        <Textarea
          id="bid-proposal"
          rows={5}
          value={proposal}
          maxLength={2000}
          placeholder="How you'd approach it, what you bring, when you can start. If you're pricing above the budget, say why here — it works more often than you'd think."
          onChange={(e) => setProposal(e.target.value)}
        />
        <p className="text-xs text-muted-foreground">
          {proposal.length} characters (20 minimum)
        </p>
      </div>

      {error && (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}

      <Button type="submit" disabled={!valid || submitting} className="w-full sm:w-auto">
        {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
        {existingBid ? 'Update bid' : 'Submit bid'}
      </Button>
    </form>
  );
}
