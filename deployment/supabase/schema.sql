-- AEC AI News Database Schema for Supabase
-- GDPR Compliant Newsletter Subscription System

-- Enable necessary extensions
create extension if not exists "uuid-ossp";

-- Subscriptions table
create table public.subscriptions (
  id uuid default uuid_generate_v4() primary key,
  email text unique not null,
  subscribed_at timestamp with time zone default now(),
  unsubscribed_at timestamp with time zone,
  gdpr_consent boolean not null default false,
  consent_date timestamp with time zone,
  source text default 'unknown',
  status text default 'active' check (status in ('active', 'unsubscribed', 'bounced')),
  preferences jsonb default '{"newsletter": true, "promotions": false, "updates": true}'::jsonb,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);

-- Newsletters table
create table public.newsletters (
  id uuid default uuid_generate_v4() primary key,
  title text not null,
  content text not null,
  html_content text not null,
  subject_line text not null,
  created_at timestamp with time zone default now(),
  sent_at timestamp with time zone,
  subscriber_count integer default 0,
  open_count integer default 0,
  click_count integer default 0,
  open_rate decimal(5,2),
  click_rate decimal(5,2),
  status text default 'draft' check (status in ('draft', 'scheduled', 'sent'))
);

-- GDPR Consents table
create table public.gdpr_consents (
  id uuid default uuid_generate_v4() primary key,
  email text not null,
  consent_type text not null,
  consent_given boolean not null,
  consent_date timestamp with time zone default now(),
  consent_source text not null,
  ip_address inet,
  user_agent text,
  created_at timestamp with time zone default now()
);

-- GDPR Actions (for audit trail)
create table public.gdpr_actions (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid,
  email text,
  action_type text not null check (action_type in ('subscribe', 'unsubscribe', 'data_access', 'data_deletion', 'data_update')),
  action_date timestamp with time zone default now(),
  details jsonb,
  ip_address inet,
  user_agent text,
  created_at timestamp with time zone default now()
);

-- Data Deletion Requests
create table public.data_deletion_requests (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid,
  email text not null,
  requested_at timestamp with time zone default now(),
  processed_at timestamp with time zone,
  reason text,
  status text default 'pending' check (status in ('pending', 'processed', 'cancelled')),
  created_at timestamp with time zone default now()
);

-- Unsubscribe Tokens (for secure one-click unsubscribe)
create table public.unsubscribe_tokens (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid,
  email text not null,
  token text unique not null,
  created_at timestamp with time zone default now(),
  expires_at timestamp with time zone not null,
  used_at timestamp with time zone
);

-- User Preferences (detailed subscription preferences)
create table public.user_preferences (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid,
  email text not null,
  newsletter_enabled boolean default true,
  promotions_enabled boolean default false,
  updates_enabled boolean default true,
  frequency text default 'weekly' check (frequency in ('daily', 'weekly', 'monthly')),
  categories text[] default '{}',
  unsubscribed_at timestamp with time zone,
  unsubscribe_reason text,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);

-- Newsletter Analytics
create table public.newsletter_analytics (
  id uuid default uuid_generate_v4() primary key,
  newsletter_id uuid references public.newsletters(id) on delete cascade,
  subscriber_id uuid,
  email text not null,
  action_type text not null check (action_type in ('sent', 'delivered', 'opened', 'clicked', 'bounced', 'complained')),
  action_date timestamp with time zone default now(),
  metadata jsonb,
  created_at timestamp with time zone default now()
);

-- Create indexes for performance
create index idx_subscriptions_email on public.subscriptions(email);
create index idx_subscriptions_status on public.subscriptions(status);
create index idx_subscriptions_created_at on public.subscriptions(created_at);

create index idx_newsletters_status on public.newsletters(status);
create index idx_newsletters_sent_at on public.newsletters(sent_at);

create index idx_gdpr_consents_email on public.gdpr_consents(email);
create index idx_gdpr_consents_consent_date on public.gdpr_consents(consent_date);

create index idx_gdpr_actions_email on public.gdpr_actions(email);
create index idx_gdpr_actions_action_date on public.gdpr_actions(action_date);

create index idx_unsubscribe_tokens_token on public.unsubscribe_tokens(token);
create index idx_unsubscribe_tokens_email on public.unsubscribe_tokens(email);

create index idx_newsletter_analytics_newsletter_id on public.newsletter_analytics(newsletter_id);
create index idx_newsletter_analytics_email on public.newsletter_analytics(email);
create index idx_newsletter_analytics_action_type on public.newsletter_analytics(action_type);

-- Row Level Security (RLS) Policies

