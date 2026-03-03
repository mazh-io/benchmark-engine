-- Lemon Squeezy subscription state (one active subscription per user)

create table if not exists public.subscriptions (
  id                    uuid default gen_random_uuid() primary key,
  user_id               uuid not null references public.users(id) on delete cascade,
  ls_subscription_id    text not null unique,
  ls_customer_id        text not null,
  variant_id            text not null,
  product_name          text,
  status                text not null default 'active',
  current_period_end    timestamptz,
  cancel_at_period_end  boolean not null default false,
  created_at            timestamptz default now(),
  updated_at            timestamptz default now()
);

create unique index if not exists idx_subscriptions_user
  on public.subscriptions(user_id);

alter table public.subscriptions enable row level security;

create policy "Users read own subscription"
  on public.subscriptions for select
  using (auth.uid() = user_id);
