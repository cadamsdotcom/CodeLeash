-- Simple PostgreSQL Job Queue
-- Replaces pgmq with a simpler native PostgreSQL approach using FOR UPDATE SKIP LOCKED

-- Create the jobs table
create table if not exists public.jobs (
  id bigserial primary key,
  queue text not null,              -- e.g. 'greeting-jobs'
  payload jsonb not null,
  status text not null default 'pending',  -- pending, processing, completed, failed

  -- Scheduling
  scheduled_for timestamptz not null default now(),

  -- Retry tracking
  attempts int not null default 0,
  max_attempts int not null default 3,
  last_error text,

  -- Timestamps
  created_at timestamptz not null default now(),
  started_at timestamptz,
  completed_at timestamptz
);

-- Index for efficient polling of pending jobs
create index if not exists idx_jobs_pending on public.jobs(scheduled_for)
  where status = 'pending';

-- Index for querying by status and queue
create index if not exists idx_jobs_status_queue on public.jobs(status, queue);

-- Enable RLS
alter table public.jobs enable row level security;

-- RLS policy: Only service role can access jobs table
create policy "Service role only" on public.jobs
  for all
  using (auth.role() = 'service_role');

-- Claim jobs atomically - the only operation that needs FOR UPDATE SKIP LOCKED
create or replace function public.claim_jobs(p_queues text[] default null, p_limit int default 1)
returns table(id bigint, queue text, payload jsonb, attempts int, max_attempts int) as $$
  with claimed as (
    select j.id from public.jobs j
    where j.status = 'pending'
      and j.scheduled_for <= now()
      and (p_queues is null or j.queue = any(p_queues))
    order by j.id
    for update skip locked
    limit p_limit
  )
  update public.jobs set
    status = 'processing',
    started_at = now(),
    attempts = public.jobs.attempts + 1
  from claimed
  where public.jobs.id = claimed.id
  returning public.jobs.id, public.jobs.queue, public.jobs.payload, public.jobs.attempts, public.jobs.max_attempts;
$$ language sql;

-- Grant execute permissions to authenticated users (for RPC calls)
grant execute on function public.claim_jobs(text[], int) to authenticated;
grant execute on function public.claim_jobs(text[], int) to service_role;
