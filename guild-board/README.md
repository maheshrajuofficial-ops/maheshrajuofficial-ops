# Guild Board

A localized, multi-city marketplace for custom requests, odd jobs and hyper-niche
tasks — a digital guild board for major cities.

Next.js 14 (App Router) · TypeScript · Tailwind + Shadcn UI · Supabase (Postgres,
RLS, Realtime, Storage) · Stripe Connect escrow · Mapbox GL.

---

## The three things this scaffold actually gets right

Most marketplace scaffolds are CRUD with a payment button bolted on. The parts
worth reviewing here are the ones that decide whether the thing survives contact
with real users:

**1. Money is never in our custody until the work is signed off.** Accepting a
bid creates a `capture_method: 'manual'` PaymentIntent — the requester's card is
*authorised*, not charged. Capture happens on sign-off, or automatically after a
72-hour dispute-free window, and the split to the worker plus our platform fee is
atomic with that capture. There is no window in which we hold funds we owe
someone. See `lib/stripe/escrow.ts`.

**2. The database does not trust the application.** Every business rule that
protects a party is a constraint or trigger, not an `if` in a route handler:
reward is frozen once escrow opens, a bid on a licensed-trade task is rejected
unless the worker holds a verified licence, reputation is derived from reviews
and cannot be written by anyone, and the `transactions` ledger has *no client
write policy at all* — only the Stripe webhook (service role) can author escrow
state. See `supabase/migrations/001_initial_schema.sql`.

**3. The safety filter is tuned against false positives, not for maximum
blocking.** A filter that refuses "help me move a gun cabinet" or "pull the weeds
in the back garden" trains people to write around it, which is strictly worse
than letting it through and catching it in human review. Ambiguous matches go to
`review`; only unambiguous ones `block`. Every rule carries an exceptions list.
See `lib/safety/prohibited-filter.ts` and its test cases.

---

## Verification status

Everything below was run in this repo, not asserted:

| Check | Result |
|---|---|
| `npx tsc --noEmit` | clean |
| `npx next lint` | no warnings or errors |
| `npx next build` | compiles; `/[city]` 258 kB first-load JS |
| Migrations applied to Postgres 16 + PostGIS | clean, twice from scratch |
| Trigger / escrow state-machine tests | 18/18 |
| RLS policy tests (as `authenticated`) | 10/10 |
| Safety filter cases | 22/22 |

Two real bugs were found and fixed by those tests, both worth knowing about:

- `guard_user_privileges` was `SECURITY DEFINER`, which makes `current_user` the
  function's *owner* — so the "is this the platform or an end user?" check
  returned true for everyone and the guard was silently inert. Any user could
  have granted themselves `is_id_verified` and a 5.0 rep score. The role check
  now reads the `role` GUC, which the definer switch does not affect.
- The filter's de-obfuscation step collapsed a preceding one-letter word into the
  token, so `"a c-o-c-a-i-n-e courier"` normalised to `acocaine` and slipped past
  every `\b`-anchored rule.

---

## Getting started

```bash
npm install
cp .env.example .env.local     # fill in Supabase, Stripe and Mapbox keys
npm run dev
```

The app runs without a Mapbox token — the map view degrades to a notice and the
location picker falls back to lat/long fields, so the task wizard stays
completable in a bare dev environment.

### Database

```bash
supabase start
supabase db reset              # applies migrations + seed.sql
npm run db:types               # regenerate types/supabase.ts from the live schema
```

`supabase/seed.sql` ships ten launch cities and a fifteen-category taxonomy with
the licensed trades (electrical, plumbing, HVAC, roofing) already flagged.

### Stripe

```bash
npm run stripe:listen          # forwards webhooks to localhost:3000
```

