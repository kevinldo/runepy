"""Route tests for the FastAPI API layer."""

from runepy.api import routes
from runepy.clients.runescape import (
    PlayerNotFoundError,
    RuneScapeClientError,
    RuneScapeUnavailableError,
)
from runepy.services.player_hiscores import StoredPlayerNotFoundError


def test_root_returns_ok(client):
    """Verify the health check route returns an OK response.

    Args:
        client (TestClient): FastAPI test client.
    """

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_player_hiscores_returns_success(client, monkeypatch, sample_player_hiscores):
    """Verify the live hiscore route returns fetched player data.

    Args:
        client (TestClient): FastAPI test client.
        monkeypatch (MonkeyPatch): Pytest monkeypatch fixture.
        sample_player_hiscores (PlayerHiscores): Mocked hiscore response.
    """

    async def fake_fetch_player_hiscores(player_name):
        assert player_name == "Zezt"
        return sample_player_hiscores

    monkeypatch.setattr(routes, "fetch_player_hiscores", fake_fetch_player_hiscores)

    response = client.get("/players/Zezt/hiscores")

    assert response.status_code == 200
    assert response.json() == sample_player_hiscores.model_dump(mode="json")


def test_player_hiscores_maps_missing_player(client, monkeypatch):
    """Verify the live hiscore route maps missing players to HTTP 404.

    Args:
        client (TestClient): FastAPI test client.
        monkeypatch (MonkeyPatch): Pytest monkeypatch fixture.
    """

    async def fake_fetch_player_hiscores(player_name):
        raise PlayerNotFoundError

    monkeypatch.setattr(routes, "fetch_player_hiscores", fake_fetch_player_hiscores)

    response = client.get("/players/Missing/hiscores")

    assert response.status_code == 404
    assert response.json() == {"detail": "Player 'Missing' not found"}


def test_player_hiscores_maps_unavailable_upstream(client, monkeypatch):
    """Verify the live hiscore route maps upstream failures to HTTP 502.

    Args:
        client (TestClient): FastAPI test client.
        monkeypatch (MonkeyPatch): Pytest monkeypatch fixture.
    """

    async def fake_fetch_player_hiscores(player_name):
        raise RuneScapeUnavailableError

    monkeypatch.setattr(routes, "fetch_player_hiscores", fake_fetch_player_hiscores)

    response = client.get("/players/Zezt/hiscores")

    assert response.status_code == 502
    assert response.json() == {"detail": "Could not reach RuneScape hiscore service"}


def test_player_hiscores_maps_invalid_upstream_data(client, monkeypatch):
    """Verify the live hiscore route maps invalid upstream data to HTTP 502.

    Args:
        client (TestClient): FastAPI test client.
        monkeypatch (MonkeyPatch): Pytest monkeypatch fixture.
    """

    async def fake_fetch_player_hiscores(player_name):
        raise RuneScapeClientError

    monkeypatch.setattr(routes, "fetch_player_hiscores", fake_fetch_player_hiscores)

    response = client.get("/players/Zezt/hiscores")

    assert response.status_code == 502
    assert response.json() == {
        "detail": "RuneScape hiscore service returned invalid data"
    }


def test_snapshot_player_hiscores_returns_fetched_hiscores(
    client,
    monkeypatch,
    sample_player_hiscores,
):
    """Verify the snapshot route returns fetched and stored hiscore data.

    Args:
        client (TestClient): FastAPI test client.
        monkeypatch (MonkeyPatch): Pytest monkeypatch fixture.
        sample_player_hiscores (PlayerHiscores): Mocked snapshot response.
    """

    async def fake_fetch_and_store_player_hiscores(player_name):
        assert player_name == "Zezt"
        return sample_player_hiscores

    monkeypatch.setattr(
        routes,
        "fetch_and_store_player_hiscores",
        fake_fetch_and_store_player_hiscores,
    )

    response = client.post("/players/Zezt/hiscores/snapshots")

    assert response.status_code == 200
    assert response.json() == sample_player_hiscores.model_dump(mode="json")


def test_player_stat_changes_returns_recent_changes(
    client, monkeypatch, sample_stat_changes
):
    """Verify stat changes can return latest-to-previous deltas."""

    recent_stat_changes = sample_stat_changes.model_copy(update={"window": "recent"})

    def fake_read_player_stat_changes(player_name, window):
        assert player_name == "Zezt"
        assert window == "recent"
        return recent_stat_changes

    monkeypatch.setattr(
        routes, "read_player_stat_changes", fake_read_player_stat_changes
    )

    response = client.get("/players/Zezt/stats/changes?window=recent")

    assert response.status_code == 200
    assert response.json() == recent_stat_changes.model_dump(mode="json")


def test_player_stat_changes_returns_unsupported_window(client):
    """Verify stat changes reject unsupported rolling windows.

    Args:
        client (TestClient): FastAPI test client.
    """

    response = client.get("/players/Zezt/stats/changes?window=bad")

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Unsupported window. Use one of: recent, 24h, 7d, 30d, 3m, 6m, 1y"
    }


def test_player_stat_changes_returns_unstored_player(client, monkeypatch):
    """Verify stat changes return HTTP 404 for players without snapshots.

    Args:
        client (TestClient): FastAPI test client.
        monkeypatch (MonkeyPatch): Pytest monkeypatch fixture.
    """

    def fake_read_player_stat_changes(player_name, window):
        raise StoredPlayerNotFoundError(player_name)

    monkeypatch.setattr(
        routes, "read_player_stat_changes", fake_read_player_stat_changes
    )

    response = client.get("/players/Unknown/stats/changes?window=24h")

    assert response.status_code == 404
    assert response.json() == {"detail": "Player 'Unknown' has no stored snapshots"}
