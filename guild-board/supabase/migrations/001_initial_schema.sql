-- ============================================================================
-- Guild Board — initial schema
--   tables, indexes, row level security, triggers, storage buckets
--
-- Design rules enforced here rather than in application code, because the
-- client is assumed hostile and Edge Functions are not the only writer:
--   1. Money never moves on a client write. `transactions` is service-role
--      only; the Stripe webhook is the sole author of escrow state.
--   2. A task's reward and category are frozen once funds are authorized.
--   3. Reviews require a completed task and participation in it.
--   4. Reputation is derived, never set. Clients cannot write `rep_score`.
--   5. High-risk (licensed trade) tasks cannot be published by an unverified
--      requester, and cannot be bid on by an unverified member.
-- ============================================================================

create extension if not exists "uuid-ossp";
create extension if not exists "postgis";
create extension if not exists "pg_trgm";

-- ----------------------------------------------------------------------------
-- Enumerated domains
-- ----------------------------------------------------------------------------
create type user_role      as enum ('requester', 'member', 'admin');
create type task_status    as enum ('open', 'assigned', 'in_escrow', 'completed', 'disputed', 'cancelled');
create type risk_tier      as enum ('low', 'medium', 'high_licensed');
create type bid_status     as enum ('pending', 'accepted', 'rejected');
create type escrow_status  as enum ('pending_hold', 'held', 'released', 'refunded');
create type dispute_status as enum ('open', 'under_review', 'resolved_requester', 'resolved_member');

-- ============================================================================
-- CITIES
-- ============================================================================
create table public.cities (
  id            uuid primary key default uuid_generate_v4(),
  name          text        not null,
  slug          text        not null unique,
  country       text        not null,
  lat           double precision not null check (lat between -90 and 90),
  long          double precision not null check (long between -180 and 180),
  -- Radius, in miles, that defines "this city" for discovery purposes.
  radius_miles  integer     not null default 30 check (radius_miles between 1 and 200),
  timezone      text        not null default 'UTC',
  currency      char(3)     not null default 'USD',
  active_status boolean     not null default true,
  created_at    timestamptz not null default now()
);

create index cities_slug_idx   on public.cities (slug) where active_status;
create index cities_active_idx on public.cities (active_status);

-- ============================================================================
-- CATEGORIES
-- ============================================================================
create table public.categories (
  id                          uuid primary key default uuid_generate_v4(),
  name                        text    not null,
  slug                        text    not null unique,
  description                 text,
  icon                        text,
  -- When true, a bid may only be accepted from a member holding a verified
  -- trade licence. The safety filter escalates these tasks to `high_licensed`.
  is_licensed_trade_required  boolean not null default false,
  -- Baseline risk applied to tasks in this category before keyword scanning.
  default_risk_tier           risk_tier not null default 'low',
  sort_order                  integer not null default 0,
  created_at                  timestamptz not null default now()
);

create index categories_slug_idx on public.categories (slug);

-- ============================================================================
-- USERS  (public profile mirror of auth.users)
-- ============================================================================
create table public.users (
  id                 uuid primary key references auth.users (id) on delete cascade,
  full_name          text,
  avatar_url         text,
  bio                text,
  city_id            uuid references public.cities (id) on delete set null,
  role               user_role   not null default 'requester',
  -- Derived from `reviews` by trigger. Never client-writable (see RLS below).
  rep_score          numeric(3,2) not null default 0.00 check (rep_score between 0 and 5),
  rep_count          integer     not null default 0 check (rep_count >= 0),
  tasks_completed    integer     not null default 0 check (tasks_completed >= 0),
  stripe_account_id  text unique,
  -- Mirrors Stripe `account.updated`: can this member actually receive payouts?
  stripe_payouts_enabled boolean not null default false,
  stripe_charges_enabled boolean not null default false,
  is_id_verified     boolean     not null default false,
  id_verified_at     timestamptz,
  is_background_checked boolean  not null default false,
  -- Verified licences, e.g. {'electrical','plumbing'}. Gates high-risk bidding.
  licensed_trades    text[]      not null default '{}',
  is_suspended       boolean     not null default false,
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now()
);

create index users_city_idx    on public.users (city_id);
create index users_role_idx    on public.users (role);
create index users_stripe_idx  on public.users (stripe_account_id);

