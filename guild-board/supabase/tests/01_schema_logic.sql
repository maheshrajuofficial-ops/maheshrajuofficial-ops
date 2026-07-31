-- ============================================================================
-- Trigger and state-machine tests.
-- Run against a database with 00_local_stub + both migrations + seed applied.
-- Rows marked `t` pass; NOTICE lines mark the negative cases that correctly
-- raised. Any ERROR is a failure.
-- ============================================================================

\set ON_ERROR_STOP on
\pset pager off

-- Two auth users; the handle_new_user trigger should mirror them into public.users
insert into auth.users (id, email, raw_user_meta_data) values
  ('11111111-1111-1111-1111-111111111111', 'rae@example.com', '{"full_name":"Rae Requester"}'),
  ('22222222-2222-2222-2222-222222222222', 'mo@example.com',  '{"full_name":"Mo Member"}'),
  ('33333333-3333-3333-3333-333333333333', 'sam@example.com', '{"full_name":"Sam Stranger"}');

select 'T1 profile mirror' as test,
       (select count(*) = 3 from public.users) as pass;

update public.users set stripe_account_id = 'acct_mo', stripe_payouts_enabled = true,
       is_id_verified = true where id = '22222222-2222-2222-2222-222222222222';

-- A task in Chicago, 2 miles from the city centre
insert into public.tasks (id, requester_id, city_id, category_id, title, description,
                          reward_amount, lat, long, safety_ack_at, currency)
select '44444444-4444-4444-4444-444444444444',
       '11111111-1111-1111-1111-111111111111',
       c.id, cat.id,
       'Move a two-seater sofa up three flights',
       'Third floor walk-up, no lift. Sofa is already wrapped and ready by the door.',
       120.00, 41.9, -87.63, now(), 'USD'
from public.cities c, public.categories cat
where c.slug = 'chicago' and cat.slug = 'moving';

-- T2: a requester must not be able to bid on their own task
do $$
begin
  insert into public.bids (task_id, member_id, amount, proposal_text)
  values ('44444444-4444-4444-4444-444444444444',
          '11111111-1111-1111-1111-111111111111', 100,
          'I would like to do my own task, which should not be allowed at all.');
  raise exception 'T2 FAILED: self-bid was accepted';
exception when check_violation then
  raise notice 'T2 self-bid blocked: OK';
end $$;

-- T3: licensed-trade gate — unlicensed member cannot bid on a high_licensed task
insert into public.tasks (id, requester_id, city_id, category_id, title, description,
                          reward_amount, lat, long, safety_ack_at, risk_tier)
select '55555555-5555-5555-5555-555555555555',
       '11111111-1111-1111-1111-111111111111', c.id, cat.id,
       'Replace the consumer unit in a two-bed flat',
       'Existing board is a rewireable fuse box. Needs a modern RCBO board and a certificate.',
       800.00, 41.9, -87.63, now(), 'high_licensed'
from public.cities c, public.categories cat
where c.slug = 'chicago' and cat.slug = 'electrical';

do $$
begin
  insert into public.bids (task_id, member_id, amount, proposal_text)
  values ('55555555-5555-5555-5555-555555555555',
          '22222222-2222-2222-2222-222222222222', 750,
          'I have done plenty of these before and can start on Monday morning.');
  raise exception 'T3 FAILED: unlicensed bid accepted on licensed task';
exception when check_violation then
  raise notice 'T3 licensed-trade gate held: OK';
end $$;

-- Grant the licence, then it should succeed
update public.users set licensed_trades = array['electrical']
 where id = '22222222-2222-2222-2222-222222222222';
insert into public.bids (task_id, member_id, amount, proposal_text)
values ('55555555-5555-5555-5555-555555555555',
        '22222222-2222-2222-2222-222222222222', 750,
        'Licensed and insured. I can supply the board and certificate on completion.');
select 'T4 licensed bid allowed once licence on file' as test, true as pass;

-- Two bids on the sofa task
insert into public.bids (id, task_id, member_id, amount, proposal_text) values
  ('66666666-6666-6666-6666-666666666666', '44444444-4444-4444-4444-444444444444',
   '22222222-2222-2222-2222-222222222222', 110, 'I have a trolley and straps, can do it Saturday morning.'),
  ('77777777-7777-7777-7777-777777777777', '44444444-4444-4444-4444-444444444444',
   '33333333-3333-3333-3333-333333333333', 140, 'Two of us with a van, we can be there this afternoon.');

-- T5: accepting one bid assigns the task and rejects the rest
update public.bids set status = 'accepted' where id = '66666666-6666-6666-6666-666666666666';