Three events carry the system: `payment_intent.amount_capturable_updated` (funds
are now held → task moves to `in_escrow`, countdown starts),
`payment_intent.succeeded` (captured → task `completed`), and `account.updated`
(a worker whose payouts capability lapses stops being biddable *before* a
requester's money is committed to them).

### Escrow auto-release

`supabase/functions/auto-release-escrow/` is a scheduler, not payment logic — it
calls the single release path in the app so that "capture funds" exists in one
place and is audited in one place. Deploy it and schedule it hourly with
`pg_cron`; the header comment has the exact invocation.

### Tests

```bash
npm run test:safety            # 22 filter cases, no external services needed
```

Schema and RLS tests need a local Postgres with PostGIS; see the header of
`supabase/tests/00_local_stub.sql` for the five-line run sequence.

---

## Layout

```
app/
  [city]/page.tsx                    Guild Board — PostGIS radius search
  [city]/tasks/[taskId]/page.tsx     detail, bids, chat, escrow, reviews
  api/tasks/                         create, gated by the safety filter
  api/bids/[bidId]/accept/           accept → opens escrow (the critical path)
  api/stripe/connect/                Express onboarding
  api/stripe/escrow/{authorize,release}/
  api/stripe/webhook/                sole author of escrow state
components/
  board/       guild-board, filters, task-card, task-map
  tasks/       create-task-modal (4-step wizard), location-picker, escrow-panel
  bids/        bid-form (counter-pricing), bid-list (sealed bids)
  chat/        task-chat (Realtime, scoped by RLS not by channel name)
  trust/       verification badges, review form
lib/
  safety/      prohibited-task filter
  stripe/      escrow primitives, fee split, Connect
  supabase/    browser / server / admin / middleware clients
  geo/         haversine, radius bounds, pin coarsening
  verification/ Persona + Checkr integration stubs
supabase/
  migrations/  schema, indexes, RLS, triggers
  tests/       schema-logic and RLS suites
  functions/   auto-release-escrow (Deno)
```

---

## Decisions taken, and what would change them

**Stripe Express, not Custom.** Stripe hosts KYC and owns the identity and tax
data, keeping that compliance surface — and its PII — off our infrastructure.
Revisit only if onboarding conversion demands a white-labelled flow, and budget
for the liability that shifts to us when it does.

**City lives in the URL, not React state.** `/[city]/...` means a filtered board
is linkable and server-renderable with no client fetch. Every filter is a search
param for the same reason; the radius slider commits on release so the cost is
one navigation per adjustment, not one per pixel.

**Public pins are deliberately imprecise.** An open task is visible to strangers,
so the board plots a seeded offset from the real point (`coarsenLocation`), not
the doorstep. The seed is the task id so the pin cannot be averaged back to the
true location across reloads. The precise address is rendered only for the
assigned member, after the bid is accepted.

**Sealed bids.** A bidder sees only their own bid; the requester sees all of
them. This is an RLS policy, not a UI choice.

---

## Known gaps before this takes real money

Named plainly, because a scaffold that pretends to be complete is worse than one
that isn't:

- **Auth screens are not built.** `/login` and `/signup` are referenced but not
  implemented; wire up Supabase Auth UI or your own forms.
- **Card authorisations expire after ~7 days.** The 72-hour window fits inside
  that, but a disputed task can outlive it. Long disputes need a re-authorisation
  path.
- **Background checks are US-centric and FCRA-bound.** `lib/verification/checkr.ts`
  refuses to order a check without a recorded consent timestamp — that guard is
  load-bearing, not decorative. Adverse-action notices and state-level rules
  (California, NYC, Illinois) are not implemented.
- **Trade-licence verification has no single registry.** Licences are per-state,
  per-council. Expect a per-jurisdiction connector or manual admin review against
  an uploaded certificate.
- **No admin console.** The review queue (`tasks.requires_admin_review`) and
  dispute resolution (`resolve_dispute`) exist in the database with no UI on top.
- **Worker classification is jurisdictional.** The footer says workers are
  independent, not employees. Whether that holds depends on the market and how
  much control the platform exerts — get local advice per city before launch.
