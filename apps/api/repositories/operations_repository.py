# -*- coding: utf-8 -*-
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
