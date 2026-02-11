# ── Build stage: install dependencies ────────────────────────────────────────
FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies first (cache-friendly layer ordering)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code and install the project itself
COPY . .
RUN uv sync --frozen --no-dev

# ── Runtime stage: slim final image ─────────────────────────────────────────
FROM python:3.13-slim AS runtime

WORKDIR /app

# Copy the virtual environment and app code from builder
COPY --from=builder /app /app

# Place the venv's bin dir on PATH so `uvicorn` and `alembic` are available
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
