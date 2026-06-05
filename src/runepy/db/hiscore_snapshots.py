"""Database operations for RuneScape hiscore data."""

from sqlalchemy import text
from sqlalchemy.orm import Session

from runepy.models.hiscores import (
    ActivityStatChange,
    PlayerHiscores,
    PlayerStatChanges,
    SkillStatChange,
)


def save_player_hiscore_snapshot(session: Session, hiscores: PlayerHiscores) -> int:
    """Save a player hiscore snapshot and related stat rows.

    Args:
        session (Session): Active SQLAlchemy session for database writes.
        hiscores (PlayerHiscores): Player hiscore data to persist.

    Returns:
        int: Database identifier for the created fetch record.
    """

    player_id = session.execute(
        text("""
            insert into players (display_name)
            values (:display_name)
            on conflict (display_name)
            do update set display_name = excluded.display_name
            returning id
            """),
        {"display_name": hiscores.name},
    ).scalar_one()

    fetch_id = session.execute(
        text("""
            insert into fetches (player_id, status)
            values (:player_id, 'success')
            returning id
            """),
        {"player_id": player_id},
    ).scalar_one()

    for skill in hiscores.skills:
        skill_id = session.execute(
            text("""
                insert into skills (name)
                values (:name)
                on conflict (name)
                do update set name = excluded.name
                returning id
                """),
            {"name": skill.name},
        ).scalar_one()

        session.execute(
            text("""
                insert into player_skill_snapshots (
                    fetch_id, skill_id, rank, level, xp
                )
                values (
                    :fetch_id, :skill_id, :rank, :level, :xp
                )
                """),
            {
                "fetch_id": fetch_id,
                "skill_id": skill_id,
                "rank": skill.rank,
                "level": skill.level,
                "xp": skill.xp,
            },
        )

    for activity in hiscores.activities:
        activity_id = session.execute(
            text("""
                insert into activities (name)
                values (:name)
                on conflict (name)
                do update set name = excluded.name
                returning id
                """),
            {"name": activity.name},
        ).scalar_one()

        session.execute(
            text("""
                insert into player_activity_snapshots (
                    fetch_id, activity_id, rank, score
                )
                values (
                    :fetch_id, :activity_id, :rank, :score
                )
                """),
            {
                "fetch_id": fetch_id,
                "activity_id": activity_id,
                "rank": activity.rank,
                "score": activity.score,
            },
        )

    session.execute(
        text("""
            update players
            set last_fetched_at = now()
            where id = :player_id
            """),
        {"player_id": player_id},
    )

    return fetch_id


