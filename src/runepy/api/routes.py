"""FastAPI route definitions for the application.

This module defines the public HTTP endpoints exposed by the app. Routes should
coordinate request handling by calling client and database modules, while
keeping external API logic and SQL persistence details in their dedicated
modules.
"""

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
    return {"status": "ok"}


async def _run_hiscore_action(action, player_name: str) -> PlayerHiscores:
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
    return await _run_hiscore_action(fetch_player_hiscores, player_name)


@router.post("/players/{player_name}/hiscores/snapshots", response_model=PlayerHiscores)
async def snapshot_player_hiscores(player_name: str) -> PlayerHiscores:
    return await _run_hiscore_action(fetch_and_store_player_hiscores, player_name)


@router.get("/players/{player_name}/stats/changes", response_model=PlayerStatChanges)
def player_stat_changes(player_name: str, window: str) -> PlayerStatChanges:
    try:
        return read_player_stat_changes(player_name, window)
    except InvalidStatsWindowError:
        raise HTTPException(
            status_code=400,
            detail="Unsupported window. Use one of: 24h, 7d, 30d",
        )
    except StoredPlayerNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Player {player_name!r} has no stored snapshots",
        )