-- Enable RLS on all tables
alter table public.subscriptions enable row level security;
alter table public.newsletters enable row level security;
alter table public.gdpr_consents enable row level security;
alter table public.gdpr_actions enable row level security;
alter table public.data_deletion_requests enable row level security;
alter table public.unsubscribe_tokens enable row level security;
alter table public.user_preferences enable row level security;
alter table public.newsletter_analytics enable row level security;

-- Subscriptions policies
create policy "Subscriptions are publicly readable" on public.subscriptions
  for select using (true);

create policy "Anyone can insert subscriptions" on public.subscriptions
  for insert with check (true);

create policy "Users can update their own subscription" on public.subscriptions
  for update using (auth.email() = email);

-- Newsletters policies (public read for sent newsletters)
create policy "Sent newsletters are publicly readable" on public.newsletters
  for select using (status = 'sent');

-- GDPR policies (users can access their own data)
create policy "Users can view their GDPR consents" on public.gdpr_consents
  for select using (auth.email() = email);

create policy "Anyone can insert GDPR consents" on public.gdpr_consents
  for insert with check (true);

create policy "Users can view their GDPR actions" on public.gdpr_actions
  for select using (auth.email() = email);

create policy "Anyone can insert GDPR actions" on public.gdpr_actions
  for insert with check (true);

-- Data deletion requests policies
create policy "Users can view their deletion requests" on public.data_deletion_requests
  for select using (auth.email() = email);

create policy "Anyone can create deletion requests" on public.data_deletion_requests
  for insert with check (true);

-- Unsubscribe tokens policies
create policy "Tokens are publicly readable" on public.unsubscribe_tokens
  for select using (true);

create policy "Anyone can create unsubscribe tokens" on public.unsubscribe_tokens
  for insert with check (true);

-- User preferences policies
create policy "Users can view their preferences" on public.user_preferences
  for select using (auth.email() = email);

create policy "Anyone can insert preferences" on public.user_preferences
  for insert with check (true);

create policy "Users can update their preferences" on public.user_preferences
  for update using (auth.email() = email);

-- Newsletter analytics policies (privacy-conscious)
create policy "Analytics are not publicly readable" on public.newsletter_analytics
  for select using (false);

-- Functions for GDPR compliance

-- Function to generate unsubscribe token
create or replace function generate_unsubscribe_token(user_email text)
returns text
language plpgsql
security definer
as $$
declare
  token text;
begin
  token := encode(gen_random_bytes(32), 'hex');
  
  insert into public.unsubscribe_tokens (email, token, expires_at)
  values (user_email, token, now() + interval '30 days');
  
  return token;
end;
$$;

-- Function to process unsubscribe
create or replace function process_unsubscribe(unsubscribe_token text)
returns boolean
language plpgsql
security definer
as $$
declare
  token_record record;
begin
  -- Find and validate token
  select * into token_record
  from public.unsubscribe_tokens
  where token = unsubscribe_token
    and expires_at > now()
    and used_at is null;
  
  if not found then
    return false;
  end if;
  
  -- Mark token as used
  update public.unsubscribe_tokens
  set used_at = now()
  where id = token_record.id;
  
  -- Update subscription status
  update public.subscriptions
  set status = 'unsubscribed',
      unsubscribed_at = now()
  where email = token_record.email;
  
  -- Log GDPR action
  insert into public.gdpr_actions (email, action_type, details)
  values (token_record.email, 'unsubscribe', jsonb_build_object('method', 'one_click', 'token', unsubscribe_token));
  
  return true;
end;
$$;

-- Function to request data deletion (GDPR Right to be Forgotten)
create or replace function request_data_deletion(user_email text, deletion_reason text default null)
returns uuid
language plpgsql
security definer
as $$
declare
  request_id uuid;
begin
  insert into public.data_deletion_requests (email, reason)
  values (user_email, deletion_reason)
  returning id into request_id;
  
  -- Log GDPR action
  insert into public.gdpr_actions (email, action_type, details)
  values (user_email, 'data_deletion', jsonb_build_object('request_id', request_id, 'reason', deletion_reason));
  
  return request_id;
end;
$$;

-- Function to update consent
create or replace function update_consent(user_email text, consent_type text, consent_given boolean, source text default 'web')
returns void
language plpgsql
security definer
as $$
begin
  insert into public.gdpr_consents (email, consent_type, consent_given, consent_source)
  values (user_email, consent_type, consent_given, source);
  
  -- Log GDPR action
  insert into public.gdpr_actions (email, action_type, details)
  values (user_email, 'data_update', jsonb_build_object('consent_type', consent_type, 'consent_given', consent_given));
end;
$$;

-- Trigger to update updated_at timestamp
create or replace function update_updated_at_column()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger update_subscriptions_updated_at
  before update on public.subscriptions
  for each row execute function update_updated_at_column();

create trigger update_user_preferences_updated_at
  before update on public.user_preferences
  for each row execute function update_updated_at_column();