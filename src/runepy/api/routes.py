"""FastAPI route definitions for the application."""

from fastapi import APIRouter, HTTPException

from runepy.clients.runescape import (
    fetch_player_hiscores,
    PlayerNotFoundError,
    RuneScapeClientError,
    RuneScapeUnavailableError,
)
from runepy.models.hiscores import PlayerHiscores, PlayerStatChanges
from runepy.services.player_hiscores import (
    fetch_and_store_player_hiscores,
    InvalidStatsWindowError,
    read_player_stat_changes,
    StoredPlayerNotFoundError,
)

router = APIRouter()


@router.get("/")
def root():
    """Return the application health status.

    Returns:
        dict[str, str]: The health status response body.
    """

    return {"status": "ok"}


async def _run_hiscore_action(action, player_name: str) -> PlayerHiscores:
    """Run a hiscore action and translate client errors to HTTP responses.

    Args:
        action (Callable): Async function that fetches or stores player hiscores.
        player_name (str): RuneScape display name to process.

    Returns:
        PlayerHiscores: Parsed hiscore data for the requested player.
    """

    try:
        return await action(player_name)
    except PlayerNotFoundError:
        raise HTTPException(status_code=404, detail=f"Player {player_name!r} not found")
    except RuneScapeUnavailableError:
        raise HTTPException(
            status_code=502,
            detail="Could not reach RuneScape hiscore service",
        )
    except RuneScapeClientError:
        raise HTTPException(
            status_code=502,
            detail="RuneScape hiscore service returned invalid data",
        )


@router.get("/players/{player_name}/hiscores", response_model=PlayerHiscores)
async def player_hiscores(player_name: str) -> PlayerHiscores:
    """Fetch current hiscore data for a RuneScape player.

    Args:
        player_name (str): RuneScape display name to fetch.

    Returns:
        PlayerHiscores: Current hiscore data from RuneScape.
    """

    return await _run_hiscore_action(fetch_player_hiscores, player_name)


@router.post("/players/{player_name}/hiscores/snapshots", response_model=PlayerHiscores)
async def snapshot_player_hiscores(player_name: str) -> PlayerHiscores:
    """Fetch and store a RuneScape player's current hiscore data.

    Args:
        player_name (str): RuneScape display name to snapshot.

    Returns:
        PlayerHiscores: Current hiscore data saved for the player.
    """

    return await _run_hiscore_action(fetch_and_store_player_hiscores, player_name)


@router.get("/players/{player_name}/stats/changes", response_model=PlayerStatChanges)
def player_stat_changes(player_name: str, window: str) -> PlayerStatChanges:
    """Read stored stat changes for a RuneScape player.

    Args:
        player_name (str): RuneScape display name to read.
        window (str): Rolling time window for comparing stored snapshots.

    Returns:
        PlayerStatChanges: Stat changes calculated within the requested window.
    """

    try:
        return read_player_stat_changes(player_name, window)
    except InvalidStatsWindowError:
        raise HTTPException(
            status_code=400,
            detail="Unsupported window. Use one of: 24h, 7d, 30d, 3m, 6m, 1y",
        )
    except StoredPlayerNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Player {player_name!r} has no stored snapshots",
        )