-- ============================================================================
-- TASKS
-- ============================================================================
create table public.tasks (
  id             uuid primary key default uuid_generate_v4(),
  requester_id   uuid not null references public.users (id) on delete cascade,
  city_id        uuid not null references public.cities (id) on delete restrict,
  category_id    uuid not null references public.categories (id) on delete restrict,
  assigned_to    uuid references public.users (id) on delete set null,

  title          text not null check (char_length(title) between 8 and 140),
  description    text not null check (char_length(description) between 20 and 5000),
  reward_amount  numeric(10,2) not null check (reward_amount >= 5 and reward_amount <= 25000),
  currency       char(3) not null default 'USD',

  lat            double precision not null check (lat between -90 and 90),
  long           double precision not null check (long between -180 and 180),
  -- Street address is shown only to the assigned member (see the column-level
  -- guard in `tasks_public` below); the board shows a coarse pin only.
  address_line   text,
  geo geography(Point, 4326)
    generated always as (st_setsrid(st_makepoint(long, lat), 4326)::geography) stored,

  status         task_status not null default 'open',
  risk_tier      risk_tier   not null default 'low',
  -- Populated by the prohibited-task filter; non-empty means a human must look.
  flagged_terms  text[]      not null default '{}',
  requires_admin_review boolean not null default false,

  image_urls     text[]      not null default '{}',
  deadline_at    timestamptz,
  -- Consent to the safety disclaimer is a legal artefact: store what and when.
  safety_ack_at  timestamptz,
  safety_ack_version text,

  completed_at   timestamptz,
  -- Set when the requester signs off; the auto-release timer counts from here.
  released_after timestamptz,
  cancelled_at   timestamptz,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now(),

  constraint tasks_assignment_consistent check (
    (status in ('open', 'cancelled') and assigned_to is null)
    or (status in ('assigned', 'in_escrow', 'completed', 'disputed'))
  ),
  constraint tasks_deadline_future check (deadline_at is null or deadline_at > created_at)
);

create index tasks_city_status_idx  on public.tasks (city_id, status, created_at desc);
create index tasks_category_idx     on public.tasks (category_id);
create index tasks_requester_idx    on public.tasks (requester_id);
create index tasks_assigned_idx     on public.tasks (assigned_to) where assigned_to is not null;
create index tasks_reward_idx       on public.tasks (reward_amount desc);
create index tasks_geo_idx          on public.tasks using gist (geo);
create index tasks_open_geo_idx     on public.tasks using gist (geo) where status = 'open';
create index tasks_search_idx       on public.tasks using gin (title gin_trgm_ops);
create index tasks_review_queue_idx on public.tasks (created_at) where requires_admin_review;

-- ============================================================================
-- BIDS
-- ============================================================================
create table public.bids (
  id             uuid primary key default uuid_generate_v4(),
  task_id        uuid not null references public.tasks (id) on delete cascade,
  member_id      uuid not null references public.users (id) on delete cascade,
  amount         numeric(10,2) not null check (amount >= 5 and amount <= 25000),
  proposal_text  text not null check (char_length(proposal_text) between 20 and 2000),
  -- Worker's own estimate, in hours, used for sorting and expectation setting.
  estimated_hours numeric(5,2) check (estimated_hours > 0 and estimated_hours <= 500),
  can_start_at   timestamptz,
  status         bid_status  not null default 'pending',
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now(),

  -- One live bid per member per task; re-bidding means updating the amount.
  constraint bids_one_per_member unique (task_id, member_id)
);

create index bids_task_idx   on public.bids (task_id, status, amount);
create index bids_member_idx on public.bids (member_id, created_at desc);

-- Exactly one accepted bid per task, enforced at the storage layer.
create unique index bids_single_accepted_idx
  on public.bids (task_id) where status = 'accepted';

-- ============================================================================
-- TRANSACTIONS  (escrow ledger — service role writes only)
-- ============================================================================
create table public.transactions (
  id                        uuid primary key default uuid_generate_v4(),
  task_id                   uuid not null references public.tasks (id) on delete restrict,
  bid_id                    uuid references public.bids (id) on delete set null,
  payer_id                  uuid not null references public.users (id) on delete restrict,
  payee_id                  uuid not null references public.users (id) on delete restrict,

  stripe_payment_intent_id  text unique,
  stripe_charge_id          text,
  stripe_transfer_id        text,
  -- Destination Connect account, snapshotted: a member may re-onboard later.
  stripe_destination_account text,

  amount                    numeric(10,2) not null check (amount > 0),
  platform_fee              numeric(10,2) not null default 0 check (platform_fee >= 0),
  -- amount - platform_fee, maintained by trigger; what the member receives.
  payout_amount             numeric(10,2) not null default 0 check (payout_amount >= 0),
  currency                  char(3) not null default 'USD',

  escrow_status             escrow_status not null default 'pending_hold',
  authorized_at             timestamptz,
  held_at                   timestamptz,
  released_at               timestamptz,
  refunded_at               timestamptz,
  -- 'manual_signoff' | 'auto_release_72h' | 'dispute_resolution' | 'admin'
  release_reason            text,
  failure_code              text,
  created_at                timestamptz not null default now(),
  updated_at                timestamptz not null default now(),

  constraint transactions_fee_within_amount check (platform_fee <= amount)
);

