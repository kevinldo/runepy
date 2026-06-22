# RunePy

Backend service for tracking RuneScape hiscore changes over time.

## Project Highlights
- FastAPI backend with typed Pydantic response models
- Postgres schema for timestamped player snapshot history
- SQL-backed stat delta queries across multiple time windows
- External RuneScape API integration with error handling
- Pytest coverage for routes, services, client behavior, and persistence logic
- CI quality gates with Ruff, Black, and pytest

## What It Does
- Fetches live RuneScape hiscore data
- Stores player snapshots in Postgres
- Computes stat deltas across recent, 24h, 7d, 30d, 3m, 6m, and 1y windows
- Exposes a FastAPI API for current hiscores and historical changes

## Why?

I built RunePy to track my RuneScape progress over time instead of only seeing the current snapshot exposed by the official hiscores. During a play session, progress can be spread across skills and activities, so I wanted a backend that could ingest hiscore data, store timestamped snapshots, and show how my account changes across sessions, days, weeks, and months.

The project is backend-first: it focuses on reliable data ingestion, persistence, and stat-change queries that can later power richer dashboards or progress summaries.


## Data Model
DB schema to handle and store fetches from RuneScape
<img width="1900" height="615" alt="image" src="https://github.com/user-attachments/assets/7b6fc7b7-ec32-426c-a138-fbbcc1304457" />


## Development
This project uses VSCode's devcontainers to seamlessly init a dev environment with minimal setup.


## Run Locally
- VSCode
Install Dev Containers extension and open project as a container
- Run FastAPI backend
```Bash
uvicorn runepy.main:app --reload
```
- First time database migration to init schema
```Bash
psql "$DATABASE_URL" -f db/migrations/001_init_schema.sql
```


## Commands
- Fetch from RuneScape
```Bash
curl -X GET "http://127.0.0.1:8000/players/<PLAYER_NAME>/hiscores"
curl -X POST "http://127.0.0.1:8000/players/<PLAYER_NAME>/hiscores/snapshots"
```

- Fetch from RunePy
```Bash
curl -X GET "http://127.0.0.1:8000/players/<PLAYER_NAME>/stats/changes?window=recent"
curl -X GET "http://127.0.0.1:8000/players/<PLAYER_NAME>/stats/changes?window=24h"
curl -X GET "http://127.0.0.1:8000/players/<PLAYER_NAME>/stats/changes?window=7d"
curl -X GET "http://127.0.0.1:8000/players/<PLAYER_NAME>/stats/changes?window=30d"
```

- DB Backup
```Bash
docker exec -t runepy-db-1 pg_dump -U postgres -d runepy > "backup_$(date +%Y%m%d_%H%M%S).sql"  # Export
docker exec -i runepy-db-1 psql -U postgres -d runepy < <BACKUP_FILE_NAME>.sql  # Import
```


## Test

```bash
ruff check .
black --check .
pytest
```
