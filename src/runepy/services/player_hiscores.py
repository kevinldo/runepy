from runepy.clients.runescape import fetch_player_hiscores
from runepy.db.hiscore_snapshots import save_player_hiscore_snapshot
from runepy.db.session import SessionLocal
from runepy.models.hiscores import PlayerHiscores


async def fetch_and_store_player_hiscores(player_name: str) -> PlayerHiscores:
    hiscores = await fetch_player_hiscores(player_name)

    with SessionLocal() as session:
        with session.begin():
            save_player_hiscore_snapshot(session, hiscores)

    return hiscores