-- One live escrow per task. A refunded attempt may be superseded by a new one.
create unique index transactions_active_per_task_idx
  on public.transactions (task_id)
  where escrow_status in ('pending_hold', 'held');

create index transactions_task_idx    on public.transactions (task_id);
create index transactions_payee_idx   on public.transactions (payee_id, escrow_status);
create index transactions_payer_idx   on public.transactions (payer_id, escrow_status);
create index transactions_intent_idx  on public.transactions (stripe_payment_intent_id);

-- ============================================================================
-- DISPUTES
-- ============================================================================
create table public.disputes (
  id                uuid primary key default uuid_generate_v4(),
  task_id           uuid not null references public.tasks (id) on delete cascade,
  raised_by         uuid not null references public.users (id) on delete cascade,
  reason            text not null check (char_length(reason) between 20 and 3000),
  evidence_urls     text[] not null default '{}',
  resolution_notes  text,
  resolved_by       uuid references public.users (id) on delete set null,
  status            dispute_status not null default 'open',
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now(),
  resolved_at       timestamptz
);

-- A task can only be under dispute once at a time.
create unique index disputes_one_open_per_task_idx
  on public.disputes (task_id) where status in ('open', 'under_review');

create index disputes_status_idx on public.disputes (status, created_at);
create index disputes_task_idx   on public.disputes (task_id);

-- ============================================================================
-- REVIEWS
-- ============================================================================
create table public.reviews (
  id           uuid primary key default uuid_generate_v4(),
  task_id      uuid not null references public.tasks (id) on delete cascade,
  reviewer_id  uuid not null references public.users (id) on delete cascade,
  reviewee_id  uuid not null references public.users (id) on delete cascade,
  rating       smallint not null check (rating between 1 and 5),
  comment      text check (char_length(comment) <= 2000),
  created_at   timestamptz not null default now(),

  constraint reviews_no_self check (reviewer_id <> reviewee_id),
  constraint reviews_one_per_side unique (task_id, reviewer_id)
);

create index reviews_reviewee_idx on public.reviews (reviewee_id, created_at desc);
create index reviews_task_idx     on public.reviews (task_id);

-- ============================================================================
-- MESSAGES  (realtime chat, scoped to a single task)
-- ============================================================================
create table public.messages (
  id          uuid primary key default uuid_generate_v4(),
  task_id     uuid not null references public.tasks (id) on delete cascade,
  sender_id   uuid not null references public.users (id) on delete cascade,
  body        text check (char_length(body) <= 4000),
  attachment_urls text[] not null default '{}',
  -- Photo proof of completion is a message with this flag; the sign-off UI
  -- surfaces these separately from ordinary chat.
  is_proof    boolean not null default false,
  read_at     timestamptz,
  created_at  timestamptz not null default now(),

  constraint messages_not_empty check (
    coalesce(char_length(trim(body)), 0) > 0 or array_length(attachment_urls, 1) > 0
  )
);

create index messages_task_idx on public.messages (task_id, created_at desc);

-- ============================================================================
-- HELPER FUNCTIONS
--   SECURITY DEFINER so policies can consult other tables without recursing
--   into those tables' own RLS. search_path is pinned against hijacking.
-- ============================================================================

create or replace function public.is_admin(uid uuid default auth.uid())
returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.users u where u.id = uid and u.role = 'admin');
$$;

-- True when the statement is running with platform privileges rather than on
-- behalf of an end user. PostgREST issues `set local role service_role` for
-- service-key requests, so the effective role is the reliable signal.
--
-- It reads the `role` GUC rather than `current_user` on purpose: inside a
-- SECURITY DEFINER function `current_user` is the function's owner, which
-- would make this return true for every caller and silently disable the
-- guards that depend on it. The `role` setting is unaffected by the definer
-- switch. `current_user` is only the fallback for direct connections (psql,
-- migrations) where no SET ROLE has happened.
create or replace function public.is_platform_actor()
returns boolean
language sql stable as $$
  select coalesce(nullif(current_setting('role', true), 'none'), current_user)
           in ('service_role', 'supabase_admin', 'postgres')
      or coalesce(auth.role(), '') = 'service_role';
$$;

