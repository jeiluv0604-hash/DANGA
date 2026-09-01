#!/bin/sh
set -e

# Apply non-destructive schema migrations, then seed the synthetic Golden Dataset
# (idempotent: skipped automatically when the dataset SHA-256 is unchanged).
python -m alembic upgrade head
python scripts/seed.py

exec python -m uvicorn apps.api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
