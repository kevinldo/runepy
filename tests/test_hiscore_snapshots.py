"""Database integration tests for hiscore snapshot persistence."""

from sqlalchemy import text

from runepy.db.hiscore_snapshots import (
    get_player_stat_changes,
    save_player_hiscore_snapshot,
)


def test_save_player_hiscore_snapshot_creates_player_and_fetch_rows(
    db_session,
    sample_player_hiscores,
):
    """Verify saving a snapshot creates player and fetch records.

    Args:
        db_session (Session): Isolated database session.
        sample_player_hiscores (PlayerHiscores): Sample hiscore data to save.
    """

    fetch_id = save_player_hiscore_snapshot(db_session, sample_player_hiscores)

    player_count = db_session.execute(text("select count(*) from players")).scalar_one()
    fetch_row = (
        db_session.execute(
            text("select id, status from fetches where id = :fetch_id"),
            {"fetch_id": fetch_id},
        )
        .mappings()
        .one()
    )

    assert player_count == 1
    assert fetch_row["id"] == fetch_id
    assert fetch_row["status"] == "success"


def test_save_player_hiscore_snapshot_stores_skill_rows(
    db_session,
    sample_player_hiscores,
):
    """Verify saving a snapshot stores skill dimension and snapshot rows.

    Args:
        db_session (Session): Isolated database session.
        sample_player_hiscores (PlayerHiscores): Sample hiscore data to save.
    """

    fetch_id = save_player_hiscore_snapshot(db_session, sample_player_hiscores)

    skill_count = db_session.execute(text("select count(*) from skills")).scalar_one()
    snapshot_rows = (
        db_session.execute(
            text("""
            select s.name, pss.rank, pss.level, pss.xp
            from player_skill_snapshots pss
            join skills s on s.id = pss.skill_id
            where pss.fetch_id = :fetch_id
            order by s.name
            """),
            {"fetch_id": fetch_id},
        )
        .mappings()
        .all()
    )

    assert skill_count == 2
    assert [row["name"] for row in snapshot_rows] == ["Attack", "Defence"]
    assert snapshot_rows[0]["xp"] == 101_333


def test_save_player_hiscore_snapshot_stores_activity_rows(
    db_session,
    sample_player_hiscores,
):
    """Verify saving a snapshot stores activity dimension and snapshot rows.

    Args:
        db_session (Session): Isolated database session.
        sample_player_hiscores (PlayerHiscores): Sample hiscore data to save.
    """

    fetch_id = save_player_hiscore_snapshot(db_session, sample_player_hiscores)

    activity_count = db_session.execute(
        text("select count(*) from activities")
    ).scalar_one()
    snapshot_row = (
        db_session.execute(
            text("""
            select a.name, pas.rank, pas.score
            from player_activity_snapshots pas
            join activities a on a.id = pas.activity_id
            where pas.fetch_id = :fetch_id
            """),
            {"fetch_id": fetch_id},
        )
        .mappings()
        .one()
    )

    assert activity_count == 1
    assert snapshot_row["name"] == "Bounty Hunter"
    assert snapshot_row["score"] == 25


def test_save_player_hiscore_snapshot_reuses_dimensions(
    db_session,
    sample_player_hiscores,
    later_player_hiscores,
):
    """Verify repeated snapshots reuse skill and activity dimensions.

    Args:
        db_session (Session): Isolated database session.
        sample_player_hiscores (PlayerHiscores): First sample hiscore snapshot.
        later_player_hiscores (PlayerHiscores): Later sample hiscore snapshot.
    """

    save_player_hiscore_snapshot(db_session, sample_player_hiscores)
    save_player_hiscore_snapshot(db_session, later_player_hiscores)

    skill_count = db_session.execute(text("select count(*) from skills")).scalar_one()
    activity_count = db_session.execute(
        text("select count(*) from activities")
    ).scalar_one()
    fetch_count = db_session.execute(text("select count(*) from fetches")).scalar_one()

    assert skill_count == 2
    assert activity_count == 1
    assert fetch_count == 2


def test_get_player_stat_changes_calculates_skill_deltas(
    db_session,
    sample_player_hiscores,
    later_player_hiscores,
):
    """Verify stored skill snapshots produce earliest-to-latest deltas.

    Args:
        db_session (Session): Isolated database session.
        sample_player_hiscores (PlayerHiscores): First sample hiscore snapshot.
        later_player_hiscores (PlayerHiscores): Later sample hiscore snapshot.
    """

    save_player_hiscore_snapshot(db_session, sample_player_hiscores)
    save_player_hiscore_snapshot(db_session, later_player_hiscores)

    stat_changes = get_player_stat_changes(db_session, "Zezt", "24h", "1 day")

    assert stat_changes is not None
    attack = next(skill for skill in stat_changes.skills if skill.name == "Attack")
    assert attack.earliest_rank == 100
    assert attack.latest_rank == 90
    assert attack.rank_delta == -10
    assert attack.earliest_level == 50
    assert attack.latest_level == 51
    assert attack.level_delta == 1
    assert attack.earliest_xp == 101_333
    assert attack.latest_xp == 112_333
    assert attack.xp_delta == 11_000


def test_get_player_stat_changes_calculates_activity_deltas(
    db_session,
    sample_player_hiscores,
    later_player_hiscores,
):
    """Verify stored activity snapshots produce earliest-to-latest deltas.

    Args:
        db_session (Session): Isolated database session.
        sample_player_hiscores (PlayerHiscores): First sample hiscore snapshot.
        later_player_hiscores (PlayerHiscores): Later sample hiscore snapshot.
    """

    save_player_hiscore_snapshot(db_session, sample_player_hiscores)
    save_player_hiscore_snapshot(db_session, later_player_hiscores)

    stat_changes = get_player_stat_changes(db_session, "Zezt", "24h", "1 day")

    assert stat_changes is not None
    activity = stat_changes.activities[0]
    assert activity.name == "Bounty Hunter"
    assert activity.earliest_rank == 10
    assert activity.latest_rank == 8
    assert activity.rank_delta == -2
    assert activity.earliest_score == 25
    assert activity.latest_score == 30
    assert activity.score_delta == 5


def test_get_player_stat_changes_returns_none_for_missing_stored_player(db_session):
    """Verify stat changes return None when the player has no snapshots.

    Args:
        db_session (Session): Isolated database session.
    """

    stat_changes = get_player_stat_changes(db_session, "Unknown", "24h", "1 day")

    assert stat_changes is None
