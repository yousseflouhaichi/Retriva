# Production image for FastAPI (api) and ARQ (worker). Build on the target arch (e.g. Oracle ARM).
FROM python:3.13-slim-bookworm

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-group dev

COPY backend ./backend/

ENV PYTHONPATH=/app
ENV PATH="/app/.venv/bin:$PATH"

# Default command: API (override in Compose for worker)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
