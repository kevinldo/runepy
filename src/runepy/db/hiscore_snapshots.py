"""Database operations for RuneScape hiscore data.

This module is responsible for saving and reading player hiscore snapshots
using the contracted Postgres schema. It should contain the SQL/database logic
for players, fetch records, skills, activities, and their snapshot tables,
keeping that persistence logic separate from FastAPI routes and RuneScape API
client code.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session

from runepy.models.hiscores import PlayerHiscores


def save_player_hiscore_snapshot(session: Session, hiscores: PlayerHiscores) -> int:
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
