"""TaskFlow: a small, SQLite-backed task management REST API."""
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
import sqlite3
from typing import Literal

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

DB_PATH = Path(__file__).with_name("tasks.db")



@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()



def initialize_database() -> None:
    with get_connection() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                completed INTEGER NOT NULL DEFAULT 0 CHECK (completed IN (0, 1))
            )"""
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="TaskFlow API",
    description="A simple REST API for creating and managing tasks.",
    version="1.0.0",
    lifespan=lifespan,
)


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    completed: bool | None = None


class Task(BaseModel):
    id: int
    title: str
    description: str
    completed: bool


def serialize_task(row: sqlite3.Row) -> Task:
    return Task(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        completed=bool(row["completed"]),
    )


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED, tags=["tasks"])
def create_task(payload: TaskCreate) -> Task:
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=422, detail="Title cannot contain only whitespace")
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (title, description) VALUES (?, ?)",
            (title, payload.description.strip()),
        )
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return serialize_task(row)


@app.get("/tasks", response_model=list[Task], tags=["tasks"])
def list_tasks(completed: bool | None = None) -> list[Task]:
    query = "SELECT * FROM tasks"
    params: tuple[int, ...] = ()
    if completed is not None:
        query += " WHERE completed = ?"
        params = (int(completed),)
    query += " ORDER BY id"
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [serialize_task(row) for row in rows]


@app.get("/tasks/{task_id}", response_model=Task, tags=["tasks"])
def get_task(task_id: int) -> Task:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return serialize_task(row)


@app.patch("/tasks/{task_id}", response_model=Task, tags=["tasks"])
def update_task(task_id: int, payload: TaskUpdate) -> Task:
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="Provide at least one field to update")
    if "title" in changes:
        title = changes["title"].strip()
        if not title:
            raise HTTPException(status_code=422, detail="Title cannot contain only whitespace")
        changes["title"] = title
    if "description" in changes and changes["description"] is not None:
        changes["description"] = changes["description"].strip()

    columns = {"title": "title", "description": "description", "completed": "completed"}
    assignments = ", ".join(f"{columns[key]} = ?" for key in changes)
    values = [int(value) if key == "completed" and value is not None else value
              for key, value in changes.items()]
    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail="Task not found")
        conn.execute(f"UPDATE tasks SET {assignments} WHERE id = ?", (*values, task_id))
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return serialize_task(row)


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["tasks"])
def delete_task(task_id: int) -> None:
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found")
    return None
