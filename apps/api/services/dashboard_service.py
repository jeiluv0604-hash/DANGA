# -*- coding: utf-8 -*-
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
