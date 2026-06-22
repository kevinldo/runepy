"""Pydantic models for RuneScape hiscore responses."""

from datetime import datetime

from pydantic import BaseModel


class SkillStat(BaseModel):
    """A single skill entry from a player's hiscore data."""

    id: int
    name: str
    rank: int
    level: int
    xp: int


class ActivityStat(BaseModel):
    """A single activity (minigame, event, etc.) entry from a player's hiscore data."""

    id: int
    name: str
    rank: int
    score: int


class PlayerHiscores(BaseModel):
    """Parsed hiscore data for one RuneScape player."""

    name: str
    skills: list[SkillStat]
    activities: list[ActivityStat]


class SkillStatChange(BaseModel):
    """A skill's earliest-to-latest change inside a rolling time window."""

    name: str
    earliest_fetched_at: datetime
    latest_fetched_at: datetime
    earliest_rank: int | None
    latest_rank: int | None
    rank_delta: int | None
    earliest_level: int
    latest_level: int
    level_delta: int
    earliest_xp: int
    latest_xp: int
    xp_delta: int


class ActivityStatChange(BaseModel):
    """An activity's earliest-to-latest change inside a rolling time window."""

    name: str
    earliest_fetched_at: datetime
    latest_fetched_at: datetime
    earliest_rank: int | None
    latest_rank: int | None
    rank_delta: int | None
    earliest_score: int
    latest_score: int
    score_delta: int


class PlayerStatChanges(BaseModel):
    """Historical stat changes for one player over a requested window."""

    name: str
    window: str
    window_start: datetime
    window_end: datetime
    skills: list[SkillStatChange]
    activities: list[ActivityStatChange]
