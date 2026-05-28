# RunePy

A small RuneScape API client project.

The project fetches player hiscores from RuneScape's hiscore API and stores them in a Postgres db. Then stats are available for presentation with a Next.js frontend.

## TO-DO
- 26-5-28 - Currently WIP. Broad tasks in-order
  - Clean-up docstrings across project so far
  - Build/review test plan for backend + plan out TDD workflow
  - Write tests for backend + fix found bugs
  - Expand CI/CD for container deployment
  - Enforce TDD workflow and git feature branch workflow
  - Set-up/integrate TypeScript+Next.JS frontend into devcontainer
  - Build frontend dev requirements
  - Build frontend (use gen AI for rapid prototyping)
  - Build deployment docker container
  - Build/deploy hosting server with cloudflare
  - Deploy using Kubernetes-lite service (coolify, etc.)


## Info
DB schema to handle fetch from RuneScape
<img width="1673" height="544" alt="image" src="https://github.com/user-attachments/assets/67ebb983-f479-42ad-87bd-150a33d134e8" />


## Development
This project usees VSCode's devcontainers to seemlessly init a dev environment with minimal setup.


## Deploy
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
