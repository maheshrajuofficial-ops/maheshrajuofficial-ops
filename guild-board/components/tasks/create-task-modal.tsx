'use client';

import * as React from 'react';
import dynamic from 'next/dynamic';
import { useRouter } from 'next/navigation';
import { AnimatePresence, motion } from 'framer-motion';
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Check,
  ImagePlus,
  Loader2,
  Plus,
  X,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { SAFETY_DISCLAIMER, SAFETY_DISCLAIMER_VERSION, REWARD_MIN } from '@/lib/constants';
import { createClient } from '@/lib/supabase/client';
import { cn, formatCurrency } from '@/lib/utils';
import type { ApiResponse, CreateTaskResponse, SafetyVerdict } from '@/types/api';
import type { Category, City } from '@/types/database';

// Mapbox is ~550kB and is only needed on step 2 of a modal most visitors never
// open, so it loads on demand rather than with the board.
const LocationPicker = dynamic(
  () => import('@/components/tasks/location-picker').then((mod) => mod.LocationPicker),
  {
    ssr: false,
    loading: () => <div className="h-64 w-full animate-pulse rounded-lg border bg-muted/40" />,
  }
);

type Step = 0 | 1 | 2 | 3;

const STEPS = [
  { title: 'What do you need?', hint: 'Title, category and the detail that matters.' },
  { title: 'Where and when', hint: 'Drop a pin and set a deadline.' },
  { title: 'Budget and photos', hint: 'What it is worth, and what it looks like.' },
  { title: 'Safety and terms', hint: 'Read this properly — it is the deal.' },
] as const;

interface Draft {
  title: string;
  description: string;
  categoryId: string;
  lat: number | null;
  long: number | null;
  addressLine: string;
  deadlineAt: string;
  rewardAmount: string;
  imageUrls: string[];
}

