"""
Repository layer — the only module that talks to the database.
All SQL lives here. Routes never see SQL.
"""

import os
import psycopg2
import psycopg2.extras
from typing import Optional

# Seed tasks — inserted only on first run
SEED_TASKS = [
    {"title": "Buy groceries", "done": False},
    {"title": "Read a book", "done": False},
    {"title": "Go for a walk", "done": True},
]


def _get_conn():
    """Return a connection with RealDictCursor so rows come back as dicts."""
    return psycopg2.connect(
        os.environ["DATABASE_URL"],
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def init_db() -> None:
    """
    Create tasks table if missing.
    Seed three tasks only if the table is empty (idempotent).
    """
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id    SERIAL PRIMARY KEY,
                    title TEXT   NOT NULL,
                    done  BOOLEAN NOT NULL DEFAULT FALSE
                )
                """
            )
            cur.execute("SELECT COUNT(*) AS count FROM tasks")
            count = cur.fetchone()["count"]
            if count == 0:
                cur.executemany(
                    "INSERT INTO tasks (title, done) VALUES (%s, %s)",
                    [(t["title"], t["done"]) for t in SEED_TASKS],
                )
            conn.commit()


# ---------------------------------------------------------------------------
# CRUD operations — all use parameterized queries (%s placeholders)
# ---------------------------------------------------------------------------

def list_tasks(search: Optional[str] = None, done: Optional[bool] = None) -> list[dict]:
    query = "SELECT id, title, done FROM tasks WHERE TRUE"
    params: list = []

    if search is not None:
        query += " AND title ILIKE %s"
        params.append(f"%{search}%")

    if done is not None:
        query += " AND done = %s"
        params.append(done)

    query += " ORDER BY id"

    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return [dict(r) for r in cur.fetchall()]


def get_task(task_id: int) -> Optional[dict]:
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, title, done FROM tasks WHERE id = %s",
                (task_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None


def create_task(title: str) -> dict:
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id, title, done",
                (title, False),
            )
            conn.commit()
            return dict(cur.fetchone())


def update_task(task_id: int, title: Optional[str], done: Optional[bool]) -> Optional[dict]:
    existing = get_task(task_id)
    if existing is None:
        return None

    new_title = title if title is not None else existing["title"]
    new_done = done if done is not None else existing["done"]

    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING id, title, done",
                (new_title, new_done, task_id),
            )
            conn.commit()
            return dict(cur.fetchone())


def delete_task(task_id: int) -> bool:
    existing = get_task(task_id)
    if existing is None:
        return False

    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            conn.commit()
    return True


def stats() -> dict:
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM tasks")
            total = cur.fetchone()["total"]
            cur.execute("SELECT COUNT(*) AS completed FROM tasks WHERE done = TRUE")
            completed = cur.fetchone()["completed"]
    return {"total": total, "completed": completed, "pending": total - completed}
