# -*- coding: utf-8 -*-
import os

files = {}

# 1. Structured Logging Module
files['apps/api/logger.py'] = """# -*- coding: utf-8 -*-
import datetime
import json
import logging
import sys

logger = logging.getLogger("damga_ops")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)

def log_event(event: str, level: str = "INFO", **kwargs):
    payload = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "level": level.upper(),
        "event": event,
        **kwargs
    }
    msg = json.dumps(payload, ensure_ascii=False)
    if level.upper() == "ERROR":
        logger.error(msg)
    elif level.upper() == "WARNING":
        logger.warning(msg)
    else:
        logger.info(msg)
"""

# 2. Updated Schemas
files['apps/api/schemas/dashboard.py'] = """# -*- coding: utf-8 -*-
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from apps.api.schemas.alerts import AlertSchema

class DashboardKPISchema(BaseModel):
    sales: Optional[float] = None
    guests: Optional[int] = None
    avg_check: Optional[float] = None
    labor_cost: Optional[float] = None
    labor_ratio: Optional[float] = None
    food_cost: Optional[float] = None
    food_cost_ratio: Optional[float] = None
    contribution: Optional[float] = None
    contribution_ratio: Optional[float] = None
    inventory_variance_kg: Optional[float] = None
    waste_ratio: Optional[float] = None
    rating: Optional[float] = None
    complaints: Optional[int] = None

class KPICoverageItem(BaseModel):
    available_days: int
    total_days: int

class DailyDashboardResponse(BaseModel):
    date: str
    dataset_type: str = "SYNTHETIC"
    data_status: str = "OK"
    blocked: bool = False
    ai_eligible: bool = True
    kpis: DashboardKPISchema
    kpi_status: Optional[Dict[str, str]] = None
    alerts: List[AlertSchema] = []
    evidence_ids: List[str] = []

class DashboardSummaryResponse(BaseModel):
    start_date: str
    end_date: str
    dataset_type: str = "SYNTHETIC"
    total_days: int
    data_complete_days: int
    data_incomplete_days: int
    total_sales: float
    average_daily_sales: float
    average_labor_ratio: Optional[float]
    average_food_cost_ratio: Optional[float]
    total_contribution: float
    average_contribution_ratio: Optional[float]
    critical_alert_count: int
    high_alert_count: int
    medium_alert_count: int
    coverage: Dict[str, KPICoverageItem]
"""

# 3. Evidence Schema
files['apps/api/schemas/evidence.py'] = """# -*- coding: utf-8 -*-
import datetime
from typing import Optional
from pydantic import BaseModel

class EvidenceIndexResponse(BaseModel):
    evidence_id: str
    evidence_type: str
    business_date: Optional[str] = None
    rule_id: Optional[str] = None
    file_path: str
    file_sha256: str
    dataset_sha256: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True
"""