export function CreateTaskModal({
  city,
  categories,
  isAuthenticated,
}: {
  city: Pick<City, 'id' | 'name' | 'slug' | 'lat' | 'long' | 'currency'>;
  categories: Pick<Category, 'id' | 'name' | 'slug' | 'is_licensed_trade_required'>[];
  isAuthenticated: boolean;
}) {
  const router = useRouter();
  const [open, setOpen] = React.useState(false);
  const [step, setStep] = React.useState<Step>(0);
  const [submitting, setSubmitting] = React.useState(false);
  const [uploading, setUploading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [safety, setSafety] = React.useState<SafetyVerdict | null>(null);
  const [acknowledged, setAcknowledged] = React.useState(false);

  const [draft, setDraft] = React.useState<Draft>({
    title: '',
    description: '',
    categoryId: '',
    lat: null,
    long: null,
    addressLine: '',
    deadlineAt: '',
    rewardAmount: '',
    imageUrls: [],
  });

  const selectedCategory = categories.find((c) => c.id === draft.categoryId);

  function update<K extends keyof Draft>(key: K, value: Draft[K]) {
    setDraft((prev) => ({ ...prev, [key]: value }));
    setError(null);
  }

  const stepValid: Record<Step, boolean> = {
    0:
      draft.title.trim().length >= 8 &&
      draft.description.trim().length >= 20 &&
      Boolean(draft.categoryId),
    1: draft.lat !== null && draft.long !== null,
    2: Number(draft.rewardAmount) >= REWARD_MIN,
    3: acknowledged,
  };

  async function handleUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []);
    if (!files.length) return;

    setUploading(true);
    setError(null);

    try {
      const supabase = createClient();
      const {
        data: { user },
      } = await supabase.auth.getUser();

      if (!user) throw new Error('Sign in to attach photos.');

      const uploaded: string[] = [];
      for (const file of files.slice(0, 6 - draft.imageUrls.length)) {
        // Storage RLS keys off the first path segment being the user id.
        const path = `${user.id}/${crypto.randomUUID()}-${file.name.replace(/[^\w.-]/g, '_')}`;
        const { error: uploadError } = await supabase.storage
          .from('task-photos')
          .upload(path, file, { cacheControl: '3600', upsert: false });

        if (uploadError) throw uploadError;

        const { data } = supabase.storage.from('task-photos').getPublicUrl(path);
        uploaded.push(data.publicUrl);
      }

      update('imageUrls', [...draft.imageUrls, ...uploaded]);
    } catch (uploadError) {
      setError(
        uploadError instanceof Error ? uploadError.message : 'Could not upload that image.'
      );
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  }

  async function handleSubmit() {
    setSubmitting(true);
    setError(null);
    setSafety(null);

    try {
      const response = await fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: draft.title.trim(),
          description: draft.description.trim(),
          citySlug: city.slug,
          categoryId: draft.categoryId,
          rewardAmount: Number(draft.rewardAmount),
          lat: draft.lat,
          long: draft.long,
          addressLine: draft.addressLine || undefined,
          deadlineAt: draft.deadlineAt || undefined,
          imageUrls: draft.imageUrls,
          safetyAckVersion: SAFETY_DISCLAIMER_VERSION,
        }),
      });

      const payload = (await response.json()) as ApiResponse<CreateTaskResponse>;

      if (!payload.ok) {
        setError(payload.error.message);
        if (payload.error.safety) setSafety(payload.error.safety);
        return;
      }

      setOpen(false);
      reset();
      router.push(`/${city.slug}/tasks/${payload.data.task.id}`);
      router.refresh();
    } catch {
      setError('Could not reach the server. Check your connection and try again.');
    } finally {
      setSubmitting(false);
    }
  }

  function reset() {
    setStep(0);
    setDraft({
      title: '',
      description: '',
      categoryId: '',
      lat: null,
      long: null,
      addressLine: '',
      deadlineAt: '',
      rewardAmount: '',
      imageUrls: [],
    });
    setAcknowledged(false);
    setSafety(null);
    setError(null);
  }

  if (!isAuthenticated) {
    return (
      <Button asChild>
        <a href="/login?next=post">
          <Plus className="h-4 w-4" />
          Post a task
        </a>
      </Button>
    );
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (!next) reset();
      }}
    >
      <DialogTrigger asChild>
        <Button>
          <Plus className="h-4 w-4" />
          Post a task
        </Button>
      </DialogTrigger>

      <DialogContent className="max-h-[92vh] max-w-2xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{STEPS[step].title}</DialogTitle>
          <DialogDescription>{STEPS[step].hint}</DialogDescription>
        </DialogHeader>

        <StepIndicator step={step} />

        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -12 }}
            transition={{ duration: 0.15 }}
            className="space-y-4 py-2"
          >
            {step === 0 && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="title">Title</Label>
                  <Input
                    id="title"
                    value={draft.title}
                    maxLength={140}
                    placeholder="Move a two-seater sofa up three flights"
                    onChange={(e) => update('title', e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    {draft.title.length}/140 — specific titles get better bids.
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="category">Category</Label>
                  <Select
                    value={draft.categoryId}
                    onValueChange={(value) => update('categoryId', value)}
                  >
                    <SelectTrigger id="category">
                      <SelectValue placeholder="Pick the closest match" />
                    </SelectTrigger>
                    <SelectContent>
                      {categories.map((category) => (
                        <SelectItem key={category.id} value={category.id}>
                          {category.name}
                          {category.is_licensed_trade_required && ' · licensed trade'}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  {selectedCategory?.is_licensed_trade_required && (
                    <Notice tone="warning">
                      This is a licensed trade. Your task will be visible only to
                      workers with a verified {selectedCategory.name.toLowerCase()}{' '}
                      licence, and we check the licence before work starts.
                    </Notice>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">What needs doing</Label>
                  <Textarea
                    id="description"
                    rows={6}
                    maxLength={5000}
                    value={draft.description}
                    placeholder="Access, timing, what you already have, what you need them to bring. The more concrete this is, the fewer follow-up questions you'll field."
                    onChange={(e) => update('description', e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    {draft.description.length} characters (20 minimum)
                  </p>
                </div>
              </>
            )}

            {step === 1 && (
              <>
                <LocationPicker
                  center={{ lat: city.lat, long: city.long }}
                  value={draft.lat !== null && draft.long !== null
                    ? { lat: draft.lat, long: draft.long }
                    : null}
                  onChange={(point) => {
                    setDraft((prev) => ({ ...prev, lat: point.lat, long: point.long }));
                    setError(null);
                  }}
                />

                <div className="space-y-2">
                  <Label htmlFor="address">Address or access notes (private)</Label>
                  <Input
                    id="address"
                    value={draft.addressLine}
                    placeholder="Flat 4, buzzer B — shown only to the worker you accept"
                    onChange={(e) => update('addressLine', e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    The public board shows an approximate pin, never your exact
                    address.
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="deadline">Deadline (optional)</Label>
                  <Input
                    id="deadline"
                    type="datetime-local"
                    value={draft.deadlineAt}
                    onChange={(e) => update('deadlineAt', e.target.value)}
                  />
                </div>
              </>
            )}

            {step === 2 && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="reward">Your budget</Label>
                  <div className="relative">
                    <Input
                      id="reward"
                      type="number"
                      inputMode="decimal"
                      min={REWARD_MIN}
                      step="1"
                      className="pl-7 text-lg"
                      value={draft.rewardAmount}
                      onChange={(e) => update('rewardAmount', e.target.value)}
                    />
                    <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                      {city.currency === 'GBP' ? '£' : city.currency === 'EUR' ? '€' : '$'}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    This is a starting point — workers bid their own price, up or
                    down. Minimum {formatCurrency(REWARD_MIN, city.currency)}.
                  </p>
                </div>

                <div className="space-y-2">
                  <Label>Photos (optional, up to 6)</Label>
                  <div className="flex flex-wrap gap-2">
                    {draft.imageUrls.map((url) => (
                      <div key={url} className="relative">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src={url}
                          alt=""
                          className="h-20 w-20 rounded-md border object-cover"
                        />
                        <button
                          type="button"
                          className="absolute -right-1.5 -top-1.5 rounded-full bg-destructive p-0.5 text-destructive-foreground"
                          onClick={() =>
                            update(
                              'imageUrls',
                              draft.imageUrls.filter((u) => u !== url)
                            )
                          }
                          aria-label="Remove photo"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </div>
                    ))}

                    {draft.imageUrls.length < 6 && (
                      <label
                        className={cn(
                          'grid h-20 w-20 cursor-pointer place-items-center rounded-md border border-dashed text-muted-foreground hover:bg-accent',
                          uploading && 'pointer-events-none opacity-60'
                        )}
                      >
                        {uploading ? (
                          <Loader2 className="h-5 w-5 animate-spin" />
                        ) : (
                          <ImagePlus className="h-5 w-5" />
                        )}
                        <input
                          type="file"
                          accept="image/*"
                          multiple
                          className="sr-only"
                          onChange={handleUpload}
                        />
                      </label>
                    )}
                  </div>
                </div>
              </>
            )}

            {step === 3 && (
              <>
                <div className="rounded-lg border bg-muted/40 p-4">
                  <ul className="space-y-3 text-sm leading-relaxed">
                    {SAFETY_DISCLAIMER.map((clause) => (
                      <li key={clause} className="flex gap-2">
                        <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-foreground/50" />
                        <span>{clause}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <label className="flex cursor-pointer items-start gap-3 rounded-lg border p-4">
                  <input
                    type="checkbox"
                    className="mt-0.5 h-4 w-4"
                    checked={acknowledged}
                    onChange={(e) => setAcknowledged(e.target.checked)}
                  />
                  <span className="text-sm">
                    I have read the above, and I confirm this task is legal, is not
                    hazardous beyond ordinary care, and — if it touches a licensed
                    trade — will be done by someone holding the licence.
                  </span>
                </label>

                <ReviewSummary draft={draft} city={city} category={selectedCategory} />
              </>
            )}

            {safety && safety.action !== 'allow' && (
              <Notice tone={safety.action === 'block' ? 'destructive' : 'warning'}>
                <p className="font-medium">
                  {safety.action === 'block'
                    ? 'This task cannot be posted'
                    : 'This task needs a quick review'}
                </p>
                <p className="mt-1">{safety.reason}</p>
                {safety.requiredLicences.length > 0 && (
                  <p className="mt-2 flex flex-wrap items-center gap-1.5">
                    Required licence:
                    {safety.requiredLicences.map((licence) => (
                      <Badge key={licence} variant="outline" className="capitalize">
                        {licence}
                      </Badge>
                    ))}
                  </p>
                )}
              </Notice>
            )}

            {error && !safety && <Notice tone="destructive">{error}</Notice>}
          </motion.div>
        </AnimatePresence>

        <div className="flex items-center justify-between border-t pt-4">
          <Button
            type="button"
            variant="ghost"
            disabled={step === 0 || submitting}
            onClick={() => setStep((s) => (s - 1) as Step)}
          >
            <ArrowLeft className="h-4 w-4" />
            Back
          </Button>

          {step < 3 ? (
            <Button
              type="button"
              disabled={!stepValid[step]}
              onClick={() => setStep((s) => (s + 1) as Step)}
            >
              Continue
              <ArrowRight className="h-4 w-4" />
            </Button>
          ) : (
            <Button type="button" disabled={!stepValid[3] || submitting} onClick={handleSubmit}>
              {submitting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Check className="h-4 w-4" />
              )}
              Post to the board
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

function StepIndicator({ step }: { step: Step }) {
  return (
    <ol className="flex items-center gap-1.5" aria-label="Progress">
      {STEPS.map((item, index) => (
        <li key={item.title} className="flex-1">
          <div
            className={cn(
              'h-1 rounded-full transition-colors',
              index <= step ? 'bg-primary' : 'bg-muted'
            )}
            aria-current={index === step ? 'step' : undefined}
          />
        </li>
      ))}
    </ol>
  );
}

function ReviewSummary({
  draft,
  city,
  category,
}: {
  draft: Draft;
  city: { name: string; currency: string };
  category?: { name: string };
}) {
  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 rounded-lg border p-4 text-sm">
      <dt className="text-muted-foreground">Task</dt>
      <dd className="font-medium">{draft.title}</dd>
      <dt className="text-muted-foreground">Category</dt>
      <dd>{category?.name ?? '—'}</dd>
      <dt className="text-muted-foreground">City</dt>
      <dd>{city.name}</dd>
      <dt className="text-muted-foreground">Budget</dt>
      <dd className="font-medium">
        {draft.rewardAmount
          ? formatCurrency(Number(draft.rewardAmount), city.currency)
          : '—'}
      </dd>
      {draft.deadlineAt && (
        <>
          <dt className="text-muted-foreground">Deadline</dt>
          <dd>{new Date(draft.deadlineAt).toLocaleString()}</dd>
        </>
      )}
    </dl>
  );
}

function Notice({
  tone,
  children,
}: {
  tone: 'warning' | 'destructive';
  children: React.ReactNode;
}) {
  return (
    <div
      role="status"
      className={cn(
        'flex gap-2 rounded-md border p-3 text-sm',
        tone === 'destructive'
          ? 'border-destructive/40 bg-destructive/10 text-destructive'
          : 'border-amber-500/40 bg-amber-500/10 text-amber-900 dark:text-amber-200'
      )}
    >
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
      <div>{children}</div>
    </div>
  );
}
