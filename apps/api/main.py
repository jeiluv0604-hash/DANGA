# -*- coding: utf-8 -*-
import os
import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from apps.api.config import settings
from apps.api.logger import log_event
from apps.api.routes import health, ingestion, operations, facts, alerts, dashboard, evidence, analyst, rules, imports, mappings, management


def _bootstrap_database() -> None:
    """Make a fresh deployment self-sufficient.

    Ensures every table exists (non-destructive create_all — never drop_all) and
    seeds the synthetic Golden Dataset once when `daily_facts` is empty. This lets
    the API come up correctly even where the container entrypoint's
    `alembic upgrade head` / `scripts/seed.py` did not run (e.g. a platform that
    auto-detected a plain Python service instead of the Dockerfile).
    Disable with DAMGA_AUTO_SETUP=0.
    """
    if os.getenv("DAMGA_AUTO_SETUP", "1") != "1" or "PYTEST_CURRENT_TEST" in os.environ:
        return
    from apps.api.database import Base, engine, SessionLocal
    import apps.api.models  # noqa: F401 — registers all ORM models on Base.metadata
    from apps.api.models.facts import DailyFact

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        already_seeded = db.query(DailyFact).first() is not None
        if not already_seeded and os.path.exists(settings.SYNTHETIC_DATASET_PATH):
            from apps.api.services.ingestion_service import IngestionService
            result = IngestionService(db).ingest_synthetic_dataset(
                settings.SYNTHETIC_DATASET_PATH, dataset_type="SYNTHETIC"
            )
            log_event("STARTUP_SEED", level="INFO", status=result.get("status"))
    except Exception as exc:  # pragma: no cover - startup diagnostics only
        log_event("STARTUP_SEED_FAILED", level="ERROR", error=str(exc))
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    _bootstrap_database()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="DAMGA-OPS Deterministic Facts Engine & Rule Storage Backend API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def request_correlation_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID") or f"REQ-{uuid.uuid4().hex[:10].upper()}"
    request.state.request_id = req_id
    start_time = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = req_id
    log_event(
        "API_REQUEST_COMPLETED",
        level="INFO",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        request_id=req_id,
        duration_ms=duration_ms
    )
    return response

app.include_router(health.router)
app.include_router(ingestion.router)
app.include_router(operations.router)
app.include_router(facts.router)
app.include_router(alerts.router)
app.include_router(dashboard.router)
app.include_router(evidence.router)
app.include_router(analyst.router)
app.include_router(rules.router)
app.include_router(imports.router)
app.include_router(mappings.router)
app.include_router(management.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.api.main:app", host="0.0.0.0", port=8000, reload=True)
