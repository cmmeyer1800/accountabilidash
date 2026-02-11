# Accountabilidash — Backend

FastAPI backend with JWT authentication, PostgreSQL, SQLModel, and Alembic migrations.

## Prerequisites

- Python 3.13+
- [UV](https://docs.astral.sh/uv/) package manager
- PostgreSQL (running locally or via Docker)

## Quick Start

```bash
# 1. Install dependencies
uv sync

# 2. Copy and edit environment variables
cp .env.example .env

# 3. Create the database
createdb accountabilidash   # or use psql / Docker

# 4. Run migrations
uv run alembic upgrade head

# 5. Start the dev server
uv run uvicorn app.main:app --reload
```

The API docs are available at **http://localhost:8000/docs** (Swagger) and **http://localhost:8000/redoc** (ReDoc).

## Project Structure

```
backend/
├── alembic/               # Alembic migration environment
│   ├── versions/          # Auto-generated migration scripts
│   └── env.py             # Alembic env (reads from app settings)
├── app/
│   ├── core/              # Settings, logging, database, security, deps
│   ├── middleware/         # Custom ASGI middleware
│   ├── models/            # SQLModel table definitions
│   ├── routers/           # FastAPI route handlers
│   ├── schemas/           # Pydantic request / response models
│   ├── services/          # Business logic layer
│   └── main.py            # Application factory & lifespan
├── alembic.ini
├── pyproject.toml
└── .env.example
```

## Common Commands

```bash
# Run the dev server
uv run uvicorn app.main:app --reload

# Create a new migration after model changes
uv run alembic revision --autogenerate -m "describe the change"

# Apply migrations
uv run alembic upgrade head

# Lint
uv run ruff check app/

# Run tests
uv run pytest
```
