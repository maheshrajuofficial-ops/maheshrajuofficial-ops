-- ============================================================================
-- Guild Board — escrow automation
--   Sign-off RPC, the 72-hour auto-release queue, and the admin dispute
--   resolution entry point. Kept apart from 001 so the money-movement policy
--   can be reviewed (and changed) on its own.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Requester signs off on completed work.
--
-- Sign-off does not move money by itself. It starts the clock: the API layer
-- captures the PaymentIntent immediately on explicit sign-off, and the
-- scheduled job captures anything still sitting here after the window.
-- ----------------------------------------------------------------------------
create or replace function public.sign_off_task(
  p_task_id uuid,
  p_hold_hours integer default 0
)
returns public.tasks
language plpgsql security definer set search_path = public as $$
declare v_task public.tasks;
begin
  select * into v_task from public.tasks where id = p_task_id for update;

  if v_task is null then
    raise exception 'Task % not found', p_task_id using errcode = 'no_data_found';
  end if;

  if v_task.requester_id <> auth.uid() and not public.is_admin() then
    raise exception 'Only the requester may sign off on this task'
      using errcode = 'insufficient_privilege';
  end if;

  if v_task.status not in ('in_escrow', 'completed') then
    raise exception 'Task % is % and cannot be signed off', p_task_id, v_task.status
      using errcode = 'check_violation';
  end if;

  update public.tasks
     set completed_at   = coalesce(completed_at, now()),
         released_after = now() + make_interval(hours => greatest(p_hold_hours, 0))
   where id = p_task_id
  returning * into v_task;

  return v_task;
end;
$$;

-- ----------------------------------------------------------------------------
-- Member marks the work finished. Starts the dispute-free countdown; the
-- requester can still sign off early, or dispute, at any point inside it.
-- ----------------------------------------------------------------------------
create or replace function public.mark_task_delivered(
  p_task_id uuid,
  p_auto_release_hours integer default 72
)
returns public.tasks
language plpgsql security definer set search_path = public as $$
declare v_task public.tasks;
begin
  select * into v_task from public.tasks where id = p_task_id for update;

  if v_task is null then
    raise exception 'Task % not found', p_task_id using errcode = 'no_data_found';
  end if;

  if v_task.assigned_to is distinct from auth.uid() then
    raise exception 'Only the assigned member may mark this task delivered'
      using errcode = 'insufficient_privilege';
  end if;

  if v_task.status <> 'in_escrow' then
    raise exception 'Funds must be held in escrow before delivery can be claimed'
      using errcode = 'check_violation';
  end if;

  update public.tasks
     set completed_at   = coalesce(completed_at, now()),
         released_after = now() + make_interval(hours => greatest(p_auto_release_hours, 1))
   where id = p_task_id
  returning * into v_task;

  return v_task;
end;
$$;

-- ----------------------------------------------------------------------------
-- The auto-release queue.
--
-- A row appears here only when: funds are actually held, the countdown has
-- elapsed, and no dispute is open. The Edge Function reads this with the
-- service role and captures each PaymentIntent through the Stripe API.
-- ----------------------------------------------------------------------------
create or replace view public.escrow_auto_release_queue
with (security_invoker = true) as
  select
    tr.id                       as transaction_id,
    tr.task_id,
    tr.stripe_payment_intent_id,
    tr.amount,
    tr.platform_fee,
    tr.payout_amount,
    tr.currency,
    tr.stripe_destination_account,
    t.released_after,
    extract(epoch from (now() - t.released_after)) / 3600 as hours_overdue
  from public.transactions tr
  join public.tasks t on t.id = tr.task_id
  where tr.escrow_status = 'held'
    and t.released_after is not null
    and t.released_after <= now()
    and t.status <> 'disputed'
    and not exists (
      select 1 from public.disputes d
      where d.task_id = t.id and d.status in ('open', 'under_review')
    );

-- ----------------------------------------------------------------------------
-- Admin dispute resolution. Records the decision and hands the payout
-- instruction back to the caller; the Stripe capture/refund happens in the
-- API layer, which then writes the final escrow status via the webhook.
-- ----------------------------------------------------------------------------
create or replace function public.resolve_dispute(
  p_dispute_id uuid,
  p_status     dispute_status,
  p_notes      text
)
returns table (dispute_id uuid, task_id uuid, payment_intent_id text, action text)
language plpgsql security definer set search_path = public as $$
declare
  v_dispute public.disputes;
  v_intent  text;
begin
  if not public.is_admin() then
    raise exception 'Only admins may resolve disputes' using errcode = 'insufficient_privilege';
  end if;

  if p_status not in ('resolved_requester', 'resolved_member', 'under_review') then
    raise exception 'Invalid resolution status %', p_status using errcode = 'check_violation';
  end if;

  update public.disputes
     set status = p_status,
         resolution_notes = p_notes,
         resolved_by = auth.uid(),
         resolved_at = case when p_status = 'under_review' then null else now() end
   where id = p_dispute_id
  returning * into v_dispute;

  if v_dispute is null then
    raise exception 'Dispute % not found', p_dispute_id using errcode = 'no_data_found';
  end if;

  select tr.stripe_payment_intent_id into v_intent
    from public.transactions tr
   where tr.task_id = v_dispute.task_id
     and tr.escrow_status in ('pending_hold', 'held')
   limit 1;

  -- 'refund' returns the hold to the requester, 'capture' pays the member.
  return query select
    v_dispute.id,
    v_dispute.task_id,
    v_intent,
    case p_status
      when 'resolved_requester' then 'refund'
      when 'resolved_member'    then 'capture'
      else 'none'
    end;
end;
$$;

-- ----------------------------------------------------------------------------
-- Completed-task counter, maintained alongside reputation.
-- ----------------------------------------------------------------------------
create or replace function public.bump_tasks_completed()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if new.status = 'completed' and old.status is distinct from 'completed'
     and new.assigned_to is not null then
    update public.users set tasks_completed = tasks_completed + 1
     where id = new.assigned_to;
  end if;
  return new;
end;
$$;

create trigger tasks_bump_completed
  after update on public.tasks
  for each row execute function public.bump_tasks_completed();

grant execute on function public.sign_off_task(uuid, integer)       to authenticated;
grant execute on function public.mark_task_delivered(uuid, integer) to authenticated;
grant execute on function public.resolve_dispute(uuid, dispute_status, text) to authenticated;
