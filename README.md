# TaskFlow API

A small task-management REST API built with Python, FastAPI, and SQLite. It demonstrates HTTP methods, request validation, parameterized SQL, persistence, error handling, and automated API tests.

## Features

- Create, list, retrieve, update, and delete tasks (CRUD)
- Filter tasks by completion status
- SQLite persistence
- Input validation and useful HTTP error codes
- Interactive OpenAPI documentation
- Automated tests with FastAPI's test client

## Requirements

Python 3.10 or newer.

## Run locally

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://127.0.0.1:8000/docs to try the endpoints. The SQLite database (`tasks.db`) is created automatically next to `main.py` on startup.

## Endpoints

| Method | Path | Purpose | Typical response |
|---|---|---|---|
| GET | `/health` | Health check | `200 OK` |
| POST | `/tasks` | Create a task | `201 Created` |
| GET | `/tasks` | List tasks; optional `?completed=true` filter | `200 OK` |
| GET | `/tasks/{task_id}` | Retrieve one task | `200 OK` or `404 Not Found` |
| PATCH | `/tasks/{task_id}` | Update provided fields | `200 OK`, `400`, or `404` |
| DELETE | `/tasks/{task_id}` | Delete a task | `204 No Content` or `404` |

### Example request

```bash
curl -X POST http://127.0.0.1:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Prepare for SDE interviews","description":"Practice arrays and hash maps"}'
```

## Run tests

```bash
pytest -q
```

Tests cover creation/retrieval, validation, updates and filtering, missing records, and deletion.

## Engineering notes

- SQL values are parameterized to avoid SQL injection through request data.
- Pydantic models validate request and response shapes.
- The API returns `404` when a requested task does not exist.
- This is a learning project, not a production deployment. Authentication, migrations, structured logging, pagination, and deployment configuration are intentionally out of scope.

## Resume wording (use only after you run and understand the project)

**TaskFlow — Task Management REST API | Python, FastAPI, SQLite, Pytest**
- Built a REST API supporting task creation, retrieval, updates, deletion, and completion-status filtering with FastAPI and SQLite.
- Added request validation, parameterized database queries, and HTTP error handling for invalid input and missing tasks.
- Wrote automated API tests covering CRUD workflows, validation, filtering, and not-found cases.
