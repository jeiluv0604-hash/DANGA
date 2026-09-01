# -*- coding: utf-8 -*-
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
