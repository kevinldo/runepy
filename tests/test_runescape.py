"""Client tests for RuneScape hiscore calls."""

from typing import ClassVar

import pytest
import httpx

from runepy.clients import runescape
from runepy.clients.runescape import (
    PlayerNotFoundError,
    RuneScapeClientError,
    RuneScapeUnavailableError,
    fetch_player_hiscores,
)


class FakeResponse:
    """Minimal HTTP response fake for hiscore client tests."""

    def __init__(self, status_code, payload=None):
        """Initialize the fake response.

        Args:
            status_code (int): HTTP status code to expose.
            payload (object | None): JSON payload or exception to raise.
        """

        self.status_code = status_code
        self._payload = payload

    def json(self):
        """Return the configured JSON payload.

        Returns:
            object: Configured response payload.
        """

        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class FakeAsyncClient:
    """Minimal async client fake that returns a configured response."""

    response: ClassVar[FakeResponse | None] = None
    request_error: ClassVar[httpx.RequestError | None] = None
    requested_url: ClassVar[str | None] = None
    requested_params: ClassVar[dict[str, str] | None] = None

    def __init__(self, timeout):
        """Initialize the fake async client.

        Args:
            timeout (float): Timeout passed by the production client.
        """

        self.timeout = timeout

    async def __aenter__(self):
        """Enter the fake async client context.

        Returns:
            FakeAsyncClient: Active fake async client.
        """

        return self

    async def __aexit__(self, exc_type, exc, traceback):
        """Exit the fake async client context without suppressing errors.

        Args:
            exc_type (type | None): Raised exception type, if any.
            exc (BaseException | None): Raised exception instance, if any.
            traceback (TracebackType | None): Raised exception traceback, if any.
        """

        return None

    async def get(self, url, params):
        """Record request details and return the configured response.

        Args:
            url (str): Requested URL.
            params (dict[str, str]): Request query parameters.

        Returns:
            FakeResponse: Configured fake response.
        """

        type(self).requested_url = url
        type(self).requested_params = params
        if type(self).request_error is not None:
            raise type(self).request_error
        return type(self).response


@pytest.fixture(autouse=True)
def reset_fake_async_client():
    """Reset fake async client state before each test."""

    FakeAsyncClient.response = None
    FakeAsyncClient.request_error = None
    FakeAsyncClient.requested_url = None
    FakeAsyncClient.requested_params = None


@pytest.mark.asyncio
async def test_fetch_player_hiscores_parses_valid_hiscores(
    monkeypatch,
    sample_hiscore_payload,
):
    """Verify valid RuneScape payloads parse into player hiscore models.

    Args:
        monkeypatch (MonkeyPatch): Pytest monkeypatch fixture.
        sample_hiscore_payload (dict[str, object]): Valid hiscore API payload.
    """

    FakeAsyncClient.response = FakeResponse(200, sample_hiscore_payload)
    monkeypatch.setattr(runescape.httpx, "AsyncClient", FakeAsyncClient)

    hiscores = await fetch_player_hiscores("Zezt")

    assert hiscores.name == "Zezt"
    assert hiscores.skills[0].name == "Attack"
    assert hiscores.activities[0].score == 25
    assert FakeAsyncClient.requested_url == runescape.HISCORE_URL
    assert FakeAsyncClient.requested_params == {"player": "Zezt"}


@pytest.mark.asyncio
async def test_fetch_player_hiscores_handles_missing_player(monkeypatch):
    """Verify missing RuneScape players raise the client lookup error.

    Args:
        monkeypatch (MonkeyPatch): Pytest monkeypatch fixture.
    """

    FakeAsyncClient.response = FakeResponse(404, {})
    monkeypatch.setattr(runescape.httpx, "AsyncClient", FakeAsyncClient)

    with pytest.raises(PlayerNotFoundError):
        await fetch_player_hiscores("Missing")


@pytest.mark.asyncio
async def test_fetch_player_hiscores_handles_request_failure(monkeypatch):
    """Verify request failures raise the upstream availability error.

    Args:
        monkeypatch (MonkeyPatch): Pytest monkeypatch fixture.
    """

    FakeAsyncClient.request_error = httpx.RequestError("network unavailable")
    monkeypatch.setattr(runescape.httpx, "AsyncClient", FakeAsyncClient)

    with pytest.raises(RuneScapeUnavailableError):
        await fetch_player_hiscores("Zezt")


@pytest.mark.asyncio
async def test_fetch_player_hiscores_handles_upstream_server_error(monkeypatch):
    """Verify upstream server errors raise the availability error.

    Args:
        monkeypatch (MonkeyPatch): Pytest monkeypatch fixture.
    """

    FakeAsyncClient.response = FakeResponse(500, {})
    monkeypatch.setattr(runescape.httpx, "AsyncClient", FakeAsyncClient)

    with pytest.raises(RuneScapeUnavailableError):
        await fetch_player_hiscores("Zezt")


@pytest.mark.asyncio
async def test_fetch_player_hiscores_rejects_invalid_payload(monkeypatch):
    """Verify schema-invalid payloads raise the client data error.

    Args:
        monkeypatch (MonkeyPatch): Pytest monkeypatch fixture.
    """

    FakeAsyncClient.response = FakeResponse(200, {"name": "Zezt"})
    monkeypatch.setattr(runescape.httpx, "AsyncClient", FakeAsyncClient)

    with pytest.raises(RuneScapeClientError):
        await fetch_player_hiscores("Zezt")
