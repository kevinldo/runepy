BEGIN;

create table if not exists players (
  id bigserial primary key,
  display_name text unique not null,
  first_added_at timestamptz not null default now(),
  last_fetched_at timestamptz
);

create table if not exists fetches (
  id bigserial primary key,
  player_id bigint not null references players(id),
  fetched_at timestamptz not null default now(),
  status text not null default 'success'
);

create table if not exists skills (
  id smallserial primary key,
  name text unique not null
);

create table if not exists activities (
  id smallserial primary key,
  name text unique not null
);

create table if not exists player_skill_snapshots (
  fetch_id bigint not null references fetches(id) on delete cascade,
  skill_id smallint not null references skills(id),
  rank int,
  level int not null,
  xp bigint not null,
  primary key (fetch_id, skill_id)
);

create table if not exists player_activity_snapshots (
  fetch_id bigint not null references fetches(id) on delete cascade,
  activity_id smallint not null references activities(id),
  rank int,
  score bigint not null,
  primary key (fetch_id, activity_id)
);

create index if not exists fetches_player_fetched_at_idx
on fetches (player_id, fetched_at desc);

create index if not exists player_skill_snapshots_skill_id_idx
on player_skill_snapshots (skill_id);

create index if not exists player_activity_snapshots_activity_id_idx
on player_activity_snapshots (activity_id);

COMMIT;
