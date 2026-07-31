'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { Loader2, Star } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { createClient } from '@/lib/supabase/client';
import { cn } from '@/lib/utils';

/**
 * Post-completion review. The database trigger enforces that the task is
 * completed and both parties are on it, so this form only has to be honest
 * about what it's collecting.
 */
export function ReviewForm({
  taskId,
  reviewerId,
  revieweeId,
  revieweeName,
}: {
  taskId: string;
  reviewerId: string;
  revieweeId: string;
  revieweeName: string;
}) {
  const router = useRouter();
  const [rating, setRating] = React.useState(0);
  const [hovered, setHovered] = React.useState(0);
  const [comment, setComment] = React.useState('');
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!rating) return;

    setSubmitting(true);
    setError(null);

    const supabase = createClient();
    const { error: insertError } = await supabase.from('reviews').insert({
      task_id: taskId,
      reviewer_id: reviewerId,
      reviewee_id: revieweeId,
      rating,
      comment: comment.trim() || null,
    });

    setSubmitting(false);

    if (insertError) {
      setError(insertError.message);
      return;
    }

    router.refresh();
  }

  return (
    <form onSubmit={submit} className="space-y-4 rounded-lg border p-5">
      <div>
        <h3 className="font-semibold">How did it go with {revieweeName}?</h3>
        <p className="text-sm text-muted-foreground">
          Reviews are public and permanent, and they are what the rep score is
          built from.
        </p>
      </div>

      <div className="flex gap-1" role="radiogroup" aria-label="Rating">
        {[1, 2, 3, 4, 5].map((value) => (
          <button
            key={value}
            type="button"
            role="radio"
            aria-checked={rating === value}
            aria-label={`${value} star${value === 1 ? '' : 's'}`}
            onClick={() => setRating(value)}
            onMouseEnter={() => setHovered(value)}
            onMouseLeave={() => setHovered(0)}
            className="rounded p-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <Star
              className={cn(
                'h-7 w-7 transition-colors',
                value <= (hovered || rating)
                  ? 'fill-amber-400 text-amber-400'
                  : 'text-muted-foreground'
              )}
            />
          </button>
        ))}
      </div>

      <Textarea
        rows={4}
        maxLength={2000}
        value={comment}
        placeholder="What would the next person want to know?"
        onChange={(e) => setComment(e.target.value)}
      />

      {error && (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}

      <Button type="submit" disabled={!rating || submitting}>
        {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
        Leave review
      </Button>
    </form>
  );
}
