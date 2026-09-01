# -*- coding: utf-8 -*-
import os

files = {}

# 1. Config
files['apps/api/config.py'] = """# -*- coding: utf-8 -*-
import os
from pydantic import BaseModel

class Settings(BaseModel):
    APP_NAME: str = "DAMGA-OPS API"
    APP_VERSION: str = "2.0.0-phase2"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///data/damga_ops.db")
    SYNTHETIC_DATASET_PATH: str = os.getenv("SYNTHETIC_DATASET_PATH", "data/synthetic/damga_dataset.json")
    DEFAULT_DATASET_TYPE: str = "SYNTHETIC"

settings = Settings()
"""

# 2. Database
files['apps/api/database.py'] = """# -*- coding: utf-8 -*-
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from apps.api.config import settings

os.makedirs("data", exist_ok=True)

connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
"""

# 3. Dependencies
files['apps/api/dependencies.py'] = """# -*- coding: utf-8 -*-
from apps.api.database import get_db

__all__ = ["get_db"]
"""

# 4. Models
files['apps/api/models/ingestion.py'] = """# -*- coding: utf-8 -*-
import datetime
from sqlalchemy import Column, Integer, String, DateTime
from apps.api.database import Base

class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id = Column(Integer, primary_key=True, index=True)
    ingestion_id = Column(String(64), unique=True, index=True, nullable=False)
    started_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    source_type = Column(String(32), default="JSON", nullable=False)
    source_filename = Column(String(255), nullable=False)
    source_sha256 = Column(String(64), index=True, nullable=False)
    dataset_type = Column(String(32), default="SYNTHETIC", nullable=False)
    status = Column(String(32), default="IN_PROGRESS", nullable=False)
    row_count = Column(Integer, default=0, nullable=False)
    valid_row_count = Column(Integer, default=0, nullable=False)
    blocked_row_count = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    code_version = Column(String(32), default="2.0.0-phase2", nullable=False)
"""

files['apps/api/models/operations.py'] = """# -*- coding: utf-8 -*-
import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime
from apps.api.database import Base

class DailyOperation(Base):
    __tablename__ = "daily_operations"

    id = Column(Integer, primary_key=True, index=True)
    business_date = Column(String(10), index=True, nullable=False)
    raw_date = Column(String(32), nullable=True)
    sales = Column(Float, nullable=True)
    guests = Column(Integer, nullable=True)
    labor_cost = Column(Float, nullable=True)
    food_cost = Column(Float, nullable=True)
    incoming_kg = Column(Float, nullable=True)
    sold_kg = Column(Float, nullable=True)
    service_kg = Column(Float, nullable=True)
    waste_kg = Column(Float, nullable=True)
    actual_end_kg = Column(Float, nullable=True)
    theory_end_kg = Column(Float, nullable=True)
    rating = Column(Float, nullable=True)
    review_count = Column(Integer, nullable=True)
    complaints = Column(Integer, nullable=True)

    dataset_type = Column(String(32), default="SYNTHETIC", nullable=False)
    ingestion_id = Column(String(64), index=True, nullable=False)
    source_row = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
"""

files['apps/api/models/facts.py'] = """# -*- coding: utf-8 -*-
import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime
from apps.api.database import Base

class DailyFact(Base):
    __tablename__ = "daily_facts"

    id = Column(Integer, primary_key=True, index=True)
    business_date = Column(String(10), index=True, nullable=False)
    
    sales = Column(Float, nullable=True)
    guests = Column(Integer, nullable=True)
    avg_check = Column(Float, nullable=True)

    labor_cost = Column(Float, nullable=True)
    labor_ratio = Column(Float, nullable=True)

    food_cost = Column(Float, nullable=True)
    food_cost_ratio = Column(Float, nullable=True)

    incoming_kg = Column(Float, nullable=True)
    sold_kg = Column(Float, nullable=True)
    service_kg = Column(Float, nullable=True)
    waste_kg = Column(Float, nullable=True)
    waste_ratio = Column(Float, nullable=True)

    theory_end_kg = Column(Float, nullable=True)
    actual_end_kg = Column(Float, nullable=True)
    variance_kg = Column(Float, nullable=True)

    rating = Column(Float, nullable=True)
    review_count = Column(Integer, nullable=True)
    complaints = Column(Integer, nullable=True)

    contribution = Column(Float, nullable=True)
    contribution_ratio = Column(Float, nullable=True)

    data_status = Column(String(32), default="OK", nullable=False)
    dataset_type = Column(String(32), default="SYNTHETIC", nullable=False)
    ingestion_id = Column(String(64), index=True, nullable=False)
    facts_version = Column(String(32), default="1.0.0", nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
"""

