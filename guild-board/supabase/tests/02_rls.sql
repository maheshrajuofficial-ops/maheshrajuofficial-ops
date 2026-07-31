-- ============================================================================
-- Row Level Security tests. Run with --single-transaction, immediately after
-- 01_schema_logic.sql (it reuses that fixture).
-- ============================================================================

\set ON_ERROR_STOP on
\pset pager off
-- Grant table privileges to the stub roles the same way Supabase does.
grant usage on schema public to anon, authenticated;

-- Sam (33333333) is a stranger: not the requester, not assigned, has one bid.
-- Rae (11111111) is the requester. Mo (22222222) is the assigned member.

-- R1: stranger cannot read the private chat of an assigned task
insert into public.messages (task_id, sender_id, body)
values ('44444444-4444-4444-4444-444444444444','11111111-1111-1111-1111-111111111111','Access code is 4821.');

set local role authenticated;
set local "request.jwt.claim.sub" = '33333333-3333-3333-3333-333333333333';
select 'R1 stranger sees 0 chat messages' as test, count(*) = 0 as pass from public.messages;

-- R2: the assigned member does see them
set local "request.jwt.claim.sub" = '22222222-2222-2222-2222-222222222222';
select 'R2 assigned member sees the chat' as test, count(*) = 1 as pass from public.messages;

-- R3: a bidder cannot see rival bids (sealed board)
set local "request.jwt.claim.sub" = '33333333-3333-3333-3333-333333333333';
select 'R3 bidder sees only their own bid' as test,
       bool_and(member_id = '33333333-3333-3333-3333-333333333333') as pass
  from public.bids;

-- R4: the requester sees every bid on their task
set local "request.jwt.claim.sub" = '11111111-1111-1111-1111-111111111111';
select 'R4 requester sees all bids on their task' as test, count(*) = 2 as pass
  from public.bids where task_id = '44444444-4444-4444-4444-444444444444';

-- R5: a stranger cannot read the escrow ledger
set local "request.jwt.claim.sub" = '33333333-3333-3333-3333-333333333333';
select 'R5 stranger sees no transactions' as test, count(*) = 0 as pass from public.transactions;

-- R6: the payer can
set local "request.jwt.claim.sub" = '11111111-1111-1111-1111-111111111111';
select 'R6 payer sees their transaction' as test, count(*) = 1 as pass from public.transactions;

-- R7: nobody can write the ledger from a client session
do $$
begin
  insert into public.transactions (task_id, payer_id, payee_id, amount)
  values ('44444444-4444-4444-4444-444444444444',
          '11111111-1111-1111-1111-111111111111',
          '11111111-1111-1111-1111-111111111111', 999);
  raise exception 'R7 FAILED: client wrote the escrow ledger';
exception when insufficient_privilege then
  raise notice 'R7 ledger is service-role only: OK';
end $$;

-- R8: a user cannot grant themselves verification or a rep score
do $$
begin
  update public.users set is_id_verified = true, rep_score = 5.00
   where id = '11111111-1111-1111-1111-111111111111';
  raise exception 'R8 FAILED: user self-granted trust fields';
exception when insufficient_privilege then
  raise notice 'R8 trust fields are platform-owned: OK';
end $$;

-- R9: a completed/disputed task leaves the public board
set local "request.jwt.claim.sub" = '33333333-3333-3333-3333-333333333333';
select 'R9 completed task hidden from non-participants' as test,
       count(*) = 0 as pass
  from public.tasks where id = '44444444-4444-4444-4444-444444444444';

-- R10: the open licensed task is still browsable by anyone
select 'R10 open task is browsable' as test, count(*) = 1 as pass
  from public.tasks where id = '55555555-5555-5555-5555-555555555555';
