from runepy.clients.runescape import fetch_player_hiscores
from runepy.db.hiscore_snapshots import (
    get_player_stat_changes,
    save_player_hiscore_snapshot,
)
from runepy.db.session import SessionLocal
from runepy.models.hiscores import PlayerHiscores, PlayerStatChanges

STAT_CHANGE_WINDOWS = {
    "24h": "1 day",
    "7d": "7 days",
    "30d": "30 days",
    "6m": "6 months",
    "1y": "1 year",
}


class InvalidStatsWindowError(ValueError):
    pass


class StoredPlayerNotFoundError(LookupError):
    pass


def parse_stat_change_window(window: str) -> str:
    try:
        return STAT_CHANGE_WINDOWS[window]
    except KeyError as exc:
        raise InvalidStatsWindowError(window) from exc


async def fetch_and_store_player_hiscores(player_name: str) -> PlayerHiscores:
    hiscores = await fetch_player_hiscores(player_name)

    with SessionLocal() as session:
        with session.begin():
            save_player_hiscore_snapshot(session, hiscores)

    return hiscores


def read_player_stat_changes(player_name: str, window: str) -> PlayerStatChanges:
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
