# -*- coding: utf-8 -*-
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from apps.api.database import Base
from apps.api.models.facts import DailyFact
from apps.api.services.analyst_service import AnalystService
from apps.api.models.analyst import AnalystBriefModel

class TestIdempotency:
    @pytest.fixture
    def db_session(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        # Add a sample daily fact
        fact = DailyFact(
            business_date="2026-06-12",
            sales=13092000,
            labor_cost=4648000,
            labor_ratio=0.355,
            food_cost=4401000,
            food_cost_ratio=0.336,
            contribution=4043000,
            contribution_ratio=0.309,
            data_status="OK",
            ingestion_id="INGEST-TEST-01"
        )
        session.add(fact)
        session.commit()
        
        yield session
        session.close()

    def test_idempotency_01_repeated_calls_reuse_existing_brief(self, db_session):
        service = AnalystService(db_session)
        
        # 10 repeated calls
        res_list = []
        for _ in range(10):
            res = service.generate_daily_brief("2026-06-12", regenerate=False)
            res_list.append(res)
        
        # All 10 returned the exact same brief_id
        first_id = res_list[0].brief_id
        for r in res_list:
            assert r.brief_id == first_id

        # Total rows in DB is exactly 1, not 10
        total_rows = db_session.query(AnalystBriefModel).filter(
            AnalystBriefModel.business_date == "2026-06-12"
        ).count()
        assert total_rows == 1

    def test_idempotency_02_explicit_regenerate_creates_new_version(self, db_session):
        service = AnalystService(db_session)
        res1 = service.generate_daily_brief("2026-06-12", regenerate=False)
        res2 = service.generate_daily_brief("2026-06-12", regenerate=True)
        
        assert res1.brief_id != res2.brief_id
        total_rows = db_session.query(AnalystBriefModel).filter(
            AnalystBriefModel.business_date == "2026-06-12"
        ).count()
        assert total_rows == 2

