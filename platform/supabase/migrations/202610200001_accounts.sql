-- Account storage only. This migration never reads or changes model/parcel data.
begin;

create table public.user_profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    email text not null unique,
    role text not null check (role in ('staff', 'productor')),
    name text not null check (length(btrim(name)) between 1 and 120),
    phone text not null default '' check (length(phone) <= 40),
    active boolean not null default true,
    access_mode text not null default 'none' check (access_mode in ('none', 'selected', 'municipalities', 'all')),
    parcel_ids text[] not null default '{}',
    municipalities jsonb not null default '[]'::jsonb check (jsonb_typeof(municipalities) = 'array'),
    session_version integer not null default 1 check (session_version >= 1),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    check (
        (access_mode in ('none', 'all') and cardinality(parcel_ids) = 0 and municipalities = '[]'::jsonb)
        or (access_mode = 'selected' and cardinality(parcel_ids) > 0 and municipalities = '[]'::jsonb)
        or (access_mode = 'municipalities' and cardinality(parcel_ids) = 0 and jsonb_array_length(municipalities) > 0)
    )
);

create index user_profiles_created on public.user_profiles(created_at desc, id);
alter table public.user_profiles enable row level security;
-- No anon access; authenticated identities can only read their own profile.
-- All writes and staff listing go through the server after its role check.
revoke all on public.user_profiles from anon, authenticated;
grant select on public.user_profiles to authenticated;
grant select, insert, update, delete on public.user_profiles to service_role;
create policy own_profile on public.user_profiles for select to authenticated
    using (id = (select auth.uid()));

create function public.account_profile_updated() returns trigger
language plpgsql set search_path = '' as $$
begin
    new.updated_at := clock_timestamp();
    if new.active is distinct from old.active or new.role is distinct from old.role
       or new.email is distinct from old.email then
        new.session_version := old.session_version + 1;
    end if;
    return new;
end;
$$;
create trigger account_profile_updated before update on public.user_profiles
    for each row execute function public.account_profile_updated();

-- Keep email consistent if it is changed through Auth Admin or the Supabase dashboard.
create function public.account_email_sync() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
    update public.user_profiles set email = lower(new.email) where id = new.id;
    return new;
end;
$$;
create trigger account_email_sync after update of email on auth.users
    for each row when (old.email is distinct from new.email)
    execute function public.account_email_sync();

create function public.revoke_app_sessions(target_id uuid) returns void
language sql security definer set search_path = '' as $$
    update public.user_profiles set session_version = session_version + 1 where id = target_id;
$$;

revoke all on function public.account_profile_updated() from public, anon, authenticated;
revoke all on function public.account_email_sync() from public, anon, authenticated;
revoke all on function public.revoke_app_sessions(uuid) from public, anon, authenticated;
grant execute on function public.revoke_app_sessions(uuid) to service_role;

-- No automatic profile from sign-up or user_metadata: identities created outside
-- the authorized provisioning process have no access, and cannot choose a role.
commit;