select 'T5 accept assigns task' as test,
       (select status = 'assigned' and assigned_to = '22222222-2222-2222-2222-222222222222'
          from public.tasks where id = '44444444-4444-4444-4444-444444444444') as pass;
select 'T6 other bids auto-rejected' as test,
       (select status = 'rejected' from public.bids where id = '77777777-7777-7777-7777-777777777777') as pass;

-- T7: escrow ledger drives task status
insert into public.transactions (id, task_id, bid_id, payer_id, payee_id, amount, platform_fee,
                                 stripe_payment_intent_id, escrow_status)
values ('88888888-8888-8888-8888-888888888888', '44444444-4444-4444-4444-444444444444',
        '66666666-6666-6666-6666-666666666666',
        '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
        110.00, 8.25, 'pi_test_1', 'pending_hold');

select 'T7 payout computed on insert' as test,
       (select payout_amount = 101.75 from public.transactions
         where id = '88888888-8888-8888-8888-888888888888') as pass;

update public.transactions set escrow_status = 'held'
 where id = '88888888-8888-8888-8888-888888888888';
select 'T8 held -> task in_escrow' as test,
       (select status = 'in_escrow' from public.tasks
         where id = '44444444-4444-4444-4444-444444444444') as pass;

-- T9: reward is frozen once in escrow
do $$
begin
  update public.tasks set reward_amount = 5 where id = '44444444-4444-4444-4444-444444444444';
  raise exception 'T9 FAILED: reward changed while in escrow';
exception when check_violation then
  raise notice 'T9 reward frozen under escrow: OK';
end $$;

-- T10: a dispute freezes the release timer
update public.tasks set released_after = now() + interval '72 hours'
 where id = '44444444-4444-4444-4444-444444444444';
insert into public.disputes (task_id, raised_by, reason)
values ('44444444-4444-4444-4444-444444444444', '11111111-1111-1111-1111-111111111111',
        'The sofa was left in the stairwell rather than in the flat as agreed.');
select 'T10 dispute freezes timer' as test,
       (select status = 'disputed' and released_after is null from public.tasks
         where id = '44444444-4444-4444-4444-444444444444') as pass;

-- T11: auto-release queue must exclude disputed tasks
select 'T11 disputed task excluded from release queue' as test,
       (select count(*) = 0 from public.escrow_auto_release_queue
         where task_id = '44444444-4444-4444-4444-444444444444') as pass;

-- Resolve for the member, release the funds
update public.disputes set status = 'resolved_member', resolved_at = now()
 where task_id = '44444444-4444-4444-4444-444444444444';
update public.transactions set escrow_status = 'released'
 where id = '88888888-8888-8888-8888-888888888888';

select 'T12 release -> task completed' as test,
       (select status = 'completed' and completed_at is not null from public.tasks
         where id = '44444444-4444-4444-4444-444444444444') as pass;
select 'T13 tasks_completed incremented' as test,
       (select tasks_completed = 1 from public.users
         where id = '22222222-2222-2222-2222-222222222222') as pass;

-- T14: reviews recompute reputation
insert into public.reviews (task_id, reviewer_id, reviewee_id, rating, comment)
values ('44444444-4444-4444-4444-444444444444',
        '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222',
        5, 'Turned up early, no fuss.');
select 'T14 rep_score derived from reviews' as test,
       (select rep_score = 5.00 and rep_count = 1 from public.users
         where id = '22222222-2222-2222-2222-222222222222') as pass;

-- T15: a review from a non-participant is refused
do $$
begin
  insert into public.reviews (task_id, reviewer_id, reviewee_id, rating)
  values ('44444444-4444-4444-4444-444444444444',
          '33333333-3333-3333-3333-333333333333',
          '22222222-2222-2222-2222-222222222222', 1);
  raise exception 'T15 FAILED: outsider review accepted';
exception when insufficient_privilege then
  raise notice 'T15 outsider review blocked: OK';
end $$;

-- T16: chat requires an assignment
do $$
begin
  insert into public.messages (task_id, sender_id, body)
  values ('55555555-5555-5555-5555-555555555555',
          '22222222-2222-2222-2222-222222222222', 'hello?');
  raise exception 'T16 FAILED: chat opened before assignment';
exception when check_violation then
  raise notice 'T16 chat gated on assignment: OK';
end $$;

-- T17: radius search
select 'T17 radius search finds the open licensed task' as test,
       (select count(*) >= 1 from public.tasks_within_radius('chicago', 41.878113, -87.629799, 25)) as pass;
select 'T18 radius search excludes far-away tasks' as test,
       (select count(*) = 0 from public.tasks_within_radius('chicago', 41.878113, -87.629799, 0.5)) as pass;