files['apps/api/models/alerts.py'] = """# -*- coding: utf-8 -*-
import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, JSON
from apps.api.database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(64), unique=True, index=True, nullable=False)
    business_date = Column(String(10), index=True, nullable=False)
    rule_id = Column(String(32), index=True, nullable=False)
    severity = Column(String(16), index=True, nullable=False)
    status = Column(String(32), default="ALERT", nullable=False)
    actual_value = Column(String(255), nullable=True)
    threshold_value = Column(String(255), nullable=True)
    comparison = Column(String(255), nullable=True)
    message_code = Column(String(64), nullable=True)

    dataset_type = Column(String(32), default="SYNTHETIC", nullable=False)
    ingestion_id = Column(String(64), index=True, nullable=False)
    evidence_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

class PeriodAlert(Base):
    __tablename__ = "period_alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(64), unique=True, index=True, nullable=False)
    rule_id = Column(String(32), index=True, nullable=False)
    severity = Column(String(16), index=True, nullable=False)
    baseline_start = Column(String(10), nullable=True)
    baseline_end = Column(String(10), nullable=True)
    target_start = Column(String(10), nullable=False)
    target_end = Column(String(10), nullable=False)
    metric_name = Column(String(64), nullable=True)
    baseline_value = Column(Float, nullable=True)
    target_value = Column(Float, nullable=True)
    comparison = Column(String(255), nullable=True)

    dataset_type = Column(String(32), default="SYNTHETIC", nullable=False)
    ingestion_id = Column(String(64), index=True, nullable=False)
    evidence_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
"""

files['apps/api/models/evidence.py'] = """# -*- coding: utf-8 -*-
import datetime
from sqlalchemy import Column, Integer, String, DateTime
from apps.api.database import Base

class EvidenceIndex(Base):
    __tablename__ = "evidence_index"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(String(64), unique=True, index=True, nullable=False)
    evidence_type = Column(String(32), nullable=False)
    business_date = Column(String(10), nullable=True)
    rule_id = Column(String(32), nullable=True)
    file_path = Column(String(255), nullable=False)
    file_sha256 = Column(String(64), nullable=False)
    dataset_sha256 = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
"""

files['apps/api/models/__init__.py'] = """# -*- coding: utf-8 -*-
from apps.api.database import Base
from apps.api.models.ingestion import IngestionRun
from apps.api.models.operations import DailyOperation
from apps.api.models.facts import DailyFact
from apps.api.models.alerts import Alert, PeriodAlert
from apps.api.models.evidence import EvidenceIndex

__all__ = [
    "Base",
    "IngestionRun",
    "DailyOperation",
    "DailyFact",
    "Alert",
    "PeriodAlert",
    "EvidenceIndex"
]
"""

# 5. Schemas
files['apps/api/schemas/ingestion.py'] = """# -*- coding: utf-8 -*-
import datetime
from typing import Optional, List
from pydantic import BaseModel

class IngestionRunResponse(BaseModel):
    ingestion_id: str
    started_at: datetime.datetime
    completed_at: Optional[datetime.datetime]
    source_type: str
    source_filename: str
    source_sha256: str
    dataset_type: str
    status: str
    row_count: int
    valid_row_count: int
    blocked_row_count: int
    error_count: int

    class Config:
        from_attributes = True

class IngestionResult(BaseModel):
    ingestion_id: str
    dataset_type: str
    status: str
    row_count: int
    valid_row_count: int
    blocked_row_count: int
    alerts_count: int
    period_alerts_count: int
    source_sha256: str
"""

files['apps/api/schemas/operations.py'] = """# -*- coding: utf-8 -*-
from typing import Optional
from pydantic import BaseModel

class DailyOperationSchema(BaseModel):
    business_date: str
    sales: Optional[float]
    guests: Optional[int]
    labor_cost: Optional[float]
    food_cost: Optional[float]
    incoming_kg: Optional[float]
    sold_kg: Optional[float]
    service_kg: Optional[float]
    waste_kg: Optional[float]
    actual_end_kg: Optional[float]
    theory_end_kg: Optional[float]
    rating: Optional[float]
    review_count: Optional[int]
    complaints: Optional[int]
    dataset_type: str
    ingestion_id: str

    class Config:
        from_attributes = True
"""