def get_player_stat_changes(
    session: Session,
    player_name: str,
    window: str,
    window_interval: str,
) -> PlayerStatChanges | None:
    """Read earliest-to-latest stat changes for a stored player and window.

    Args:
        session (Session): Active SQLAlchemy session for database reads.
        player_name (str): RuneScape display name to read.
        window (str): Public stat change window key.
        window_interval (str): Postgres interval value for the requested window.

    Returns:
        PlayerStatChanges | None: Calculated stat changes, or None if the
        player has no stored snapshots.
    """

    player = (
        session.execute(
            text("""
            select id, display_name
            from players
            where display_name = :display_name
            """),
            {"display_name": player_name},
        )
        .mappings()
        .one_or_none()
    )

    if player is None:
        return None

    bounds = (
        session.execute(
            text("""
            select
                now() - cast(:window_interval as interval) as window_start,
                now() as window_end
            """),
            {"window_interval": window_interval},
        )
        .mappings()
        .one()
    )

    query_params = {
        "player_id": player["id"],
        "window_start": bounds["window_start"],
        "window_end": bounds["window_end"],
    }

    skill_rows = (
        session.execute(
            text("""
            with skill_points as (
                select
                    f.id as fetch_id,
                    f.fetched_at,
                    s.name,
                    pss.rank,
                    pss.level,
                    pss.xp
                from fetches f
                join player_skill_snapshots pss on pss.fetch_id = f.id
                join skills s on s.id = pss.skill_id
                where f.player_id = :player_id
                    and f.status = 'success'
                    and f.fetched_at >= :window_start
                    and f.fetched_at <= :window_end
            )
            select
                name,
                (array_agg(fetched_at order by fetched_at asc, fetch_id asc))[1]
                    as earliest_fetched_at,
                (array_agg(fetched_at order by fetched_at desc, fetch_id desc))[1]
                    as latest_fetched_at,
                (array_agg(rank order by fetched_at asc, fetch_id asc))[1]
                    as earliest_rank,
                (array_agg(rank order by fetched_at desc, fetch_id desc))[1]
                    as latest_rank,
                (array_agg(level order by fetched_at asc, fetch_id asc))[1]
                    as earliest_level,
                (array_agg(level order by fetched_at desc, fetch_id desc))[1]
                    as latest_level,
                (array_agg(xp order by fetched_at asc, fetch_id asc))[1]
                    as earliest_xp,
                (array_agg(xp order by fetched_at desc, fetch_id desc))[1]
                    as latest_xp
            from skill_points
            group by name
            order by name
            """),
            query_params,
        )
        .mappings()
        .all()
    )

    activity_rows = (
        session.execute(
            text("""
            with activity_points as (
                select
                    f.id as fetch_id,
                    f.fetched_at,
                    a.name,
                    pas.rank,
                    pas.score
                from fetches f
                join player_activity_snapshots pas on pas.fetch_id = f.id
                join activities a on a.id = pas.activity_id
                where f.player_id = :player_id
                    and f.status = 'success'
                    and f.fetched_at >= :window_start
                    and f.fetched_at <= :window_end
            )
            select
                name,
                (array_agg(fetched_at order by fetched_at asc, fetch_id asc))[1]
                    as earliest_fetched_at,
                (array_agg(fetched_at order by fetched_at desc, fetch_id desc))[1]
                    as latest_fetched_at,
                (array_agg(rank order by fetched_at asc, fetch_id asc))[1]
                    as earliest_rank,
                (array_agg(rank order by fetched_at desc, fetch_id desc))[1]
                    as latest_rank,
                (array_agg(score order by fetched_at asc, fetch_id asc))[1]
                    as earliest_score,
                (array_agg(score order by fetched_at desc, fetch_id desc))[1]
                    as latest_score
            from activity_points
            group by name
            order by name
            """),
            query_params,
        )
        .mappings()
        .all()
    )

    return PlayerStatChanges(
        name=player["display_name"],
        window=window,
        window_start=bounds["window_start"],
        window_end=bounds["window_end"],
        skills=[_skill_change_from_row(row) for row in skill_rows],
        activities=[_activity_change_from_row(row) for row in activity_rows],
    )


def _rank_delta(latest_rank: int | None, earliest_rank: int | None) -> int | None:
    """Calculate rank movement when both rank values are present.

    Args:
        latest_rank (int | None): Latest stored rank value.
        earliest_rank (int | None): Earliest stored rank value.

    Returns:
        int | None: Rank delta, or None when either rank is missing.
    """

    if latest_rank is None or earliest_rank is None:
        return None
    return latest_rank - earliest_rank


def _skill_change_from_row(row) -> SkillStatChange:
    """Build a skill stat change model from a database row.

    Args:
        row (Mapping): Database row containing earliest and latest skill values.

    Returns:
        SkillStatChange: Skill change model for one skill.
    """

    return SkillStatChange(
        name=row["name"],
        earliest_fetched_at=row["earliest_fetched_at"],
        latest_fetched_at=row["latest_fetched_at"],
        earliest_rank=row["earliest_rank"],
        latest_rank=row["latest_rank"],
        rank_delta=_rank_delta(row["latest_rank"], row["earliest_rank"]),
        earliest_level=row["earliest_level"],
        latest_level=row["latest_level"],
        level_delta=row["latest_level"] - row["earliest_level"],
        earliest_xp=row["earliest_xp"],
        latest_xp=row["latest_xp"],
        xp_delta=row["latest_xp"] - row["earliest_xp"],
    )


def _activity_change_from_row(row) -> ActivityStatChange:
    """Build an activity stat change model from a database row.

    Args:
        row (Mapping): Database row containing earliest and latest activity values.

    Returns:
        ActivityStatChange: Activity change model for one activity.
    """

    return ActivityStatChange(
        name=row["name"],
        earliest_fetched_at=row["earliest_fetched_at"],
        latest_fetched_at=row["latest_fetched_at"],
        earliest_rank=row["earliest_rank"],
        latest_rank=row["latest_rank"],
        rank_delta=_rank_delta(row["latest_rank"], row["earliest_rank"]),
        earliest_score=row["earliest_score"],
        latest_score=row["latest_score"],
        score_delta=row["latest_score"] - row["earliest_score"],
    )