# 4. Ingestion Service with Evidence Linkage & Partial Facts
files['apps/api/services/ingestion_service.py'] = """# -*- coding: utf-8 -*-
import datetime
import hashlib
import json
import uuid
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session

from apps.api.models.ingestion import IngestionRun
from apps.api.models.operations import DailyOperation
from apps.api.models.facts import DailyFact
from apps.api.models.alerts import Alert, PeriodAlert
from apps.api.models.evidence import EvidenceIndex
from apps.api.repositories.ingestion_repository import IngestionRepository
from apps.api.repositories.operations_repository import OperationsRepository
from apps.api.repositories.facts_repository import FactsRepository
from apps.api.repositories.alerts_repository import AlertsRepository
from apps.api.logger import log_event
from domains.pipeline import process_daily_record, excel_serial_to_date_str
from domains.rules import detect_food_cost_streak, detect_profit_reversal

class IngestionService:
    def __init__(self, db: Session):
        self.db = db
        self.ingestion_repo = IngestionRepository(db)
        self.ops_repo = OperationsRepository(db)
        self.facts_repo = FactsRepository(db)
        self.alerts_repo = AlertsRepository(db)

    def ingest_synthetic_dataset(self, file_path: str, dataset_type: str = "SYNTHETIC") -> Dict[str, Any]:
        log_event("INGESTION_STARTED", level="INFO", file_path=file_path, dataset_type=dataset_type)
        with open(file_path, "rb") as f:
            content_bytes = f.read()
        source_sha256 = hashlib.sha256(content_bytes).hexdigest()

        # 1. Idempotency Check
        existing = self.ingestion_repo.get_by_sha256(source_sha256)
        if existing:
            log_event("INGESTION_ALREADY_EXISTS", level="INFO", ingestion_id=existing.ingestion_id, source_sha256=source_sha256)
            return {
                "status": "ALREADY_INGESTED",
                "ingestion_id": existing.ingestion_id,
                "dataset_type": existing.dataset_type,
                "source_sha256": existing.source_sha256,
                "row_count": existing.row_count,
                "valid_row_count": existing.valid_row_count,
                "blocked_row_count": existing.blocked_row_count,
                "alerts_count": 0,
                "period_alerts_count": 0
            }

        # 2. Parse JSON
        raw_json = json.loads(content_bytes.decode("utf-8"))
        header = raw_json["Daily_Operations"][0]
        raw_rows = [dict(zip(header, r)) for r in raw_json["Daily_Operations"][1:]]

        ingestion_id = f"INGEST-{uuid.uuid4().hex[:12].upper()}"
        run_record = IngestionRun(
            ingestion_id=ingestion_id,
            started_at=datetime.datetime.utcnow(),
            source_type="JSON",
            source_filename=file_path,
            source_sha256=source_sha256,
            dataset_type=dataset_type,
            status="IN_PROGRESS",
            row_count=len(raw_rows),
            valid_row_count=0,
            blocked_row_count=0,
            error_count=0
        )
        self.ingestion_repo.create(run_record)

        # 3. Process Rows through Domain Pipeline
        ops_models = []
        facts_models = []
        alert_models = []
        evidence_models = []
        pipeline_results = []

        valid_count = 0
        blocked_count = 0
        prev_end = 0.0

        for idx, row in enumerate(raw_rows):
            raw_date = row.get("Date", "")
            b_date = excel_serial_to_date_str(raw_date)

            def to_f(v):
                try: return float(v) if v not in (None, "") else None
                except: return None
            def to_i(v):
                try: return int(v) if v not in (None, "") else None
                except: return None

            op_model = DailyOperation(
                business_date=b_date,
                raw_date=str(raw_date),
                sales=to_f(row.get("Sales")),
                guests=to_i(row.get("Guests")),
                labor_cost=to_f(row.get("Labor_Cost")),
                food_cost=to_f(row.get("Food_Cost")),
                incoming_kg=to_f(row.get("Incoming_kg")),
                sold_kg=to_f(row.get("Sold_kg")),
                service_kg=to_f(row.get("Service_kg")),
                waste_kg=to_f(row.get("Waste_kg")),
                actual_end_kg=to_f(row.get("Actual_End_kg")),
                theory_end_kg=to_f(row.get("Theory_End_kg")),
                rating=to_f(row.get("Rating")),
                review_count=to_i(row.get("Review_Count")),
                complaints=to_i(row.get("Complaints")),
                dataset_type=dataset_type,
                ingestion_id=ingestion_id,
                source_row=idx + 1
            )
            ops_models.append(op_model)

            res = process_daily_record(row, prev_actual_end_kg=prev_end)
            pipeline_results.append(res)

            if res["data_status"] == "OK":
                valid_count += 1
            else:
                blocked_count += 1
                log_event("DATA_QUALITY_BLOCKED", level="WARNING", business_date=b_date, missing_fields=res.get("missing_fields"))

            f = res.get("facts", {})
            if f.get("actual_end_kg") is not None:
                prev_end = f.get("actual_end_kg", 0.0)

            fact_model = DailyFact(
                business_date=b_date,
                sales=f.get("sales"),
                guests=f.get("guests"),
                avg_check=f.get("avg_check"),
                labor_cost=f.get("labor_cost"),
                labor_ratio=f.get("labor_ratio"),
                food_cost=f.get("food_cost"),
                food_cost_ratio=f.get("food_cost_ratio"),
                incoming_kg=f.get("incoming_kg"),
                sold_kg=f.get("sold_kg"),
                service_kg=f.get("service_kg"),
                waste_kg=f.get("waste_kg"),
                waste_ratio=f.get("waste_ratio"),
                theory_end_kg=f.get("theory_end_kg"),
                actual_end_kg=f.get("actual_end_kg"),
                variance_kg=f.get("variance_kg"),
                rating=f.get("rating"),
                review_count=f.get("review_count"),
                complaints=f.get("complaints"),
                contribution=f.get("contribution"),
                contribution_ratio=f.get("contribution_ratio"),
                data_status=res["data_status"],
                dataset_type=dataset_type,
                ingestion_id=ingestion_id
            )
            facts_models.append(fact_model)

            # Daily Alerts & Evidence Linkage
            for a in res.get("alerts", []):
                alert_id = f"ALT-{uuid.uuid4().hex[:10].upper()}"
                ev_id = f"EV-ALT-{uuid.uuid4().hex[:10].upper()}"
                act_val = json.dumps(a.get("actual"), ensure_ascii=False) if isinstance(a.get("actual"), (dict, list)) else str(a.get("actual"))
                thresh_val = str(a.get("threshold"))

                alert_model = Alert(
                    alert_id=alert_id,
                    business_date=b_date,
                    rule_id=a["rule_id"],
                    severity=a["severity"],
                    status=a.get("status", "ALERT"),
                    actual_value=act_val,
                    threshold_value=thresh_val,
                    comparison=a.get("comparison", ""),
                    dataset_type=dataset_type,
                    ingestion_id=ingestion_id,
                    evidence_id=ev_id
                )
                alert_models.append(alert_model)

                ev_model = EvidenceIndex(
                    evidence_id=ev_id,
                    evidence_type="DAILY_ALERT",
                    business_date=b_date,
                    rule_id=a["rule_id"],
                    file_path=f"evidence/{ev_id}.json",
                    file_sha256=source_sha256,
                    dataset_sha256=source_sha256
                )
                evidence_models.append(ev_model)
                log_event("RULE_TRIGGERED", level="INFO", rule_id=a["rule_id"], business_date=b_date, severity=a["severity"], evidence_id=ev_id)

        # 4. Period Rules & Evidence Linkage
        period_models = []
        fc_streaks = detect_food_cost_streak(pipeline_results, threshold=0.39, min_consecutive_days=7)
        for s in fc_streaks:
            p_alt_id = f"PALT-{uuid.uuid4().hex[:10].upper()}"
            ev_id = f"EV-PALT-{uuid.uuid4().hex[:10].upper()}"
            period_models.append(PeriodAlert(
                alert_id=p_alt_id,
                rule_id=s["rule_id"],
                severity=s["severity"],
                target_start=s["start_date"],
                target_end=s["end_date"],
                metric_name="food_cost_ratio",
                target_value=s["actual"]["avg_ratio"],
                comparison=s["comparison"],
                dataset_type=dataset_type,
                ingestion_id=ingestion_id,
                evidence_id=ev_id
            ))
            evidence_models.append(EvidenceIndex(
                evidence_id=ev_id,
                evidence_type="PERIOD_ALERT",
                business_date=s["start_date"],
                rule_id=s["rule_id"],
                file_path=f"evidence/{ev_id}.json",
                file_sha256=source_sha256,
                dataset_sha256=source_sha256
            ))
            log_event("RULE_TRIGGERED", level="INFO", rule_id=s["rule_id"], period=f"{s['start_date']}~{s['end_date']}", evidence_id=ev_id)

        p_reversals = detect_profit_reversal(pipeline_results, window_days=7)
        for pr in p_reversals:
            p_alt_id = f"PALT-{uuid.uuid4().hex[:10].upper()}"
            ev_id = f"EV-PALT-{uuid.uuid4().hex[:10].upper()}"
            period_models.append(PeriodAlert(
                alert_id=p_alt_id,
                rule_id=pr["rule_id"],
                severity=pr["severity"],
                baseline_start=pr["baseline_start"],
                baseline_end=pr["baseline_end"],
                target_start=pr["target_start"],
                target_end=pr["target_end"],
                metric_name="contribution_ratio",
                baseline_value=pr["actual"]["baseline_contribution_ratio"],
                target_value=pr["actual"]["target_contribution_ratio"],
                comparison=pr["comparison"],
                dataset_type=dataset_type,
                ingestion_id=ingestion_id,
                evidence_id=ev_id
            ))
            evidence_models.append(EvidenceIndex(
                evidence_id=ev_id,
                evidence_type="PERIOD_ALERT",
                business_date=pr["target_start"],
                rule_id=pr["rule_id"],
                file_path=f"evidence/{ev_id}.json",
                file_sha256=source_sha256,
                dataset_sha256=source_sha256
            ))
            log_event("RULE_TRIGGERED", level="INFO", rule_id=pr["rule_id"], period=f"{pr['target_start']}~{pr['target_end']}", evidence_id=ev_id)

        # 5. Persist Everything in DB Transaction
        self.ops_repo.create_batch(ops_models)
        self.facts_repo.create_batch(facts_models)
        self.alerts_repo.create_alerts(alert_models)
        self.alerts_repo.create_period_alerts(period_models)
        self.db.add_all(evidence_models)

        run_record.valid_row_count = valid_count
        run_record.blocked_row_count = blocked_count
        run_record.status = "COMPLETED"
        run_record.completed_at = datetime.datetime.utcnow()

        self.db.commit()
        log_event("INGESTION_COMPLETED", level="INFO", ingestion_id=ingestion_id, row_count=len(raw_rows), valid_rows=valid_count, blocked_rows=blocked_count)

        return {
            "status": "COMPLETED",
            "ingestion_id": ingestion_id,
            "dataset_type": dataset_type,
            "source_sha256": source_sha256,
            "row_count": len(raw_rows),
            "valid_row_count": valid_count,
            "blocked_row_count": blocked_count,
            "alerts_count": len(alert_models),
            "period_alerts_count": len(period_models)
        }
"""

