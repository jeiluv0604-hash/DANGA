# -*- coding: utf-8 -*-
import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from apps.api.config import settings
from apps.api.logger import log_event
from apps.api.routes import health, ingestion, operations, facts, alerts, dashboard, evidence, analyst, rules, imports, mappings, management

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="DAMGA-OPS Deterministic Facts Engine & Rule Storage Backend API"
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
