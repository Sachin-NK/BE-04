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