-- True when `uid` is the requester or the assigned member on `tid`.
create or replace function public.is_task_participant(tid uuid, uid uuid default auth.uid())
returns boolean
language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from public.tasks t
    where t.id = tid and (t.requester_id = uid or t.assigned_to = uid)
  );
$$;

create or replace function public.is_task_owner(tid uuid, uid uuid default auth.uid())
returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.tasks t where t.id = tid and t.requester_id = uid);
$$;

-- Radius search for the Guild Board. Distance in miles, ordered nearest-first.
-- SECURITY INVOKER: the caller's RLS still applies to the underlying rows.
create or replace function public.tasks_within_radius(
  p_city_slug   text,
  p_lat         double precision,
  p_long        double precision,
  p_radius_miles double precision default 25,
  p_category_ids uuid[] default null,
  p_min_reward  numeric default null,
  p_max_reward  numeric default null,
  p_limit       integer default 50,
  p_offset      integer default 0
)
returns table (
  id uuid, title text, description text, reward_amount numeric,
  lat double precision, long double precision, status task_status,
  risk_tier risk_tier, category_id uuid, requester_id uuid,
  image_urls text[], deadline_at timestamptz, created_at timestamptz,
  distance_miles double precision, bid_count bigint
)
language sql stable set search_path = public as $$
  select
    t.id, t.title, t.description, t.reward_amount,
    t.lat, t.long, t.status, t.risk_tier, t.category_id, t.requester_id,
    t.image_urls, t.deadline_at, t.created_at,
    st_distance(t.geo, st_setsrid(st_makepoint(p_long, p_lat), 4326)::geography) / 1609.344
      as distance_miles,
    (select count(*) from public.bids b where b.task_id = t.id and b.status = 'pending')
      as bid_count
  from public.tasks t
  join public.cities c on c.id = t.city_id
  where c.slug = p_city_slug
    and c.active_status
    and t.status = 'open'
    and not t.requires_admin_review
    and st_dwithin(
      t.geo,
      st_setsrid(st_makepoint(p_long, p_lat), 4326)::geography,
      p_radius_miles * 1609.344
    )
    and (p_category_ids is null or t.category_id = any (p_category_ids))
    and (p_min_reward is null or t.reward_amount >= p_min_reward)
    and (p_max_reward is null or t.reward_amount <= p_max_reward)
  order by distance_miles asc
  limit least(coalesce(p_limit, 50), 200) offset coalesce(p_offset, 0);
$$;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- --- updated_at ------------------------------------------------------------
create or replace function public.touch_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

create trigger users_touch        before update on public.users        for each row execute function public.touch_updated_at();
create trigger tasks_touch        before update on public.tasks        for each row execute function public.touch_updated_at();
create trigger bids_touch         before update on public.bids         for each row execute function public.touch_updated_at();
create trigger transactions_touch before update on public.transactions for each row execute function public.touch_updated_at();
create trigger disputes_touch     before update on public.disputes     for each row execute function public.touch_updated_at();

