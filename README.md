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

---

## Stage 6: AI rematch

### The prompt I wrote

```
You are a Python backend developer. Build a FastAPI CRUD API for tasks using
Python and psycopg2 connected to a PostgreSQL database. The database runs in
Docker. Requirements:
- Five endpoints: GET /tasks, GET /tasks/{id}, POST /tasks, PUT /tasks/{id},
  DELETE /tasks/{id}
- Tasks table: id (serial primary key), title (text), done (boolean)
- Seed three example tasks only if the table is empty on startup
- Read the database password from a DATABASE_URL environment variable in a
  .env file — never hardcode credentials
- Use parameterized queries (%s placeholders), never string interpolation
- POST returns 201, DELETE returns 204, unknown id returns 404, blank title
  returns 400
- A named Docker volume must persist data across container restarts
- docker compose up starts both the app and the database
Write main.py, docker-compose.yml, Dockerfile, and .env.example.
```

### What the AI got right

- Correct table schema and seed-once logic.
- Parameterized queries throughout — no string interpolation.
- Volume defined in compose, so data persists.
- Status codes correct: 201 on POST, 204 on DELETE, 404 on unknown id, 400 on blank title.
- Reads `DATABASE_URL` from environment, not hardcoded.

### What the AI got wrong or missed

1. **No healthcheck on the db service.** The `depends_on` just waits for the container to start, not for Postgres to be ready to accept connections. The app will crash on startup if it connects before Postgres is ready. My version uses `condition: service_healthy` with `pg_isready`.

2. **Credentials hardcoded in docker-compose.yml.** The AI put `POSTGRES_PASSWORD: taskpass` directly in the compose file instead of reading from `.env` with `env_file: .env`. Anyone reading the compose file sees the password.

3. **Requirements not pinned.** `fastapi`, `uvicorn`, `psycopg2-binary`, `python-dotenv` with no version numbers. Unpinned deps break silently months later when a new version ships.

4. **PUT accepts a blank title silently.** The AI's `update_task` does not validate `body.title.strip()` — a PUT with `{"title": "   "}` updates the task to a blank title with no error.

5. **`TaskIn` model used for PUT.** The AI reused the same model for create and update, so `done` defaults to `False` on PUT. A PUT with only `{"title": "New title"}` silently resets `done` to False. My version uses a separate `TaskUpdate` model with all optional fields.

### What my prompt missed

I didn't specify that PUT should use a partial update model (all fields optional). The AI's choice to reuse the create model for updates was a reasonable response to an underspecified prompt — and it caused a real bug.

### One rematch

Added to the prompt: "PUT should accept partial updates — title and done are both optional. Only update the fields provided."

On the second run the AI produced a separate `TaskUpdate` model with `Optional` fields and merged them with the existing values before writing — matching what my hand-built version does.

### The lesson

The AI's output was exactly as good as the specification. The healthcheck gap and the credential leak came from things I didn't name in the prompt. The partial-update bug came from a vague requirement. I could only spot all three because I had already built the correct version by hand.
