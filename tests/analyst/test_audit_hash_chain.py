# -*- coding: utf-8 -*-
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from apps.api.database import Base
from apps.api.repositories.analyst_repository import AnalystRepository
from apps.api.models.analyst import DecisionAuditLogModel

class TestAuditHashChain:
    @pytest.fixture
    def db_session(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        yield session
        session.close()

    def test_audit_01_valid_hash_chain(self, db_session):
        repo = AnalystRepository(db_session)
        repo.save_brief({
            "brief_id": "BRF-CHAIN-01",
            "business_date": "2026-06-12",
            "status": "REVIEW_REQUIRED",
            "executive_summary": "Test Brief"
        })
        
        # Action 1: Approval
        repo.update_brief_status("BRF-CHAIN-01", "APPROVED", "CEO", "First action approved")
        
        # Verify chain
        res = repo.verify_audit_chain("BRF-CHAIN-01")
        assert res["valid"] is True
        assert res["status"] == "VALID"
        assert res["log_count"] == 1

    def test_audit_02_middle_payload_tampered(self, db_session):
        repo = AnalystRepository(db_session)
        repo.save_brief({
            "brief_id": "BRF-CHAIN-02",
            "business_date": "2026-06-12",
            "status": "REVIEW_REQUIRED",
            "executive_summary": "Test Brief"
        })
        
        repo.update_brief_status("BRF-CHAIN-02", "APPROVED", "CEO", "Original comment")
        
        # Malicious attacker alters the comment directly in SQL database
        log = db_session.query(DecisionAuditLogModel).filter(
            DecisionAuditLogModel.brief_id == "BRF-CHAIN-02"
        ).first()
        log.comment = "TAMPERED_MALICIOUS_COMMENT"
        db_session.commit()
        
        # Verify chain detects tampering
        res = repo.verify_audit_chain("BRF-CHAIN-02")
        assert res["valid"] is False
        assert res["status"] == "INVALID"
        assert "Payload tampered" in res["reason"]

    def test_audit_03_previous_hash_tampered(self, db_session):
        repo = AnalystRepository(db_session)
        repo.save_brief({
            "brief_id": "BRF-CHAIN-03",
            "business_date": "2026-06-12",
            "status": "REVIEW_REQUIRED",
            "executive_summary": "Test Brief"
        })
        
        repo.update_brief_status("BRF-CHAIN-03", "APPROVED", "CEO", "Action 1")
        
        # Attacker modifies previous_hash
        log = db_session.query(DecisionAuditLogModel).filter(
            DecisionAuditLogModel.brief_id == "BRF-CHAIN-03"
        ).first()
        log.previous_hash = "FORGED_PREVIOUS_HASH_12345"
        db_session.commit()
        
        # Verify chain detects forged previous_hash
        res = repo.verify_audit_chain("BRF-CHAIN-03")
        assert res["valid"] is False
        assert "mismatch" in res["reason"] or res["status"] in ["INVALID", "BROKEN_CHAIN"]

    def test_audit_04_deleted_event_breaks_chain(self, db_session):
        repo = AnalystRepository(db_session)
        repo.save_brief({
            "brief_id": "BRF-CHAIN-04",
            "business_date": "2026-06-12",
            "status": "REVIEW_REQUIRED",
            "executive_summary": "Test Brief"
        })
        
        # Create log 1 manually, then log 2
        log1 = DecisionAuditLogModel(
            log_id="LOG-01",
            brief_id="BRF-CHAIN-04",
            previous_status="REVIEW_REQUIRED",
            new_status="REVIEW_REQUIRED",
            actor_role="SYSTEM",
            action_type="INIT",
            previous_hash="GENESIS",
            event_hash="HASH_OF_EVENT_1"
        )
        db_session.add(log1)
        
        log2 = DecisionAuditLogModel(
            log_id="LOG-02",
            brief_id="BRF-CHAIN-04",
            previous_status="REVIEW_REQUIRED",
            new_status="APPROVED",
            actor_role="CEO",
            action_type="SET_APPROVED",
            previous_hash="HASH_OF_EVENT_1",
            event_hash="HASH_OF_EVENT_2"
        )
        db_session.add(log2)
        db_session.commit()
        
        # Attacker deletes log 1
        db_session.delete(log1)
        db_session.commit()
        
        # Verify chain detects broken chain
        res = repo.verify_audit_chain("BRF-CHAIN-04")
        assert res["valid"] is False
        assert res["status"] in ["BROKEN_CHAIN", "INVALID"]

