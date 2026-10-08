import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

import repository

app = FastAPI(
    title="Task API",
    description="CRUD API backed by Postgres running in Docker.",
    version="3.0.0",
)

repository.init_db()

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class TaskCreate(BaseModel):
    title: str


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None


# ---------------------------------------------------------------------------
# Stage 2: Read endpoints
# ---------------------------------------------------------------------------

@app.get(
    "/tasks",
    summary="List all tasks",
    description="Returns all tasks. Supports ?search= and ?done= filters.",
)
def list_tasks(search: Optional[str] = None, done: Optional[bool] = None):
    return repository.list_tasks(search=search, done=done)


@app.get(
    "/tasks/{task_id}",
    summary="Get a single task",
    description="Returns the task with the given id. 404 if not found.",
)
def get_task(task_id: int):
    task = repository.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


# ---------------------------------------------------------------------------
# Stage 3: Create, update, delete
# ---------------------------------------------------------------------------

@app.post(
    "/tasks",
    status_code=201,
    summary="Create a task",
    description="Creates a new task. 201 on success, 400 if title is blank.",
)
def create_task(body: TaskCreate):
    if not body.title.strip():
        raise HTTPException(status_code=400, detail="title is required and cannot be blank")
    return repository.create_task(body.title.strip())


@app.put(
    "/tasks/{task_id}",
    summary="Update a task",
    description="Updates title and/or done. 404 if not found, 400 if title is blank.",
)
def update_task(task_id: int, body: TaskUpdate):
    if body.title is not None and not body.title.strip():
        raise HTTPException(status_code=400, detail="title cannot be blank")

    title = body.title.strip() if body.title is not None else None
    task = repository.update_task(task_id, title=title, done=body.done)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.delete(
    "/tasks/{task_id}",
    status_code=204,
    summary="Delete a task",
    description="Deletes the task with the given id. 204 on success, 404 if not found.",
)
def delete_task(task_id: int):
    if not repository.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return None


@app.get(
    "/stats",
    summary="Task statistics",
    description="Returns total, completed, and pending task counts.",
)
def get_stats():
    return repository.stats()
