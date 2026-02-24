-- Hello World table for CodeLeash scaffold
create table if not exists greetings (
    id uuid primary key default gen_random_uuid(),
    message text not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    deleted_at timestamptz  -- soft delete
);

-- Index for soft-delete queries
create index idx_greetings_not_deleted on greetings (id) where deleted_at is null;
