'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { CheckCircle2, Loader2, Lock, ShieldAlert, Timer } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { createClient } from '@/lib/supabase/client';
import { formatCurrency, hoursUntil } from '@/lib/utils';
import type { ApiResponse } from '@/types/api';
import type { Task, Transaction } from '@/types/database';

/**
 * The escrow surface both parties see once money is committed.
 *
 * Deliberately explicit about where the money is and what happens next: the
 * single most common support burden on marketplaces like this is "you've taken
 * my money" when in fact nothing has been captured yet.
 */
export function EscrowPanel({
  task,
  transaction,
  viewerRole,
  currency = 'USD',
}: {
  task: Pick<Task, 'id' | 'status' | 'released_after' | 'completed_at'>;
  transaction: Pick<
    Transaction,
    'id' | 'escrow_status' | 'amount' | 'platform_fee' | 'payout_amount'
  > | null;
  viewerRole: 'requester' | 'member';
  currency?: string;
}) {
  const router = useRouter();
  const [busy, setBusy] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [disputeOpen, setDisputeOpen] = React.useState(false);
  const [disputeReason, setDisputeReason] = React.useState('');

  const hoursLeft = hoursUntil(task.released_after);

  async function call(path: string, body?: unknown) {
    setBusy(path);
    setError(null);
    try {
      const response = await fetch(path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : undefined,
      });
      const payload = (await response.json()) as ApiResponse<unknown>;
      if (!payload.ok) {
        setError(payload.error.message);
        return false;
      }
      router.refresh();
      return true;
    } catch {
      setError('Request failed. Nothing was changed.');
      return false;
    } finally {
      setBusy(null);
    }
  }

  async function markDelivered() {
    setBusy('delivered');
    setError(null);
    const supabase = createClient();
    const { error: rpcError } = await supabase.rpc('mark_task_delivered', {
      p_task_id: task.id,
    });
    setBusy(null);
    if (rpcError) setError(rpcError.message);
    else router.refresh();
  }

  async function raiseDispute() {
    if (disputeReason.trim().length < 20) return;
    setBusy('dispute');
    setError(null);

    const supabase = createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      setError('Session expired.');
      setBusy(null);
      return;
    }

    const { error: insertError } = await supabase.from('disputes').insert({
      task_id: task.id,
      raised_by: user.id,
      reason: disputeReason.trim(),
    });

    setBusy(null);
    if (insertError) setError(insertError.message);
    else router.refresh();
  }

  if (!transaction) return null;

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base">
          <Lock className="h-4 w-4" />
          Escrow
        </CardTitle>
        <EscrowBadge status={transaction.escrow_status} />
      </CardHeader>

      <CardContent className="space-y-4">
        <dl className="space-y-1.5 text-sm">
          <div className="flex justify-between">
            <dt className="text-muted-foreground">Agreed price</dt>
            <dd className="font-medium tabular-nums">
              {formatCurrency(transaction.amount, currency)}
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-muted-foreground">Platform fee</dt>
            <dd className="tabular-nums">
              −{formatCurrency(transaction.platform_fee, currency)}
            </dd>
          </div>
          <div className="flex justify-between border-t pt-1.5">
            <dt className="text-muted-foreground">
              {viewerRole === 'member' ? 'You receive' : 'Worker receives'}
            </dt>
            <dd className="font-semibold tabular-nums">
              {formatCurrency(transaction.payout_amount, currency)}
            </dd>
          </div>
        </dl>

        {transaction.escrow_status === 'held' && (
          <p className="rounded-md bg-muted p-3 text-xs leading-relaxed">
            {viewerRole === 'requester'
              ? 'Your card is authorised but not charged. Money moves only when you sign off, or automatically once the dispute window closes.'
              : 'The requester’s payment is authorised and ring-fenced for this task. It is released to you on sign-off, or automatically once the window closes.'}
          </p>
        )}

        {hoursLeft !== null && transaction.escrow_status === 'held' && (
          <p className="flex items-center gap-2 text-sm">
            <Timer className="h-4 w-4 text-muted-foreground" />
            {hoursLeft > 0
              ? `Auto-releases in ${Math.ceil(hoursLeft)}h unless disputed`
              : 'Auto-release is due on the next sweep'}
          </p>
        )}

        {error && (
          <p role="alert" className="text-sm text-destructive">
            {error}
          </p>
        )}

        <div className="flex flex-wrap gap-2">
          {viewerRole === 'member' && task.status === 'in_escrow' && !task.completed_at && (
            <Button size="sm" disabled={busy !== null} onClick={markDelivered}>
              {busy === 'delivered' ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <CheckCircle2 className="h-4 w-4" />
              )}
              Mark delivered
            </Button>
          )}

          {viewerRole === 'requester' &&
            transaction.escrow_status === 'held' && (
              <Button
                size="sm"
                disabled={busy !== null}
                onClick={() =>
                  call('/api/stripe/escrow/release', {
                    taskId: task.id,
                    reason: 'manual_signoff',
                  })
                }
              >
                {busy === '/api/stripe/escrow/release' ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <CheckCircle2 className="h-4 w-4" />
                )}
                Sign off &amp; release funds
              </Button>
            )}

          {transaction.escrow_status === 'held' && task.status !== 'disputed' && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => setDisputeOpen((open) => !open)}
            >
              <ShieldAlert className="h-4 w-4" />
              Raise a dispute
            </Button>
          )}
        </div>

        {disputeOpen && (
          <div className="space-y-2 rounded-md border p-3">
            <Textarea
              rows={4}
              value={disputeReason}
              placeholder="What went wrong, and what outcome are you asking for? Attach photos in the chat — an admin reads both sides."
              onChange={(e) => setDisputeReason(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Raising a dispute freezes the auto-release timer immediately.
            </p>
            <Button
              size="sm"
              variant="destructive"
              disabled={disputeReason.trim().length < 20 || busy !== null}
              onClick={raiseDispute}
            >
              {busy === 'dispute' && <Loader2 className="h-4 w-4 animate-spin" />}
              Submit dispute
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function EscrowBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; variant: 'warning' | 'info' | 'success' | 'secondary' }> = {
    pending_hold: { label: 'Awaiting authorisation', variant: 'warning' },
    held: { label: 'Funds held', variant: 'info' },
    released: { label: 'Released', variant: 'success' },
    refunded: { label: 'Refunded', variant: 'secondary' },
  };
  const entry = map[status] ?? { label: status, variant: 'secondary' as const };
  return <Badge variant={entry.variant}>{entry.label}</Badge>;
}
