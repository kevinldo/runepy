"""Shared pytest fixtures for RunePy backend tests."""

from __future__ import annotations

from datetime import UTC, datetime
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_SESSION_URL", "sqlite:///:memory:")

from runepy.main import app  # noqa: E402
from runepy.models.hiscores import (  # noqa: E402
    ActivityStat,
    ActivityStatChange,
    PlayerHiscores,
    PlayerStatChanges,
    SkillStat,
    SkillStatChange,
)


@pytest.fixture
def sample_player_hiscores() -> PlayerHiscores:
    """Return representative player hiscore data."""

    return PlayerHiscores(
        name="Zezt",
        skills=[
            SkillStat(id=0, name="Attack", rank=100, level=50, xp=101_333),
            SkillStat(id=1, name="Defence", rank=200, level=45, xp=61_512),
        ],
        activities=[
            ActivityStat(id=0, name="Bounty Hunter", rank=10, score=25),
        ],
    )


@pytest.fixture
def later_player_hiscores() -> PlayerHiscores:
    """Return later player hiscore data with changed values."""

    return PlayerHiscores(
        name="Zezt",
        skills=[
            SkillStat(id=0, name="Attack", rank=90, level=51, xp=112_333),
            SkillStat(id=1, name="Defence", rank=190, level=46, xp=71_512),
        ],
        activities=[
            ActivityStat(id=0, name="Bounty Hunter", rank=8, score=30),
        ],
    )


@pytest.fixture
def sample_hiscore_payload() -> dict[str, object]:
    """Return a valid RuneScape hiscore response payload."""

    return {
        "name": "Zezt",
        "skills": [
            {"id": 0, "name": "Attack", "rank": 100, "level": 50, "xp": 101333},
            {"id": 1, "name": "Defence", "rank": 200, "level": 45, "xp": 61512},
        ],
        "activities": [
            {"id": 0, "name": "Bounty Hunter", "rank": 10, "score": 25},
        ],
    }


@pytest.fixture
def sample_stat_changes() -> PlayerStatChanges:
    """Return representative stat changes for one player."""

    earliest = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    latest = datetime(2026, 1, 2, 12, 0, tzinfo=UTC)
    return PlayerStatChanges(
        name="Zezt",
        window="24h",
        window_start=earliest,
        window_end=latest,
        skills=[
            SkillStatChange(
                name="Attack",
                earliest_fetched_at=earliest,
                latest_fetched_at=latest,
                earliest_rank=100,
                latest_rank=90,
                rank_delta=-10,
                earliest_level=50,
                latest_level=51,
                level_delta=1,
                earliest_xp=101_333,
                latest_xp=112_333,
                xp_delta=11_000,
            )
        ],
        activities=[
            ActivityStatChange(
                name="Bounty Hunter",
                earliest_fetched_at=earliest,
                latest_fetched_at=latest,
                earliest_rank=10,
                latest_rank=8,
                rank_delta=-2,
                earliest_score=25,
                latest_score=30,
                score_delta=5,
            )
        ],
    )


@pytest.fixture
def client() -> TestClient:
    """Return a FastAPI test client for the application."""

    return TestClient(app)


@pytest.fixture(scope="session")
def db_engine():
    """Return a migrated Postgres engine or skip DB integration tests."""

    url = os.environ.get("TEST_DATABASE_SESSION_URL") or os.environ.get(
        "DATABASE_SESSION_URL"
    )
    if not url or url.startswith("sqlite"):
        pytest.skip("Postgres DATABASE_SESSION_URL is not configured")

    engine = create_engine(url)
    try:
        with engine.begin() as connection:
            connection.execute(text("select 1"))
            migration_sql = Path("db/migrations/001_init_schema.sql").read_text()
            for statement in migration_sql.split(";"):
                if statement.strip():
                    connection.execute(text(statement))
    except OperationalError as exc:
        pytest.skip(f"Postgres database is not reachable: {exc}")

    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Return an isolated database session for one integration test."""

    Session = sessionmaker(bind=db_engine)
    with db_engine.begin() as connection:
        connection.execute(text("""
                truncate table
                    player_activity_snapshots,
                    player_skill_snapshots,
                    fetches,
                    activities,
                    skills,
                    players
                restart identity cascade
                """))

    with Session() as session:
        yield session
        session.rollback()
