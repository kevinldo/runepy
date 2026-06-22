"""Service functions for player hiscore workflows."""

from runepy.clients.runescape import fetch_player_hiscores
from runepy.db.hiscore_snapshots import (
    get_player_stat_changes,
    save_player_hiscore_snapshot,
)
from runepy.db.session import SessionLocal
from runepy.models.hiscores import PlayerHiscores, PlayerStatChanges

RECENT_STAT_CHANGE_WINDOW = "recent"

STAT_CHANGE_WINDOWS = {
    RECENT_STAT_CHANGE_WINDOW: RECENT_STAT_CHANGE_WINDOW,
    "24h": "1 day",
    "7d": "7 days",
    "30d": "30 days",
    "3m": "3 months",
    "6m": "6 months",
    "1y": "1 year",
}


class InvalidStatsWindowError(ValueError):
    """Represent an unsupported stat change window."""

    pass


class StoredPlayerNotFoundError(LookupError):
    """Represent a player with no stored hiscore snapshots."""

    pass


def parse_stat_change_window(window: str) -> str:
    """Translate a public stat window into a database comparison value.

    Args:
        window (str): Public stat change window key.

    Returns:
        str: Postgres interval value or recent comparison sentinel.
    """

    try:
        return STAT_CHANGE_WINDOWS[window]
    except KeyError as exc:
        raise InvalidStatsWindowError(window) from exc


async def fetch_and_store_player_hiscores(player_name: str) -> PlayerHiscores:
    """Fetch and persist current hiscore data for a RuneScape player.

    Args:
        player_name (str): RuneScape display name to snapshot.

    Returns:
        PlayerHiscores: Current hiscore data saved for the player.
    """

    hiscores = await fetch_player_hiscores(player_name)

    with SessionLocal() as session:
        with session.begin():
            save_player_hiscore_snapshot(session, hiscores)

    return hiscores


def read_player_stat_changes(player_name: str, window: str) -> PlayerStatChanges:
    """Read stored stat changes for a RuneScape player.

    Args:
        player_name (str): RuneScape display name to read.
        window (str): Rolling time window for comparing stored snapshots.

    Returns:
        PlayerStatChanges: Stat changes calculated within the requested window.
    """

    window_interval = parse_stat_change_window(window)

    with SessionLocal() as session:
        stat_changes = get_player_stat_changes(
            session,
            player_name,
            window,
            window_interval,
        )

    if stat_changes is None:
        raise StoredPlayerNotFoundError(player_name)

    return stat_changes
