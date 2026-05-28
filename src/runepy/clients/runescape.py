"""Client functions for RuneScape's public APIs.

This module is responsible for making outbound requests to RuneScape services,
handling API errors, and returning validated application models. FastAPI routes
should call functions from this module instead of using HTTP client code
directly.
"""

import httpx
from pydantic import ValidationError
from runepy.models.hiscores import PlayerHiscores

HISCORE_URL = "https://secure.runescape.com/m=hiscore/index_lite.json"


class RuneScapeClientError(Exception):
    pass


class PlayerNotFoundError(RuneScapeClientError):
    pass


class RuneScapeUnavailableError(RuneScapeClientError):
    pass


async def fetch_player_hiscores(player_name: str) -> PlayerHiscores:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(HISCORE_URL, params={"player": player_name})
    except httpx.RequestError as exc:
        raise RuneScapeUnavailableError from exc

    if response.status_code == 404:
        raise PlayerNotFoundError

    if response.status_code >= 400:
        raise RuneScapeUnavailableError

    try:
        return PlayerHiscores.model_validate(response.json())
    except (ValueError, ValidationError) as exc:
        raise RuneScapeClientError from exc