# 5. Updated Dashboard Service with Coverage & KPI Status
files['apps/api/services/dashboard_service.py'] = """# -*- coding: utf-8 -*-
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from apps.api.repositories.facts_repository import FactsRepository
from apps.api.repositories.alerts_repository import AlertsRepository
from apps.api.schemas.dashboard import DailyDashboardResponse, DashboardKPISchema, DashboardSummaryResponse, KPICoverageItem
from apps.api.schemas.alerts import AlertSchema

class DashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.facts_repo = FactsRepository(db)
        self.alerts_repo = AlertsRepository(db)

    def get_daily_dashboard(self, business_date: str) -> Optional[DailyDashboardResponse]:
        fact = self.facts_repo.get_by_date(business_date)
        if not fact:
            return None

        alerts = self.alerts_repo.get_by_date(business_date)
        alert_schemas = [AlertSchema.model_validate(a) for a in alerts]
        evidence_ids = [a.evidence_id for a in alerts if a.evidence_id]

        kpi_schema = DashboardKPISchema(
            sales=fact.sales,
            guests=fact.guests,
            avg_check=fact.avg_check,
            labor_cost=fact.labor_cost,
            labor_ratio=fact.labor_ratio,
            food_cost=fact.food_cost,
            food_cost_ratio=fact.food_cost_ratio,
            contribution=fact.contribution,
            contribution_ratio=fact.contribution_ratio,
            inventory_variance_kg=fact.variance_kg,
            waste_ratio=fact.waste_ratio,
            rating=fact.rating,
            complaints=fact.complaints
        )

        kpi_status = {
            "sales": "AVAILABLE" if fact.sales is not None else "MISSING_INPUT",
            "guests": "AVAILABLE" if fact.guests is not None else "MISSING_INPUT",
            "avg_check": "AVAILABLE" if fact.avg_check is not None else "BLOCKED_DEPENDENCY",
            "labor_cost": "AVAILABLE" if fact.labor_cost is not None else "MISSING_INPUT",
            "labor_ratio": "AVAILABLE" if fact.labor_ratio is not None else "BLOCKED_DEPENDENCY",
            "food_cost": "AVAILABLE" if fact.food_cost is not None else "MISSING_INPUT",
            "food_cost_ratio": "AVAILABLE" if fact.food_cost_ratio is not None else "BLOCKED_DEPENDENCY",
            "contribution": "AVAILABLE" if fact.contribution is not None else "BLOCKED_DEPENDENCY",
            "contribution_ratio": "AVAILABLE" if fact.contribution_ratio is not None else "BLOCKED_DEPENDENCY",
            "inventory_variance": "AVAILABLE" if fact.variance_kg is not None else "BLOCKED_DEPENDENCY",
            "waste_ratio": "AVAILABLE" if fact.waste_ratio is not None else "BLOCKED_DEPENDENCY",
            "rating": "AVAILABLE" if fact.rating is not None else "NOT_PROVIDED",
            "complaints": "AVAILABLE" if fact.complaints is not None else "NOT_PROVIDED"
        }

        is_blocked = (fact.data_status == "DATA_INCOMPLETE")

        return DailyDashboardResponse(
            date=fact.business_date,
            dataset_type=fact.dataset_type,
            data_status=fact.data_status,
            blocked=is_blocked,
            ai_eligible=not is_blocked,
            kpis=kpi_schema,
            kpi_status=kpi_status,
            alerts=alert_schemas,
            evidence_ids=evidence_ids
        )

    def get_dashboard_summary(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> DashboardSummaryResponse:
        facts = self.facts_repo.list_facts(start_date=start_date, end_date=end_date)
        if not facts:
            return DashboardSummaryResponse(
                start_date=start_date or "",
                end_date=end_date or "",
                dataset_type="SYNTHETIC",
                total_days=0,
                data_complete_days=0,
                data_incomplete_days=0,
                total_sales=0.0,
                average_daily_sales=0.0,
                average_labor_ratio=None,
                average_food_cost_ratio=None,
                total_contribution=0.0,
                average_contribution_ratio=None,
                critical_alert_count=0,
                high_alert_count=0,
                medium_alert_count=0,
                coverage={}
            )

        total_days = len(facts)
        complete_days = len([f for f in facts if f.data_status == "OK"])
        incomplete_days = len([f for f in facts if f.data_status == "DATA_INCOMPLETE"])

        # Independent Observation Aggregations (Phase 2.1)
        sales_facts = [f for f in facts if f.sales is not None]
        tot_sales = sum(f.sales for f in sales_facts)
        avg_sales = tot_sales / len(sales_facts) if sales_facts else 0.0

        labor_facts = [f for f in facts if f.labor_ratio is not None]
        avg_labor_ratio = round(sum(f.labor_ratio for f in labor_facts) / len(labor_facts), 4) if labor_facts else None

        fc_facts = [f for f in facts if f.food_cost_ratio is not None]
        avg_fc_ratio = round(sum(f.food_cost_ratio for f in fc_facts) / len(fc_facts), 4) if fc_facts else None

        contrib_facts = [f for f in facts if f.contribution is not None]
        tot_contrib = sum(f.contribution for f in contrib_facts)
        contrib_sales_sum = sum(f.sales for f in contrib_facts if f.sales is not None)
        avg_contrib_ratio = round(tot_contrib / contrib_sales_sum, 4) if contrib_sales_sum > 0 else None

        # Alerts summary
        effective_start = start_date or facts[0].business_date
        effective_end = end_date or facts[-1].business_date
        alerts = self.alerts_repo.list_alerts(start_date=effective_start, end_date=effective_end)

        crit = len([a for a in alerts if a.severity == "CRITICAL"])
        high = len([a for a in alerts if a.severity == "HIGH"])
        med = len([a for a in alerts if a.severity == "MEDIUM"])

        coverage = {
            "sales": KPICoverageItem(available_days=len(sales_facts), total_days=total_days),
            "labor_ratio": KPICoverageItem(available_days=len(labor_facts), total_days=total_days),
            "food_cost_ratio": KPICoverageItem(available_days=len(fc_facts), total_days=total_days),
            "contribution_ratio": KPICoverageItem(available_days=len(contrib_facts), total_days=total_days)
        }

        return DashboardSummaryResponse(
            start_date=effective_start,
            end_date=effective_end,
            dataset_type="SYNTHETIC",
            total_days=total_days,
            data_complete_days=complete_days,
            data_incomplete_days=incomplete_days,
            total_sales=tot_sales,
            average_daily_sales=round(avg_sales, 2),
            average_labor_ratio=avg_labor_ratio,
            average_food_cost_ratio=avg_fc_ratio,
            total_contribution=tot_contrib,
            average_contribution_ratio=avg_contrib_ratio,
            critical_alert_count=crit,
            high_alert_count=high,
            medium_alert_count=med,
            coverage=coverage
        )
"""

# 6. Evidence Route
files['apps/api/routes/evidence.py'] = """# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from apps.api.dependencies import get_db
from apps.api.models.evidence import EvidenceIndex
from apps.api.schemas.evidence import EvidenceIndexResponse

router = APIRouter(prefix="/api/v1/evidence", tags=["Evidence"])

@router.get("/{evidence_id}", response_model=EvidenceIndexResponse)
def get_evidence(evidence_id: str, db: Session = Depends(get_db)):
    ev = db.query(EvidenceIndex).filter(EvidenceIndex.evidence_id == evidence_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail=f"Evidence not found: {evidence_id}")
    return ev
"""

# 7. Main Application with Middleware & Evidence Router
files['apps/api/main.py'] = """# -*- coding: utf-8 -*-
import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from apps.api.config import settings
from apps.api.database import engine, Base
from apps.api.logger import log_event
from apps.api.routes import health, ingestion, operations, facts, alerts, dashboard, evidence

Base.metadata.create_all(bind=engine)

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.api.main:app", host="0.0.0.0", port=8000, reload=True)
"""

for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

print(f"Successfully generated {len(files)} Phase 2.1 hardening files.")

