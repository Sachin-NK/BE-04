"""
AI-generated version of the Task API.
Generated from the prompt below. Kept untouched for comparison.

PROMPT USED:
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
"""

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")

SEED_TASKS = [
    ("Buy groceries", False),
    ("Read a book", False),
    ("Go for a walk", True),
]


def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    done BOOLEAN NOT NULL DEFAULT FALSE
                )
            """)
            cur.execute("SELECT COUNT(*) as count FROM tasks")
            if cur.fetchone()["count"] == 0:
                cur.executemany(
                    "INSERT INTO tasks (title, done) VALUES (%s, %s)", SEED_TASKS
                )
            conn.commit()


init_db()


class TaskIn(BaseModel):
    title: str
    done: Optional[bool] = False


@app.get("/tasks")
def list_tasks():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM tasks ORDER BY id")
            return cur.fetchall()


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
            task = cur.fetchone()
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            return task


@app.post("/tasks", status_code=201)
def create_task(body: TaskIn):
    if not body.title or not body.title.strip():
        raise HTTPException(status_code=400, detail="title is required")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING *",
                (body.title.strip(), body.done),
            )
            conn.commit()
            return cur.fetchone()


@app.put("/tasks/{task_id}")
def update_task(task_id: int, body: TaskIn):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Task not found")
            cur.execute(
                "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING *",
                (body.title, body.done, task_id),
            )
            conn.commit()
            return cur.fetchone()


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Task not found")
            cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            conn.commit()