files['apps/api/schemas/facts.py'] = """# -*- coding: utf-8 -*-
from typing import Optional
from pydantic import BaseModel

class DailyFactSchema(BaseModel):
    business_date: str
    sales: Optional[float]
    guests: Optional[int]
    avg_check: Optional[float]
    labor_cost: Optional[float]
    labor_ratio: Optional[float]
    food_cost: Optional[float]
    food_cost_ratio: Optional[float]
    incoming_kg: Optional[float]
    sold_kg: Optional[float]
    service_kg: Optional[float]
    waste_kg: Optional[float]
    waste_ratio: Optional[float]
    theory_end_kg: Optional[float]
    actual_end_kg: Optional[float]
    variance_kg: Optional[float]
    rating: Optional[float]
    review_count: Optional[int]
    complaints: Optional[int]
    contribution: Optional[float]
    contribution_ratio: Optional[float]
    data_status: str
    dataset_type: str
    ingestion_id: str

    class Config:
        from_attributes = True
"""

files['apps/api/schemas/alerts.py'] = """# -*- coding: utf-8 -*-
from typing import Optional
from pydantic import BaseModel

class AlertSchema(BaseModel):
    alert_id: str
    business_date: str
    rule_id: str
    severity: str
    status: str
    actual_value: Optional[str]
    threshold_value: Optional[str]
    comparison: Optional[str]
    dataset_type: str
    ingestion_id: str
    evidence_id: Optional[str]

    class Config:
        from_attributes = True

class PeriodAlertSchema(BaseModel):
    alert_id: str
    rule_id: str
    severity: str
    baseline_start: Optional[str]
    baseline_end: Optional[str]
    target_start: str
    target_end: str
    metric_name: Optional[str]
    baseline_value: Optional[float]
    target_value: Optional[float]
    comparison: Optional[str]
    dataset_type: str
    ingestion_id: str
    evidence_id: Optional[str]

    class Config:
        from_attributes = True
"""

files['apps/api/schemas/dashboard.py'] = """# -*- coding: utf-8 -*-
import datetime
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

class DailyDashboardResponse(BaseModel):
    date: str
    dataset_type: str = "SYNTHETIC"
    data_status: str = "OK"
    kpis: DashboardKPISchema
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
"""

# 6. Repositories
files['apps/api/repositories/ingestion_repository.py'] = """# -*- coding: utf-8 -*-
from typing import Optional, List
from sqlalchemy.orm import Session
from apps.api.models.ingestion import IngestionRun

class IngestionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_sha256(self, sha256_hash: str) -> Optional[IngestionRun]:
        return self.db.query(IngestionRun).filter(IngestionRun.source_sha256 == sha256_hash, IngestionRun.status == "COMPLETED").first()

    def create(self, run: IngestionRun) -> IngestionRun:
        self.db.add(run)
        self.db.flush()
        return run

    def list_runs(self, limit: int = 50) -> List[IngestionRun]:
        return self.db.query(IngestionRun).order_by(IngestionRun.id.desc()).limit(limit).all()
"""

files['apps/api/repositories/operations_repository.py'] = """# -*- coding: utf-8 -*-
from typing import List, Optional
from sqlalchemy.orm import Session
from apps.api.models.operations import DailyOperation

class OperationsRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_batch(self, operations: List[DailyOperation]):
        self.db.add_all(operations)
        self.db.flush()

    def get_by_date(self, business_date: str) -> Optional[DailyOperation]:
        return self.db.query(DailyOperation).filter(DailyOperation.business_date == business_date).first()

    def list_operations(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[DailyOperation]:
        q = self.db.query(DailyOperation)
        if start_date:
            q = q.filter(DailyOperation.business_date >= start_date)
        if end_date:
            q = q.filter(DailyOperation.business_date <= end_date)
        return q.order_by(DailyOperation.business_date.asc()).all()
"""

