# -*- coding: utf-8 -*-
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
