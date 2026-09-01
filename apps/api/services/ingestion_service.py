# -*- coding: utf-8 -*-
import datetime
import hashlib
import json
import os
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

        os.makedirs("evidence", exist_ok=True)

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

            # Daily Alerts & Real Evidence File Generation
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

                # Write Real Evidence JSON File
                ev_payload = {
                    "evidence_id": ev_id,
                    "evidence_type": "DAILY_ALERT",
                    "business_date": b_date,
                    "rule_id": a["rule_id"],
                    "severity": a["severity"],
                    "status": a.get("status", "ALERT"),
                    "actual": a.get("actual"),
                    "threshold": a.get("threshold"),
                    "comparison": a.get("comparison", ""),
                    "dataset_type": dataset_type,
                    "dataset_sha256": source_sha256,
                    "created_at": datetime.datetime.utcnow().isoformat()
                }
                ev_file_path = f"evidence/{ev_id}.json"
                with open(ev_file_path, "w", encoding="utf-8") as ef:
                    json.dump(ev_payload, ef, ensure_ascii=False, indent=2)

                # Calculate SHA-256 of the actual evidence file
                with open(ev_file_path, "rb") as ef:
                    file_sha256 = hashlib.sha256(ef.read()).hexdigest()

                ev_model = EvidenceIndex(
                    evidence_id=ev_id,
                    evidence_type="DAILY_ALERT",
                    business_date=b_date,
                    rule_id=a["rule_id"],
                    file_path=ev_file_path,
                    file_sha256=file_sha256,
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
            ev_payload = {
                "evidence_id": ev_id,
                "evidence_type": "PERIOD_ALERT",
                "business_date": s["start_date"],
                "rule_id": s["rule_id"],
                "severity": s["severity"],
                "period": f"{s['start_date']}~{s['end_date']}",
                "actual": s.get("actual"),
                "comparison": s.get("comparison"),
                "dataset_type": dataset_type,
                "dataset_sha256": source_sha256,
                "created_at": datetime.datetime.utcnow().isoformat()
            }
            ev_file_path = f"evidence/{ev_id}.json"
            with open(ev_file_path, "w", encoding="utf-8") as ef:
                json.dump(ev_payload, ef, ensure_ascii=False, indent=2)

            with open(ev_file_path, "rb") as ef:
                file_sha256 = hashlib.sha256(ef.read()).hexdigest()

            evidence_models.append(EvidenceIndex(
                evidence_id=ev_id,
                evidence_type="PERIOD_ALERT",
                business_date=s["start_date"],
                rule_id=s["rule_id"],
                file_path=ev_file_path,
                file_sha256=file_sha256,
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
            ev_payload = {
                "evidence_id": ev_id,
                "evidence_type": "PERIOD_ALERT",
                "business_date": pr["target_start"],
                "rule_id": pr["rule_id"],
                "severity": pr["severity"],
                "baseline_period": f"{pr['baseline_start']}~{pr['baseline_end']}",
                "target_period": f"{pr['target_start']}~{pr['target_end']}",
                "actual": pr.get("actual"),
                "comparison": pr.get("comparison"),
                "dataset_type": dataset_type,
                "dataset_sha256": source_sha256,
                "created_at": datetime.datetime.utcnow().isoformat()
            }
            ev_file_path = f"evidence/{ev_id}.json"
            with open(ev_file_path, "w", encoding="utf-8") as ef:
                json.dump(ev_payload, ef, ensure_ascii=False, indent=2)

            with open(ev_file_path, "rb") as ef:
                file_sha256 = hashlib.sha256(ef.read()).hexdigest()

            evidence_models.append(EvidenceIndex(
                evidence_id=ev_id,
                evidence_type="PERIOD_ALERT",
                business_date=pr["target_start"],
                rule_id=pr["rule_id"],
                file_path=ev_file_path,
                file_sha256=file_sha256,
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