files['apps/api/repositories/facts_repository.py'] = """# -*- coding: utf-8 -*-
from typing import List, Optional
from sqlalchemy.orm import Session
from apps.api.models.facts import DailyFact

class FactsRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_batch(self, facts: List[DailyFact]):
        self.db.add_all(facts)
        self.db.flush()

    def get_by_date(self, business_date: str) -> Optional[DailyFact]:
        return self.db.query(DailyFact).filter(DailyFact.business_date == business_date).first()

    def list_facts(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[DailyFact]:
        q = self.db.query(DailyFact)
        if start_date:
            q = q.filter(DailyFact.business_date >= start_date)
        if end_date:
            q = q.filter(DailyFact.business_date <= end_date)
        return q.order_by(DailyFact.business_date.asc()).all()
"""

files['apps/api/repositories/alerts_repository.py'] = """# -*- coding: utf-8 -*-
from typing import List, Optional
from sqlalchemy.orm import Session
from apps.api.models.alerts import Alert, PeriodAlert

class AlertsRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_alerts(self, alerts: List[Alert]):
        self.db.add_all(alerts)
        self.db.flush()

    def create_period_alerts(self, period_alerts: List[PeriodAlert]):
        self.db.add_all(period_alerts)
        self.db.flush()

    def get_by_date(self, business_date: str) -> List[Alert]:
        return self.db.query(Alert).filter(Alert.business_date == business_date).all()

    def list_alerts(self, start_date: Optional[str] = None, end_date: Optional[str] = None,
                    severity: Optional[str] = None, rule_id: Optional[str] = None) -> List[Alert]:
        q = self.db.query(Alert)
        if start_date:
            q = q.filter(Alert.business_date >= start_date)
        if end_date:
            q = q.filter(Alert.business_date <= end_date)
        if severity:
            q = q.filter(Alert.severity == severity.upper())
        if rule_id:
            q = q.filter(Alert.rule_id == rule_id.upper())
        return q.order_by(Alert.business_date.asc()).all()

    def list_period_alerts(self) -> List[PeriodAlert]:
        return self.db.query(PeriodAlert).order_by(PeriodAlert.target_start.asc()).all()
"""

# 7. Services
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
        with open(file_path, "rb") as f:
            content_bytes = f.read()
        source_sha256 = hashlib.sha256(content_bytes).hexdigest()

        # 1. Idempotency Check
        existing = self.ingestion_repo.get_by_sha256(source_sha256)
        if existing:
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

        # 3. Process Rows through Pure Domain Pipeline & Build DB Records
        ops_models = []
        facts_models = []
        alert_models = []
        pipeline_results = []

        valid_count = 0
        blocked_count = 0
        prev_end = 0.0

        for idx, row in enumerate(raw_rows):
            # Production Table: DO NOT store Expected_Anomaly_ID
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

            # Pass into Pure Domain Pipeline
            res = process_daily_record(row, prev_actual_end_kg=prev_end)
            pipeline_results.append(res)

            if res["data_status"] == "OK" and res.get("facts"):
                valid_count += 1
                f = res["facts"]
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
                    data_status="OK",
                    dataset_type=dataset_type,
                    ingestion_id=ingestion_id
                )
                facts_models.append(fact_model)
            else:
                # GA-007 / DATA_INCOMPLETE: Do NOT fabricate facts!
                blocked_count += 1
                fact_model = DailyFact(
                    business_date=b_date,
                    data_status="DATA_INCOMPLETE",
                    dataset_type=dataset_type,
                    ingestion_id=ingestion_id
                )
                facts_models.append(fact_model)

            # Save Daily Alerts
            for a in res.get("alerts", []):
                alert_id = f"ALT-{uuid.uuid4().hex[:10].upper()}"
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
                    ingestion_id=ingestion_id
                )
                alert_models.append(alert_model)

        # 4. Run Generalized Period Rules
        period_models = []
        # A. Food Cost Streak
        fc_streaks = detect_food_cost_streak(pipeline_results, threshold=0.39, min_consecutive_days=7)
        for s in fc_streaks:
            p_alt_id = f"PALT-{uuid.uuid4().hex[:10].upper()}"
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
                ingestion_id=ingestion_id
            ))

        # B. Profit Reversal
        p_reversals = detect_profit_reversal(pipeline_results, window_days=7)
        for pr in p_reversals:
            p_alt_id = f"PALT-{uuid.uuid4().hex[:10].upper()}"
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
                ingestion_id=ingestion_id
            ))

        # 5. Persist Everything in DB Transaction
        self.ops_repo.create_batch(ops_models)
        self.facts_repo.create_batch(facts_models)
        self.alerts_repo.create_alerts(alert_models)
        self.alerts_repo.create_period_alerts(period_models)

        run_record.valid_row_count = valid_count
        run_record.blocked_row_count = blocked_count
        run_record.status = "COMPLETED"
        run_record.completed_at = datetime.datetime.utcnow()

        self.db.commit()

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

