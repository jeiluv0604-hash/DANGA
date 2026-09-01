#!/bin/sh
# Best-effort schema migration + synthetic seed. If either step fails (or this
# entrypoint is bypassed by a platform that auto-detects a plain Python service),
# the FastAPI lifespan hook in apps/api/main.py performs the same bootstrap on
# startup, so the API still comes up with data.
python -m alembic upgrade head || echo "entrypoint: alembic upgrade failed; app will self-bootstrap"
python scripts/seed.py || echo "entrypoint: seed failed; app will self-bootstrap"

exec python -m uvicorn apps.api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
