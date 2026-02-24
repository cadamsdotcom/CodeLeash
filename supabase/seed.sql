-- Seed data for development and e2e testing
-- Applied on `supabase db reset`
insert into greetings (message)
values ('Hello from CodeLeash!')
on conflict do nothing;