files['apps/api/services/dashboard_service.py'] = """# -*- coding: utf-8 -*-
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from apps.api.repositories.facts_repository import FactsRepository
from apps.api.repositories.alerts_repository import AlertsRepository
from apps.api.schemas.dashboard import DailyDashboardResponse, DashboardKPISchema, DashboardSummaryResponse
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
        alert_schemas = [AlertSchema.from_orm(a) for a in alerts]

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

        return DailyDashboardResponse(
            date=fact.business_date,
            dataset_type=fact.dataset_type,
            data_status=fact.data_status,
            kpis=kpi_schema,
            alerts=alert_schemas,
            evidence_ids=[]
        )

    def get_dashboard_summary(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> DashboardSummaryResponse:
        facts = self.facts_repo.list_facts(start_date=start_date, end_date=end_date)
        if not facts:
            return DashboardSummaryResponse(
                start_date=start_date or "",
                end_date=end_date or "",
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
                medium_alert_count=0
            )

        valid_facts = [f for f in facts if f.data_status == "OK" and f.sales is not None]
        incomplete_days = len([f for f in facts if f.data_status == "DATA_INCOMPLETE"])

        tot_sales = sum(f.sales for f in valid_facts) if valid_facts else 0.0
        tot_contrib = sum(f.contribution for f in valid_facts if f.contribution is not None) if valid_facts else 0.0
        avg_sales = tot_sales / len(valid_facts) if valid_facts else 0.0

        labor_ratios = [f.labor_ratio for f in valid_facts if f.labor_ratio is not None]
        avg_labor_ratio = round(sum(labor_ratios) / len(labor_ratios), 4) if labor_ratios else None

        fc_ratios = [f.food_cost_ratio for f in valid_facts if f.food_cost_ratio is not None]
        avg_fc_ratio = round(sum(fc_ratios) / len(fc_ratios), 4) if fc_ratios else None

        avg_contrib_ratio = round(tot_contrib / tot_sales, 4) if tot_sales > 0 else None

        # Alerts summary
        effective_start = start_date or facts[0].business_date
        effective_end = end_date or facts[-1].business_date
        alerts = self.alerts_repo.list_alerts(start_date=effective_start, end_date=effective_end)

        crit = len([a for a in alerts if a.severity == "CRITICAL"])
        high = len([a for a in alerts if a.severity == "HIGH"])
        med = len([a for a in alerts if a.severity == "MEDIUM"])

        return DashboardSummaryResponse(
            start_date=effective_start,
            end_date=effective_end,
            dataset_type="SYNTHETIC",
            total_days=len(facts),
            data_complete_days=len(valid_facts),
            data_incomplete_days=incomplete_days,
            total_sales=tot_sales,
            average_daily_sales=round(avg_sales, 2),
            average_labor_ratio=avg_labor_ratio,
            average_food_cost_ratio=avg_fc_ratio,
            total_contribution=tot_contrib,
            average_contribution_ratio=avg_contrib_ratio,
            critical_alert_count=crit,
            high_alert_count=high,
            medium_alert_count=med
        )
"""

# 8. Routes
files['apps/api/routes/health.py'] = """# -*- coding: utf-8 -*-
from fastapi import APIRouter
from apps.api.config import settings

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }
"""

files['apps/api/routes/ingestion.py'] = """# -*- coding: utf-8 -*-
import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from apps.api.dependencies import get_db
from apps.api.config import settings
from apps.api.services.ingestion_service import IngestionService
from apps.api.schemas.ingestion import IngestionResult, IngestionRunResponse
from apps.api.repositories.ingestion_repository import IngestionRepository

router = APIRouter(prefix="/api/v1/ingestions", tags=["Ingestion"])

@router.post("/synthetic", response_model=IngestionResult)
def ingest_synthetic(file_path: str = Query(default=settings.SYNTHETIC_DATASET_PATH),
                    db: Session = Depends(get_db)):
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    service = IngestionService(db)
    result = service.ingest_synthetic_dataset(file_path=file_path, dataset_type="SYNTHETIC")
    return result

@router.get("", response_model=List[IngestionRunResponse])
def list_ingestions(limit: int = Query(default=50, ge=1, le=100), db: Session = Depends(get_db)):
    repo = IngestionRepository(db)
    return repo.list_runs(limit=limit)
"""

