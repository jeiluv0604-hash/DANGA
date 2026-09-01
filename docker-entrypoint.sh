#!/bin/sh
# Schema + synthetic seed happen in the FastAPI lifespan hook (apps/api/main.py):
# it runs create_all (full current schema straight from the ORM models) and
# seeds the Golden Dataset when daily_facts is empty. We deliberately do NOT run
# `alembic upgrade` here — the migration chain only evolves an existing database
# and cannot build one from scratch. Operators of a persistent DB run alembic
# themselves.
exec python -m uvicorn apps.api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
