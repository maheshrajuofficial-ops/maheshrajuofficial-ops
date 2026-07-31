import { notFound } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, CalendarClock, MapPin } from 'lucide-react';

import { BidForm } from '@/components/bids/bid-form';
import { BidList } from '@/components/bids/bid-list';
import { TaskChat } from '@/components/chat/task-chat';
import { EscrowPanel } from '@/components/tasks/escrow-panel';
import { RepScore, RiskBadge, IdVerifiedBadge } from '@/components/trust/verification-badge';
import { ReviewForm } from '@/components/trust/review-form';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { TASK_STATUS_LABELS } from '@/lib/constants';
import { createClient } from '@/lib/supabase/server';
import { formatCurrency, formatRelativeTime, initials } from '@/lib/utils';
import type { BidWithMember, MessageWithSender } from '@/types/database';

interface PageProps {
  params: { city: string; taskId: string };
}

export default async function TaskDetailPage({ params }: PageProps) {
  const supabase = createClient();

  const [{ data: task }, { data: auth }] = await Promise.all([
    supabase
      .from('tasks')
      .select(
        `*,
         category:categories!tasks_category_id_fkey (id, name, slug, icon, is_licensed_trade_required),
         city:cities!tasks_city_id_fkey (id, name, slug, currency),
         requester:users!tasks_requester_id_fkey (id, full_name, avatar_url, rep_score, rep_count, is_id_verified)`
      )
      .eq('id', params.taskId)
      .single(),
    supabase.auth.getUser(),
  ]);

  if (!task) notFound();

  const viewerId = auth?.user?.id ?? null;
  const isRequester = viewerId === task.requester_id;
  const isAssigned = viewerId !== null && viewerId === task.assigned_to;
  const isParticipant = isRequester || isAssigned;
  const currency = (task.city as { currency?: string })?.currency ?? 'USD';

  // RLS already restricts what comes back here; these queries just avoid
  // asking for rows the viewer definitionally can't see.
  const [{ data: bids }, { data: transaction }, { data: messages }, { data: myBid }, { data: reviews }] =
    await Promise.all([
      isRequester
        ? supabase
            .from('bids')
            .select(
              `*, member:users!bids_member_id_fkey (id, full_name, avatar_url, rep_score, rep_count, tasks_completed, is_id_verified, is_background_checked, licensed_trades)`
            )
            .eq('task_id', task.id)
            .order('amount')
        : { data: null },
      isParticipant
        ? supabase
            .from('transactions')
            .select('id, escrow_status, amount, platform_fee, payout_amount')
            .eq('task_id', task.id)
            .order('created_at', { ascending: false })
            .limit(1)
            .maybeSingle()
        : { data: null },
      isParticipant && task.assigned_to
        ? supabase
            .from('messages')
            .select(`*, sender:users!messages_sender_id_fkey (id, full_name, avatar_url)`)
            .eq('task_id', task.id)
            .order('created_at')
            .limit(200)
        : { data: null },
      viewerId && !isRequester
        ? supabase
            .from('bids')
            .select('id, amount, proposal_text, estimated_hours')
            .eq('task_id', task.id)
            .eq('member_id', viewerId)
            .maybeSingle()
        : { data: null },
      supabase
        .from('reviews')
        .select('id, rating, comment, reviewer_id, created_at')
        .eq('task_id', task.id),
    ]);

  const requester = task.requester as {
    id: string;
    full_name: string | null;
    avatar_url: string | null;
    rep_score: number;
    rep_count: number;
    is_id_verified: boolean;
  };

  const alreadyReviewed = (reviews ?? []).some((r) => r.reviewer_id === viewerId);

  return (
    <div className="container grid gap-8 py-8 lg:grid-cols-[1fr_22rem]">
      <div className="min-w-0 space-y-6">
        <Button asChild variant="ghost" size="sm" className="-ml-2">
          <Link href={`/${params.city}`}>
            <ArrowLeft className="h-4 w-4" />
            Back to the board
          </Link>
        </Button>

        <header className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary">
              {(task.category as { name: string })?.name}
            </Badge>
            <RiskBadge tier={task.risk_tier} />
            <Badge variant="outline">{TASK_STATUS_LABELS[task.status]}</Badge>
          </div>

          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
            {task.title}
          </h1>

          <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <MapPin className="h-4 w-4" />
              {(task.city as { name: string })?.name}
              {/* The precise address is only rendered for the assigned member. */}
              {isAssigned && task.address_line && ` · ${task.address_line}`}
            </span>
            {task.deadline_at && (
              <span className="flex items-center gap-1.5">
                <CalendarClock className="h-4 w-4" />
                Due {new Date(task.deadline_at).toLocaleDateString()}
              </span>
            )}
            <span>Posted {formatRelativeTime(task.created_at)}</span>
          </div>
        </header>

        {task.image_urls.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {task.image_urls.map((url: string) => (
              /* eslint-disable-next-line @next/next/no-img-element */
              <img
                key={url}
                src={url}
                alt=""
                className="h-32 w-32 rounded-lg border object-cover"
              />
            ))}
          </div>
        )}

        <div className="prose prose-sm max-w-none dark:prose-invert">
          <p className="whitespace-pre-line leading-relaxed">{task.description}</p>
        </div>

        <Separator />

        {isRequester && (
          <section className="space-y-4">
            <h2 className="text-lg font-semibold">
              Bids ({(bids ?? []).length})
            </h2>
            <BidList
              bids={(bids ?? []) as BidWithMember[]}
              currency={currency}
              canAccept={task.status === 'open'}
            />
          </section>
        )}

        {!isRequester && viewerId && (
          <BidForm
            taskId={task.id}
            suggestedAmount={task.reward_amount}
            currency={currency}
            existingBid={myBid}
            disabledReason={
              task.status !== 'open'
                ? 'This task is no longer accepting bids.'
                : null
            }
          />
        )}

        {!viewerId && (
          <div className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
            <Link href="/login" className="font-medium text-primary underline">
              Log in
            </Link>{' '}
            to bid on this task.
          </div>
        )}

        {isParticipant && task.assigned_to && viewerId && (
          <section className="space-y-4">
            <h2 className="text-lg font-semibold">Chat</h2>
            <TaskChat
              taskId={task.id}
              currentUserId={viewerId}
              counterparty={
                isRequester
                  ? { id: task.assigned_to, full_name: 'Assigned member', avatar_url: null }
                  : {
                      id: requester.id,
                      full_name: requester.full_name,
                      avatar_url: requester.avatar_url,
                    }
              }
              initialMessages={(messages ?? []) as MessageWithSender[]}
            />
          </section>
        )}

        {isParticipant && task.status === 'completed' && !alreadyReviewed && viewerId && (
          <ReviewForm
            taskId={task.id}
            reviewerId={viewerId}
            revieweeId={isRequester ? task.assigned_to! : task.requester_id}
            revieweeName={isRequester ? 'the worker' : requester.full_name ?? 'the requester'}
          />
        )}
      </div>

      <aside className="space-y-4 lg:sticky lg:top-24 lg:self-start">
        <div className="rounded-lg border p-5">
          <p className="text-sm text-muted-foreground">Posted budget</p>
          <p className="text-3xl font-semibold tabular-nums">
            {formatCurrency(task.reward_amount, currency)}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Workers bid their own price against this.
          </p>

          <Separator className="my-4" />

          <div className="flex items-center gap-3">
            <Avatar className="h-10 w-10 border">
              {requester.avatar_url && <AvatarImage src={requester.avatar_url} alt="" />}
              <AvatarFallback>{initials(requester.full_name)}</AvatarFallback>
            </Avatar>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">
                {requester.full_name ?? 'Guild requester'}
              </p>
              <RepScore score={requester.rep_score} count={requester.rep_count} />
            </div>
          </div>
          {requester.is_id_verified && <IdVerifiedBadge className="mt-3" />}
        </div>

        {isParticipant && (
          <EscrowPanel
            task={task}
            transaction={transaction ?? null}
            viewerRole={isRequester ? 'requester' : 'member'}
            currency={currency}
          />
        )}
      </aside>
    </div>
  );
}