-- --- Provision a profile for every new auth user ---------------------------
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.users (id, full_name, avatar_url)
  values (
    new.id,
    coalesce(new.raw_user_meta_data ->> 'full_name', new.raw_user_meta_data ->> 'name'),
    new.raw_user_meta_data ->> 'avatar_url'
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- --- Freeze the commercial terms of a task once money is committed ---------
create or replace function public.guard_task_mutation()
returns trigger language plpgsql as $$
begin
  if old.status in ('in_escrow', 'completed', 'disputed')
     and (new.reward_amount is distinct from old.reward_amount
          or new.category_id  is distinct from old.category_id
          or new.city_id      is distinct from old.city_id) then
    raise exception 'Task % is under escrow; reward, category and city are frozen', old.id
      using errcode = 'check_violation';
  end if;

  -- A cancelled or completed task is terminal for clients; only the service
  -- role (webhooks, admin tooling) may move it out of those states.
  if old.status in ('completed', 'cancelled')
     and new.status is distinct from old.status
     and not public.is_platform_actor()
     and not public.is_admin() then
    raise exception 'Task % is in a terminal state (%)', old.id, old.status
      using errcode = 'check_violation';
  end if;

  if new.status = 'cancelled' and old.status is distinct from 'cancelled' then
    new.cancelled_at := now();
  end if;

  return new;
end;
$$;

create trigger tasks_guard_mutation
  before update on public.tasks
  for each row execute function public.guard_task_mutation();

-- --- Licensed-trade gate ---------------------------------------------------
-- A high-risk task may only be bid on by a member holding the matching
-- verified licence. Enforced here so no API path can skip it.
create or replace function public.guard_bid_eligibility()
returns trigger language plpgsql security definer set search_path = public as $$
declare
  v_task   record;
  v_member record;
begin
  select t.status, t.risk_tier, t.requester_id, c.slug as category_slug,
         c.is_licensed_trade_required
    into v_task
    from public.tasks t
    join public.categories c on c.id = t.category_id
   where t.id = new.task_id;

  if v_task is null then
    raise exception 'Task % not found', new.task_id using errcode = 'foreign_key_violation';
  end if;

  if v_task.status <> 'open' then
    raise exception 'Task % is no longer accepting bids', new.task_id
      using errcode = 'check_violation';
  end if;

  if v_task.requester_id = new.member_id then
    raise exception 'A requester cannot bid on their own task'
      using errcode = 'check_violation';
  end if;

  select is_id_verified, licensed_trades, is_suspended, stripe_payouts_enabled
    into v_member from public.users where id = new.member_id;

  if v_member.is_suspended then
    raise exception 'Account is suspended' using errcode = 'check_violation';
  end if;

  if (v_task.risk_tier = 'high_licensed' or v_task.is_licensed_trade_required) then
    if not v_member.is_id_verified then
      raise exception 'Identity verification is required to bid on licensed-trade tasks'
        using errcode = 'check_violation';
    end if;
    if not (v_task.category_slug = any (v_member.licensed_trades)) then
      raise exception 'A verified % licence is required to bid on this task', v_task.category_slug
        using errcode = 'check_violation';
    end if;
  end if;

  return new;
end;
$$;

create trigger bids_guard_eligibility
  before insert on public.bids
  for each row execute function public.guard_bid_eligibility();

-- --- Accepting a bid assigns the task and closes the others ----------------
create or replace function public.handle_bid_accepted()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if new.status = 'accepted' and old.status is distinct from 'accepted' then
    update public.tasks
       set status = 'assigned', assigned_to = new.member_id
     where id = new.task_id and status = 'open';

    if not found then
      raise exception 'Task % is not open; bid cannot be accepted', new.task_id
        using errcode = 'check_violation';
    end if;

    update public.bids
       set status = 'rejected'
     where task_id = new.task_id and id <> new.id and status = 'pending';
  end if;
  return new;
end;
$$;

create trigger bids_on_accept
  after update on public.bids
  for each row execute function public.handle_bid_accepted();

-- --- Escrow state drives task state ---------------------------------------
create or replace function public.sync_task_from_escrow()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  new.payout_amount := new.amount - new.platform_fee;

  if new.escrow_status is distinct from old.escrow_status then
    if new.escrow_status = 'held' then
      new.held_at := coalesce(new.held_at, now());
      update public.tasks set status = 'in_escrow'
       where id = new.task_id and status in ('assigned', 'open');

    elsif new.escrow_status = 'released' then
      new.released_at := coalesce(new.released_at, now());
      update public.tasks
         set status = 'completed', completed_at = coalesce(completed_at, now())
       where id = new.task_id and status <> 'completed';

    elsif new.escrow_status = 'refunded' then
      new.refunded_at := coalesce(new.refunded_at, now());
    end if;
  end if;

  return new;
end;
$$;

create trigger transactions_sync_task
  before update on public.transactions
  for each row execute function public.sync_task_from_escrow();

create or replace function public.set_payout_on_insert()
returns trigger language plpgsql as $$
begin
  new.payout_amount := new.amount - new.platform_fee;
  return new;
end;
$$;

create trigger transactions_set_payout
  before insert on public.transactions
  for each row execute function public.set_payout_on_insert();

-- --- Raising a dispute freezes the release timer ---------------------------
create or replace function public.handle_dispute_opened()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if not public.is_task_participant(new.task_id, new.raised_by) then
    raise exception 'Only the requester or the assigned member may raise a dispute'
      using errcode = 'insufficient_privilege';
  end if;

  update public.tasks
     set status = 'disputed', released_after = null
   where id = new.task_id and status in ('assigned', 'in_escrow', 'completed');

  return new;
end;
$$;

create trigger disputes_on_open
  after insert on public.disputes
  for each row execute function public.handle_dispute_opened();

-- --- Reviews: only real counterparties, only completed work ----------------
create or replace function public.guard_review()
returns trigger language plpgsql security definer set search_path = public as $$
declare v_task record;
begin
  select requester_id, assigned_to, status into v_task
    from public.tasks where id = new.task_id;

  if v_task.status <> 'completed' then
    raise exception 'Reviews are only allowed on completed tasks'
      using errcode = 'check_violation';
  end if;

  if not (new.reviewer_id in (v_task.requester_id, v_task.assigned_to)
          and new.reviewee_id in (v_task.requester_id, v_task.assigned_to)) then
    raise exception 'Reviewer and reviewee must both be parties to the task'
      using errcode = 'insufficient_privilege';
  end if;

  return new;
end;
$$;

create trigger reviews_guard
  before insert on public.reviews
  for each row execute function public.guard_review();

-- --- Reputation is derived, recomputed on every review ---------------------
create or replace function public.recompute_rep_score()
returns trigger language plpgsql security definer set search_path = public as $$
declare v_target uuid := coalesce(new.reviewee_id, old.reviewee_id);
begin
  update public.users u
     set rep_score = coalesce(r.avg_rating, 0),
         rep_count = coalesce(r.n, 0)
    from (
      select round(avg(rating)::numeric, 2) as avg_rating, count(*) as n
        from public.reviews where reviewee_id = v_target
    ) r
   where u.id = v_target;
  return null;
end;
$$;

create trigger reviews_recompute_rep
  after insert or update or delete on public.reviews
  for each row execute function public.recompute_rep_score();

-- --- Chat is scoped to an assignment, full stop ----------------------------
create or replace function public.guard_message()
returns trigger language plpgsql security definer set search_path = public as $$
declare v_task record;
begin
  select status, requester_id, assigned_to into v_task
    from public.tasks where id = new.task_id;

  if v_task.assigned_to is null then
    raise exception 'Chat opens once a bid is accepted' using errcode = 'check_violation';
  end if;

  if new.sender_id not in (v_task.requester_id, v_task.assigned_to) then
    raise exception 'Only the requester and the assigned member may post here'
      using errcode = 'insufficient_privilege';
  end if;

  return new;
end;
$$;

create trigger messages_guard
  before insert on public.messages
  for each row execute function public.guard_message();

-- ============================================================================
-- ROW LEVEL SECURITY
--   Every table is deny-by-default. The service-role key bypasses RLS
--   entirely and is the only writer for `transactions`.
-- ============================================================================

alter table public.cities       enable row level security;
alter table public.categories   enable row level security;
alter table public.users        enable row level security;
alter table public.tasks        enable row level security;
alter table public.bids         enable row level security;
alter table public.transactions enable row level security;
alter table public.disputes     enable row level security;
alter table public.reviews      enable row level security;
alter table public.messages     enable row level security;

-- --- cities / categories: public read, admin write -------------------------
create policy "cities are public" on public.cities
  for select using (true);
create policy "admins manage cities" on public.cities
  for all using (public.is_admin()) with check (public.is_admin());

create policy "categories are public" on public.categories
  for select using (true);
create policy "admins manage categories" on public.categories
  for all using (public.is_admin()) with check (public.is_admin());

-- --- users -----------------------------------------------------------------
-- Profiles are public (the board shows names, avatars, rep). Sensitive columns
-- are protected by the trigger below rather than by hiding the row.
create policy "profiles are readable" on public.users
  for select using (true);

create policy "users update own profile" on public.users
  for update using (auth.uid() = id) with check (auth.uid() = id);

create policy "admins manage users" on public.users
  for all using (public.is_admin()) with check (public.is_admin());

-- Trust columns are server-owned. A user updating their own row may not grant
-- themselves verification, reputation, payout capability or a role.
-- Not SECURITY DEFINER: this trigger must see the *caller's* role, not the
-- owner's. `public.is_admin()` is definer-scoped where the elevated read is
-- actually needed.
create or replace function public.guard_user_privileges()
returns trigger language plpgsql set search_path = public as $$
begin
  if public.is_platform_actor() or public.is_admin() then
    return new;
  end if;

  if new.role                  is distinct from old.role
     or new.rep_score          is distinct from old.rep_score
     or new.rep_count          is distinct from old.rep_count
     or new.tasks_completed    is distinct from old.tasks_completed
     or new.is_id_verified     is distinct from old.is_id_verified
     or new.is_background_checked is distinct from old.is_background_checked
     or new.licensed_trades    is distinct from old.licensed_trades
     or new.stripe_account_id  is distinct from old.stripe_account_id
     or new.stripe_payouts_enabled is distinct from old.stripe_payouts_enabled
     or new.stripe_charges_enabled is distinct from old.stripe_charges_enabled
     or new.is_suspended       is distinct from old.is_suspended then
    raise exception 'Trust and payout fields are managed by the platform'
      using errcode = 'insufficient_privilege';
  end if;
  return new;
end;
$$;

create trigger users_guard_privileges
  before update on public.users
  for each row execute function public.guard_user_privileges();

-- --- tasks -----------------------------------------------------------------
-- Open tasks are the public board. Non-open tasks are visible only to the
-- parties involved, so a cancelled or disputed job leaves the board entirely.
create policy "open tasks are browsable" on public.tasks
  for select using (
    (status = 'open' and not requires_admin_review)
    or requester_id = auth.uid()
    or assigned_to = auth.uid()
    or exists (select 1 from public.bids b where b.task_id = id and b.member_id = auth.uid())
    or public.is_admin()
  );

create policy "requesters create own tasks" on public.tasks
  for insert with check (
    requester_id = auth.uid()
    and status = 'open'
    and assigned_to is null
    and safety_ack_at is not null
    and not exists (select 1 from public.users u where u.id = auth.uid() and u.is_suspended)
  );

create policy "requesters update own tasks" on public.tasks
  for update using (requester_id = auth.uid())
  with check (requester_id = auth.uid());

-- The assigned member may only move an in-escrow task to 'completed'
-- (marking work done); everything else stays with the requester.
create policy "assigned member marks work done" on public.tasks
  for update using (assigned_to = auth.uid() and status = 'in_escrow')
  with check (assigned_to = auth.uid() and status in ('in_escrow', 'completed'));

create policy "requesters delete only untouched tasks" on public.tasks
  for delete using (
    requester_id = auth.uid()
    and status = 'open'
    and not exists (select 1 from public.bids b where b.task_id = id)
  );

create policy "admins manage tasks" on public.tasks
  for all using (public.is_admin()) with check (public.is_admin());

-- --- bids ------------------------------------------------------------------
-- A member sees their own bids; the requester sees every bid on their task.
-- Bidders cannot see each other's numbers — this is a sealed-bid board.
create policy "bids visible to bidder and task owner" on public.bids
  for select using (
    member_id = auth.uid()
    or public.is_task_owner(task_id)
    or public.is_admin()
  );

create policy "members create own bids" on public.bids
  for insert with check (
    member_id = auth.uid()
    and status = 'pending'
    and not exists (select 1 from public.users u where u.id = auth.uid() and u.is_suspended)
  );

-- A bidder may revise or withdraw while still pending.
create policy "members update own pending bids" on public.bids
  for update using (member_id = auth.uid() and status = 'pending')
  with check (member_id = auth.uid() and status in ('pending', 'rejected'));

-- The task owner is the only one who can accept or reject.
create policy "task owner decides bids" on public.bids
  for update using (public.is_task_owner(task_id))
  with check (public.is_task_owner(task_id));

create policy "members withdraw own pending bids" on public.bids
  for delete using (member_id = auth.uid() and status = 'pending');

create policy "admins manage bids" on public.bids
  for all using (public.is_admin()) with check (public.is_admin());

-- --- transactions ----------------------------------------------------------
-- Read-only to the two parties. No client INSERT/UPDATE/DELETE policy exists,
-- so only the service role (Stripe webhook) can write the ledger.
create policy "parties read own transactions" on public.transactions
  for select using (
    payer_id = auth.uid() or payee_id = auth.uid() or public.is_admin()
  );

create policy "admins manage transactions" on public.transactions
  for all using (public.is_admin()) with check (public.is_admin());

-- --- disputes --------------------------------------------------------------
create policy "parties read own disputes" on public.disputes
  for select using (public.is_task_participant(task_id) or public.is_admin());

create policy "parties raise disputes" on public.disputes
  for insert with check (
    raised_by = auth.uid()
    and public.is_task_participant(task_id)
    and status = 'open'
  );

-- The raiser may add evidence while the case is still open; resolution notes
-- and status transitions belong to admins.
create policy "raiser appends evidence" on public.disputes
  for update using (raised_by = auth.uid() and status = 'open')
  with check (raised_by = auth.uid() and status = 'open' and resolution_notes is null);

create policy "admins resolve disputes" on public.disputes
  for all using (public.is_admin()) with check (public.is_admin());

-- --- reviews ---------------------------------------------------------------
create policy "reviews are public" on public.reviews
  for select using (true);

create policy "participants write reviews" on public.reviews
  for insert with check (
    reviewer_id = auth.uid() and public.is_task_participant(task_id)
  );

create policy "admins manage reviews" on public.reviews
  for all using (public.is_admin()) with check (public.is_admin());

-- --- messages --------------------------------------------------------------
-- The whole point of the chat rule: membership in the conversation is derived
-- from the task assignment, so a subscriber cannot listen to another job.
create policy "participants read task chat" on public.messages
  for select using (public.is_task_participant(task_id) or public.is_admin());

create policy "participants send messages" on public.messages
  for insert with check (
    sender_id = auth.uid() and public.is_task_participant(task_id)
  );

create policy "senders edit own messages" on public.messages
  for update using (sender_id = auth.uid()) with check (sender_id = auth.uid());

create policy "admins read all messages" on public.messages
  for all using (public.is_admin()) with check (public.is_admin());

-- ============================================================================
-- REALTIME
-- ============================================================================
alter publication supabase_realtime add table public.messages;
alter publication supabase_realtime add table public.bids;
alter publication supabase_realtime add table public.tasks;

-- Realtime respects RLS only when the table publishes full row data.
alter table public.messages replica identity full;
alter table public.bids     replica identity full;

-- ============================================================================
-- STORAGE BUCKETS
-- ============================================================================
-- `storage.objects` lives outside the `public` schema, so these policies
-- survive a `drop schema public cascade`. The drop guards keep the migration
-- re-runnable against a database that has been partially reset by hand.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values
  ('task-photos',       'task-photos',       true,  10485760, array['image/jpeg','image/png','image/webp','image/heic']),
  ('completion-proof',  'completion-proof',  false, 10485760, array['image/jpeg','image/png','image/webp','image/heic']),
  ('dispute-evidence',  'dispute-evidence',  false, 26214400, array['image/jpeg','image/png','image/webp','application/pdf']),
  ('identity-docs',     'identity-docs',     false, 26214400, array['image/jpeg','image/png','application/pdf'])
on conflict (id) do nothing;

-- Task photos: world-readable, owner-writable, foldered by user id.
drop policy if exists "task photos are public" on storage.objects;
create policy "task photos are public" on storage.objects
  for select using (bucket_id = 'task-photos');

drop policy if exists "users upload own task photos" on storage.objects;
create policy "users upload own task photos" on storage.objects
  for insert with check (
    bucket_id = 'task-photos' and (storage.foldername(name))[1] = auth.uid()::text
  );

drop policy if exists "users delete own task photos" on storage.objects;
create policy "users delete own task photos" on storage.objects
  for delete using (
    bucket_id = 'task-photos' and (storage.foldername(name))[1] = auth.uid()::text
  );

-- Completion proof: private, foldered by task id, readable by the two parties.
drop policy if exists "parties read completion proof" on storage.objects;
create policy "parties read completion proof" on storage.objects
  for select using (
    bucket_id = 'completion-proof'
    and public.is_task_participant(((storage.foldername(name))[1])::uuid)
  );

drop policy if exists "parties upload completion proof" on storage.objects;
create policy "parties upload completion proof" on storage.objects
  for insert with check (
    bucket_id = 'completion-proof'
    and public.is_task_participant(((storage.foldername(name))[1])::uuid)
  );

-- Dispute evidence: private, readable by the parties and admins.
drop policy if exists "parties read dispute evidence" on storage.objects;
create policy "parties read dispute evidence" on storage.objects
  for select using (
    bucket_id = 'dispute-evidence'
    and (public.is_task_participant(((storage.foldername(name))[1])::uuid) or public.is_admin())
  );

drop policy if exists "parties upload dispute evidence" on storage.objects;
create policy "parties upload dispute evidence" on storage.objects
  for insert with check (
    bucket_id = 'dispute-evidence'
    and public.is_task_participant(((storage.foldername(name))[1])::uuid)
  );

-- Identity documents: the uploader can write, only admins can read back.
drop policy if exists "users upload own identity docs" on storage.objects;
create policy "users upload own identity docs" on storage.objects
  for insert with check (
    bucket_id = 'identity-docs' and (storage.foldername(name))[1] = auth.uid()::text
  );

drop policy if exists "admins read identity docs" on storage.objects;
create policy "admins read identity docs" on storage.objects
  for select using (bucket_id = 'identity-docs' and public.is_admin());

-- ============================================================================
-- GRANTS
-- ============================================================================
grant usage on schema public to anon, authenticated;
grant select on public.cities, public.categories to anon, authenticated;
grant select, insert, update, delete on public.tasks, public.bids, public.messages, public.disputes, public.reviews to authenticated;
grant select on public.users, public.tasks, public.reviews to anon;
grant select, update on public.users to authenticated;
grant select on public.transactions to authenticated;
grant execute on function public.is_platform_actor() to anon, authenticated;
grant execute on function public.tasks_within_radius(text, double precision, double precision, double precision, uuid[], numeric, numeric, integer, integer) to anon, authenticated;
