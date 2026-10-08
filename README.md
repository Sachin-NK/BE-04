# Task API — Postgres + Docker

CRUD API for tasks. Third storage swap in the same project: memory (A1) → SQLite (A2) → containerized Postgres (this one). The routes never changed.

---

## One command to run everything

```bash
cp .env.example .env
docker compose up --build
```

API is live at [http://localhost:8000](http://localhost:8000)
Interactive docs at [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Environment variables

Copy `.env.example` to `.env`. Never commit `.env` — it is gitignored.

| Variable | Description |
|---|---|
| `DATABASE_URL` | Full Postgres connection string |
| `POSTGRES_USER` | Database user |
| `POSTGRES_PASSWORD` | Database password |
| `POSTGRES_DB` | Database name |

---

## API endpoints

| Method | Path | Status codes | Description |
|---|---|---|---|
| GET | /tasks | 200 | List all tasks. Supports `?search=` and `?done=` |
| GET | /tasks/{id} | 200, 404 | Get one task |
| POST | /tasks | 201, 400 | Create a task (title required, non-blank) |
| PUT | /tasks/{id} | 200, 400, 404 | Update title and/or done |
| DELETE | /tasks/{id} | 204, 404 | Delete a task |
| GET | /stats | 200 | Total, completed, pending counts |

---

## curl examples

```bash
# List all tasks
curl -i http://localhost:8000/tasks

# Get one task
curl -i http://localhost:8000/tasks/1

# Create a task
curl -i -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d "{\"title\": \"Buy milk\"}"

# Mark done
curl -i -X PUT http://localhost:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d "{\"done\": true}"

# Delete
curl -i -X DELETE http://localhost:8000/tasks/1

# Unknown id — expect 404
curl -i http://localhost:8000/tasks/999

# Blank title — expect 400
curl -i -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d "{\"title\": \"   \"}"
```

---

## Persistence proof

1. Start the stack: `docker compose up --build`
2. Create a task:
   ```bash
   curl -X POST http://localhost:8000/tasks \
     -H "Content-Type: application/json" \
     -d "{\"title\": \"Survive a restart\"}"
   ```
3. Stop everything: `docker compose down` (containers stop, volume stays)
4. Start again: `docker compose up`
5. Check: `curl http://localhost:8000/tasks`

The task is still there. Data lives in the `postgres_data` Docker volume — not in the container — so stopping and removing the container does not touch the data.

To wipe all data and start fresh:
```bash
docker compose down -v
```

---

## Architecture

```
Client
  |
  v
main.py          — routes + request validation only
  |
  v
repository.py    — all SQL lives here, nowhere else
  |
  v
Postgres         — running in Docker with a named volume
```

**What changed across storage swaps:**

| | A1 (memory) | A2 (SQLite) | A3 (Postgres) |
|---|---|---|---|
| Storage | Python list | `tasks.db` file | Postgres container |
| SQL | none | sqlite3 | psycopg2 |
| Routes | unchanged | unchanged | unchanged |
| Survives restart | no | yes | yes |
| Infrastructure | none | none | Docker + compose |

The routes are identical across all three. Storage is an implementation detail — only `repository.py` changes when storage changes.

---

## Database screenshot

Add a screenshot of `psql` or DBeaver showing the tasks table here before submitting.

```bash
# Open psql inside the running container
docker exec -it task7-db-1 psql -U taskuser -d taskdb

# Then run:
\dt
SELECT * FROM tasks;
```

---

## AI vs me

See Stage 6 below and the `ai-version/` folder.
