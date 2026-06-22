"""Client functions for RuneScape's public APIs."""

import httpx
from pydantic import ValidationError
from runepy.models.hiscores import PlayerHiscores

HISCORE_URL = "https://secure.runescape.com/m=hiscore/index_lite.json"


class RuneScapeClientError(Exception):
    """Represent a RuneScape hiscore client failure."""

    pass


class PlayerNotFoundError(RuneScapeClientError):
    """Represent a missing RuneScape player in hiscore responses."""

    pass


class RuneScapeUnavailableError(RuneScapeClientError):
    """Represent an unavailable RuneScape hiscore service."""

    pass


async def fetch_player_hiscores(player_name: str) -> PlayerHiscores:
    """Fetch current hiscore data from RuneScape.

    Args:
        player_name (str): RuneScape display name to fetch.

    Returns:
        PlayerHiscores: Parsed hiscore data from RuneScape.
    """

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
