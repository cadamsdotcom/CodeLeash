---
title: 'Worker System'
sidebar_position: 7
---

CodeLeash includes a background job queue built on PostgreSQL. Instead of using a separate message broker, jobs are stored in a regular table and claimed atomically using `FOR UPDATE SKIP LOCKED`.

## Jobs Table

The jobs table is created by a [Supabase migration](https://github.com/cadamsdotcom/CodeLeash/blob/main/supabase/migrations/20260223000002_create_jobs_table.sql):

```sql
create table if not exists public.jobs (
  id bigserial primary key,
  queue text not null,               -- e.g. 'greeting-jobs'
  payload jsonb not null,
  status text not null default 'pending',

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
```

Two indexes support efficient polling:

- `idx_jobs_pending` on `scheduled_for` where `status = 'pending'`
- `idx_jobs_status_queue` on `(status, queue)`

RLS is enabled with a policy restricting access to the `service_role`.

## Atomic Job Claiming

The `claim_jobs` SQL function uses `FOR UPDATE SKIP LOCKED` to atomically claim jobs without conflicts between concurrent workers:

```sql
create or replace function public.claim_jobs(
  p_queues text[] default null,
  p_limit int default 1
) returns table(id bigint, queue text, payload jsonb, attempts int, max_attempts int) as $$
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
  returning public.jobs.id, public.jobs.queue, public.jobs.payload,
            public.jobs.attempts, public.jobs.max_attempts;
$$ language sql;
```

> [`supabase/migrations/20260223000002_create_jobs_table.sql`](https://github.com/cadamsdotcom/CodeLeash/blob/main/supabase/migrations/20260223000002_create_jobs_table.sql)

`FOR UPDATE SKIP LOCKED` means:

- Each row is locked when selected
- Other workers skip locked rows instead of waiting
- No two workers can claim the same job
- No advisory locks or external coordination needed

## JobRepository

The [`JobRepository`](https://github.com/cadamsdotcom/CodeLeash/blob/main/app/repositories/job.py) wraps the Supabase client with typed methods:

| Method                                                 | What It Does                                       |
| ------------------------------------------------------ | -------------------------------------------------- |
| `enqueue(queue, payload, delay_seconds, max_attempts)` | Insert a new job                                   |
| `claim(queues, limit)`                                 | Call `claim_jobs` RPC, return `Job` dataclass list |
| `complete(job_id)`                                     | Set status to `completed`, record timestamp        |
| `fail(job_id, error)`                                  | Retry with backoff or mark as permanently failed   |
| `get_queue_depth(queue)`                               | Count pending jobs (for metrics)                   |

### Enqueuing a Job

```python
async def enqueue(self, queue: str, payload: dict, delay_seconds: int = 0,
                  max_attempts: int = 3) -> int:
    scheduled_for = datetime.now(UTC) + timedelta(seconds=delay_seconds)
    response = self.client.table(self.table_name).insert({
        "queue": queue,
        "payload": payload,
        "scheduled_for": scheduled_for.isoformat(),
        "max_attempts": max_attempts,
    }).execute()
```

> [`app/repositories/job.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/app/repositories/job.py)

### Retry with Exponential Backoff

When a job fails and has remaining attempts, the `fail()` method schedules a retry:

```python
# Backoff: 30 seconds × attempt number
backoff = timedelta(seconds=30 * attempts)
scheduled_for = datetime.now(UTC) + backoff
update_data = {
    "status": "pending",
    "last_error": error,
    "scheduled_for": scheduled_for.isoformat(),
}
```

When all attempts are exhausted, the job is marked `failed` with `completed_at` set.

### Metrics Integration

Every `enqueue`, `fail`, and `complete` operation updates a Prometheus gauge for queue depth. Connection errors are detected and recorded as a separate metric.

## QueueWorker

The [`QueueWorker`](https://github.com/cadamsdotcom/CodeLeash/blob/main/app/workers/queue_worker.py) class runs a polling loop:

```python
class QueueWorker:
    def __init__(self, job_repo, handlers):
        self.job_repo = job_repo
        self.handlers = handlers  # {"queue-name": handler_instance}
        self._running = False

    async def run(self, poll_interval=5):
        self._running = True
        queues = list(self.handlers.keys())
        while self._running:
            jobs = await self.job_repo.claim(queues=queues, limit=1)
            for job in jobs:
                task = asyncio.create_task(self._execute_job(job))
                self._active_tasks.add(task)
            await asyncio.sleep(poll_interval)
```

Each job is dispatched to its handler's `handle()` method. The worker tracks active tasks and supports graceful shutdown with a configurable timeout.

### Job Execution

```python
async def _execute_job(self, job):
    handler = self.handlers.get(job.queue)
    if handler is None:
        await self.job_repo.fail(job.id, f"No handler for queue {job.queue}")
        return

    start_time = time.time()
    try:
        await handler.handle(job)
        await self.job_repo.complete(job.id)
        record_queue_job_processed(queue=job.queue, status="completed")
    except Exception as e:
        await self.job_repo.fail(job.id, str(e))
        record_queue_job_processed(queue=job.queue, status="failed")
    finally:
        duration = time.time() - start_time
        record_queue_job_duration(queue=job.queue, duration=duration)
```

## Handler Registration

Handlers are wired up in [`app/core/worker_dependencies.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/app/core/worker_dependencies.py):

```python
def create_queue_worker() -> QueueWorker:
    container = _get_container()
    greeting_handler = GreetingHandler(
        greeting_repository=container.get_greeting_repository()
    )
    return QueueWorker(
        job_repo=container.get_job_repository(),
        handlers={
            "greeting-jobs": greeting_handler,
        },
    )
```

This follows the same container DI pattern as the web application.

### Writing a Handler

Handlers implement an `async handle(job)` method. Here's the [`GreetingHandler`](https://github.com/cadamsdotcom/CodeLeash/blob/main/app/workers/handlers/greeting_handler.py):

```python
class GreetingHandler:
    def __init__(self, greeting_repository: GreetingRepository) -> None:
        self.greeting_repository = greeting_repository

    async def handle(self, job: Job) -> dict[str, Any]:
        greeting_id = job.payload.get("greeting_id", "")
        greeting = await self.greeting_repository.get_by_id(greeting_id)
        return {"status": "processed", "greeting_id": greeting_id}
```

> [`app/workers/handlers/greeting_handler.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/app/workers/handlers/greeting_handler.py)

## Hot Reload in Development

The [`worker.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/worker.py) entry point uses `watchdog` to monitor file changes in development:

```python
class WorkerReloadHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if self._should_reload_for_file(filepath):
            self.restart_event.set()
```

The reload handler:

- Watches `app/` (recursive) and `worker.py`
- Skips irrelevant files (templates, static, tests, routes)
- Debounces with a 0.5-second delay
- Signals the main loop to restart the worker

In production (`ENVIRONMENT != "development"`), hot reload is disabled and the worker runs until interrupted.

## Adding a New Job Type

1. **Create a handler** in `app/workers/handlers/`:

```python
class MyHandler:
    def __init__(self, my_service):
        self.my_service = my_service

    async def handle(self, job):
        await self.my_service.do_work(job.payload)
```

2. **Register it** in [`app/core/worker_dependencies.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/app/core/worker_dependencies.py):

```python
my_handler = MyHandler(my_service=container.get_my_service())
return QueueWorker(
    job_repo=container.get_job_repository(),
    handlers={
        "greeting-jobs": greeting_handler,
        "my-jobs": my_handler,  # Add here
    },
)
```

3. **Enqueue jobs** from your service:

```python
await job_repo.enqueue("my-jobs", {"key": "value"})
```
