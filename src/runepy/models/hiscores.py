"""Pydantic models for RuneScape hiscore responses."""

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