files['apps/api/routes/operations.py'] = """# -*- coding: utf-8 -*-
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from apps.api.dependencies import get_db
from apps.api.repositories.operations_repository import OperationsRepository
from apps.api.schemas.operations import DailyOperationSchema

router = APIRouter(prefix="/api/v1/operations", tags=["Operations"])

@router.get("", response_model=List[DailyOperationSchema])
def list_operations(start_date: Optional[str] = Query(None),
                    end_date: Optional[str] = Query(None),
                    db: Session = Depends(get_db)):
    repo = OperationsRepository(db)
    return repo.list_operations(start_date=start_date, end_date=end_date)
"""

files['apps/api/routes/facts.py'] = """# -*- coding: utf-8 -*-
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from apps.api.dependencies import get_db
from apps.api.repositories.facts_repository import FactsRepository
from apps.api.schemas.facts import DailyFactSchema

router = APIRouter(prefix="/api/v1/facts", tags=["Facts"])

@router.get("", response_model=List[DailyFactSchema])
def list_facts(start_date: Optional[str] = Query(None),
               end_date: Optional[str] = Query(None),
               db: Session = Depends(get_db)):
    repo = FactsRepository(db)
    return repo.list_facts(start_date=start_date, end_date=end_date)

@router.get("/{date}", response_model=DailyFactSchema)
def get_facts_by_date(date: str, db: Session = Depends(get_db)):
    repo = FactsRepository(db)
    fact = repo.get_by_date(date)
    if not fact:
        raise HTTPException(status_code=404, detail=f"Facts not found for date: {date}")
    return fact
"""

files['apps/api/routes/alerts.py'] = """# -*- coding: utf-8 -*-
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from apps.api.dependencies import get_db
from apps.api.repositories.alerts_repository import AlertsRepository
from apps.api.schemas.alerts import AlertSchema, PeriodAlertSchema

router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts"])

@router.get("", response_model=List[AlertSchema])
def list_alerts(start_date: Optional[str] = Query(None),
                end_date: Optional[str] = Query(None),
                severity: Optional[str] = Query(None),
                rule_id: Optional[str] = Query(None),
                db: Session = Depends(get_db)):
    if severity and severity.upper() not in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "NORMAL"):
        raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")
    repo = AlertsRepository(db)
    return repo.list_alerts(start_date=start_date, end_date=end_date, severity=severity, rule_id=rule_id)

@router.get("/periods", response_model=List[PeriodAlertSchema])
def list_period_alerts(db: Session = Depends(get_db)):
    repo = AlertsRepository(db)
    return repo.list_period_alerts()

@router.get("/{date}", response_model=List[AlertSchema])
def get_alerts_by_date(date: str, db: Session = Depends(get_db)):
    repo = AlertsRepository(db)
    return repo.get_by_date(date)
"""

files['apps/api/routes/dashboard.py'] = """# -*- coding: utf-8 -*-
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from apps.api.dependencies import get_db
from apps.api.services.dashboard_service import DashboardService
from apps.api.schemas.dashboard import DailyDashboardResponse, DashboardSummaryResponse

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])

@router.get("/daily/{date}", response_model=DailyDashboardResponse)
def get_daily_dashboard(date: str, db: Session = Depends(get_db)):
    service = DashboardService(db)
    dash = service.get_daily_dashboard(date)
    if not dash:
        raise HTTPException(status_code=404, detail=f"Dashboard data not found for date: {date}")
    return dash

@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(start_date: Optional[str] = Query(None),
                          end_date: Optional[str] = Query(None),
                          db: Session = Depends(get_db)):
    service = DashboardService(db)
    return service.get_dashboard_summary(start_date=start_date, end_date=end_date)
"""

# 9. Main Application
files['apps/api/main.py'] = """# -*- coding: utf-8 -*-
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.api.config import settings
from apps.api.database import engine, Base
from apps.api.routes import health, ingestion, operations, facts, alerts, dashboard

# Create tables if not exists
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

app.include_router(health.router)
app.include_router(ingestion.router)
app.include_router(operations.router)
app.include_router(facts.router)
app.include_router(alerts.router)
app.include_router(dashboard.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.api.main:app", host="0.0.0.0", port=8000, reload=True)
"""

for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

print(f"Successfully generated {len(files)} API files.")

