"""Service tests for player hiscore workflows."""

import pytest

from runepy.models.hiscores import PlayerStatChanges
from runepy.services import player_hiscores
from runepy.services.player_hiscores import (
    InvalidStatsWindowError,
    StoredPlayerNotFoundError,
    fetch_and_store_player_hiscores,
    parse_stat_change_window,
    read_player_stat_changes,
)


class FakeTransaction:
    """Minimal transaction context manager for service tests."""

    def __enter__(self):
        """Enter the fake transaction context.

        Returns:
            FakeTransaction: Active fake transaction.
        """

        return self

    def __exit__(self, exc_type, exc, traceback):
        """Exit the fake transaction context without suppressing errors.

        Args:
            exc_type (type | None): Raised exception type, if any.
            exc (BaseException | None): Raised exception instance, if any.
            traceback (TracebackType | None): Raised exception traceback, if any.
        """

        return None


class FakeSession:
    """Minimal session context manager for service tests."""

    def __enter__(self):
        """Enter the fake session context.

        Returns:
            FakeSession: Active fake session.
        """

        return self

    def __exit__(self, exc_type, exc, traceback):
        """Exit the fake session context without suppressing errors.

        Args:
            exc_type (type | None): Raised exception type, if any.
            exc (BaseException | None): Raised exception instance, if any.
            traceback (TracebackType | None): Raised exception traceback, if any.
        """

        return None

    def begin(self):
        """Begin a fake database transaction.

        Returns:
            FakeTransaction: Transaction context manager for the fake session.
        """

        return FakeTransaction()


class FakeSessionLocal:
    """Minimal session factory for service tests."""

    last_session = None

    def __call__(self):
        """Create and remember a fake session.

        Returns:
            FakeSession: New fake session instance.
        """

        self.last_session = FakeSession()
        return self.last_session


def test_parse_stat_change_window_maps_supported_windows():
    """Verify every supported stat-change window maps to a DB interval."""

    expected_windows = {
        "24h": "1 day",
        "7d": "7 days",
        "30d": "30 days",
        "3m": "3 months",
        "6m": "6 months",
        "1y": "1 year",
    }

    for window, interval in expected_windows.items():
        assert parse_stat_change_window(window) == interval


def test_parse_stat_change_window_raises_for_unsupported_window():
    """Verify unsupported stat-change windows raise the service error."""

    with pytest.raises(InvalidStatsWindowError):
        parse_stat_change_window("bad")


@pytest.mark.asyncio
async def test_fetch_and_store_player_hiscores_saves_snapshot(
    monkeypatch,
    sample_player_hiscores,
):
    """Verify fetched hiscores are persisted inside a session transaction.

    Args:
        monkeypatch (MonkeyPatch): Pytest monkeypatch fixture.
        sample_player_hiscores (PlayerHiscores): Mocked hiscore data.
    """

    fake_session_local = FakeSessionLocal()
    saved = {}

    async def fake_fetch_player_hiscores(player_name):
        assert player_name == "Zezt"
        return sample_player_hiscores

    def fake_save_player_hiscore_snapshot(session, hiscores):
        saved["session"] = session
        saved["hiscores"] = hiscores
        return 1

    monkeypatch.setattr(player_hiscores, "SessionLocal", fake_session_local)
    monkeypatch.setattr(
        player_hiscores,
        "fetch_player_hiscores",
        fake_fetch_player_hiscores,
    )
    monkeypatch.setattr(
        player_hiscores,
        "save_player_hiscore_snapshot",
        fake_save_player_hiscore_snapshot,
    )

    hiscores = await fetch_and_store_player_hiscores("Zezt")

    assert hiscores == sample_player_hiscores
    assert saved == {
        "session": fake_session_local.last_session,
        "hiscores": sample_player_hiscores,
    }


def test_read_player_stat_changes_returns_stored_changes(
    monkeypatch, sample_stat_changes
):
    """Verify stored stat changes are returned for a known player.

    Args:
        monkeypatch (MonkeyPatch): Pytest monkeypatch fixture.
        sample_stat_changes (PlayerStatChanges): Mocked stored stat changes.
    """

    fake_session_local = FakeSessionLocal()

    def fake_get_player_stat_changes(session, player_name, window, window_interval):
        assert session == fake_session_local.last_session
        assert player_name == "Zezt"
        assert window == "24h"
        assert window_interval == "1 day"
        return sample_stat_changes

    monkeypatch.setattr(player_hiscores, "SessionLocal", fake_session_local)
    monkeypatch.setattr(
        player_hiscores,
        "get_player_stat_changes",
        fake_get_player_stat_changes,
    )

    stat_changes = read_player_stat_changes("Zezt", "24h")

    assert isinstance(stat_changes, PlayerStatChanges)
    assert stat_changes == sample_stat_changes


def test_read_player_stat_changes_raises_for_unstored_player(monkeypatch):
    """Verify missing stored snapshots raise the service lookup error.

    Args:
        monkeypatch (MonkeyPatch): Pytest monkeypatch fixture.
    """

    fake_session_local = FakeSessionLocal()

    def fake_get_player_stat_changes(session, player_name, window, window_interval):
        return None

    monkeypatch.setattr(player_hiscores, "SessionLocal", fake_session_local)
    monkeypatch.setattr(
        player_hiscores,
        "get_player_stat_changes",
        fake_get_player_stat_changes,
    )

    with pytest.raises(StoredPlayerNotFoundError):
        read_player_stat_changes("Unknown", "24h")
