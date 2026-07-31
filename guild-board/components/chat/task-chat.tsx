'use client';

import * as React from 'react';
import type { RealtimeChannel } from '@supabase/supabase-js';
import { Camera, Loader2, SendHorizonal } from 'lucide-react';

import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { createClient } from '@/lib/supabase/client';
import { cn, formatRelativeTime, initials } from '@/lib/utils';
import type { Message, MessageWithSender } from '@/types/database';

/**
 * Task-scoped realtime chat.
 *
 * The subscription filters on `task_id`, but that filter is a convenience,
 * not the security boundary — RLS on `messages` is. A client that tampers
 * with the filter still only receives rows its JWT can select, which is why
 * the policy is written in terms of task participation rather than a
 * client-supplied room id.
 */
export function TaskChat({
  taskId,
  currentUserId,
  counterparty,
  initialMessages,
}: {
  taskId: string;
  currentUserId: string;
  counterparty: { id: string; full_name: string | null; avatar_url: string | null };
  initialMessages: MessageWithSender[];
}) {
  const [messages, setMessages] = React.useState<MessageWithSender[]>(initialMessages);
  const [draft, setDraft] = React.useState('');
  const [sending, setSending] = React.useState(false);
  const [uploading, setUploading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const bottom = React.useRef<HTMLDivElement>(null);

  const supabase = React.useMemo(() => createClient(), []);

  React.useEffect(() => {
    let channel: RealtimeChannel;

    channel = supabase
      .channel(`task:${taskId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'messages',
          filter: `task_id=eq.${taskId}`,
        },
        (payload) => {
          const row = payload.new as Message;
          setMessages((prev) => {
            if (prev.some((m) => m.id === row.id)) return prev;
            return [
              ...prev,
              {
                ...row,
                sender:
                  row.sender_id === currentUserId
                    ? { id: currentUserId, full_name: 'You', avatar_url: null }
                    : counterparty,
              },
            ];
          });
        }
      )
      .subscribe();

    return () => {
      void supabase.removeChannel(channel);
    };
  }, [supabase, taskId, currentUserId, counterparty]);

  React.useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  async function send(event: React.FormEvent) {
    event.preventDefault();
    const body = draft.trim();
    if (!body) return;

    setSending(true);
    setError(null);
    setDraft('');

    const { error: insertError } = await supabase
      .from('messages')
      .insert({ task_id: taskId, sender_id: currentUserId, body });

    if (insertError) {
      setError(insertError.message);
      setDraft(body);
    }

    setSending(false);
  }

  async function sendPhoto(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError(null);

    try {
      // Foldered by task id — the storage policy checks participation on it.
      const path = `${taskId}/${crypto.randomUUID()}-${file.name.replace(/[^\w.-]/g, '_')}`;
      const { error: uploadError } = await supabase.storage
        .from('completion-proof')
        .upload(path, file);

      if (uploadError) throw uploadError;

      const { data, error: signError } = await supabase.storage
        .from('completion-proof')
        .createSignedUrl(path, 60 * 60 * 24 * 30);

      if (signError) throw signError;

      const { error: insertError } = await supabase.from('messages').insert({
        task_id: taskId,
        sender_id: currentUserId,
        body: 'Photo proof attached',
        attachment_urls: [data.signedUrl],
        is_proof: true,
      });

      if (insertError) throw insertError;
    } catch (uploadError) {
      setError(
        uploadError instanceof Error ? uploadError.message : 'Could not upload that photo.'
      );
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  }

  return (
    <div className="flex h-[32rem] flex-col rounded-lg border">
      <header className="flex items-center gap-2 border-b px-4 py-3">
        <Avatar className="h-8 w-8 border">
          {counterparty.avatar_url && <AvatarImage src={counterparty.avatar_url} alt="" />}
          <AvatarFallback>{initials(counterparty.full_name)}</AvatarFallback>
        </Avatar>
        <div className="min-w-0">
          <p className="truncate text-sm font-medium">
            {counterparty.full_name ?? 'Guild member'}
          </p>
          <p className="text-xs text-muted-foreground">
            Private to this task — nobody else can read it
          </p>
        </div>
      </header>

      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.length === 0 && (
          <p className="py-8 text-center text-sm text-muted-foreground">
            Chat is open. Agree access, timing and what &ldquo;done&rdquo; looks
            like before work starts.
          </p>
        )}

        {messages.map((message) => {
          const mine = message.sender_id === currentUserId;
          return (
            <div
              key={message.id}
              className={cn('flex gap-2', mine && 'flex-row-reverse')}
            >
              <div
                className={cn(
                  'max-w-[80%] space-y-2 rounded-lg px-3 py-2 text-sm',
                  mine ? 'bg-primary text-primary-foreground' : 'bg-muted'
                )}
              >
                {message.is_proof && (
                  <Badge variant="secondary" className="mb-1">
                    Completion proof
                  </Badge>
                )}
                {message.body && <p className="whitespace-pre-line">{message.body}</p>}
                {message.attachment_urls.map((url) => (
                  /* eslint-disable-next-line @next/next/no-img-element */
                  <img
                    key={url}
                    src={url}
                    alt="Attachment"
                    className="max-h-56 rounded border object-cover"
                  />
                ))}
                <time
                  className={cn(
                    'block text-[10px]',
                    mine ? 'text-primary-foreground/70' : 'text-muted-foreground'
                  )}
                >
                  {formatRelativeTime(message.created_at)}
                </time>
              </div>
            </div>
          );
        })}
        <div ref={bottom} />
      </div>

      {error && (
        <p role="alert" className="border-t px-4 py-2 text-xs text-destructive">
          {error}
        </p>
      )}

      <form onSubmit={send} className="flex items-center gap-2 border-t p-3">
        <label
          className={cn(
            'grid h-9 w-9 shrink-0 cursor-pointer place-items-center rounded-md border hover:bg-accent',
            uploading && 'pointer-events-none opacity-60'
          )}
          title="Attach photo proof"
        >
          {uploading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Camera className="h-4 w-4" />
          )}
          <input type="file" accept="image/*" className="sr-only" onChange={sendPhoto} />
        </label>

        <Input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Message…"
          aria-label="Message"
        />

        <Button type="submit" size="icon" disabled={sending || !draft.trim()}>
          {sending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <SendHorizonal className="h-4 w-4" />
          )}
          <span className="sr-only">Send</span>
        </Button>
      </form>
    </div>
  );
}
