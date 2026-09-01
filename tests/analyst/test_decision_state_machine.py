# -*- coding: utf-8 -*-
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from apps.api.database import Base
from apps.api.repositories.analyst_repository import AnalystRepository, InvalidStateTransitionError

class TestDecisionStateMachine:
    @pytest.fixture
    def db_session(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        yield session
        session.close()

    def _create_sample_brief(self, repo: AnalystRepository, brief_id: str = "BRF-2026-06-12-TEST"):
        return repo.save_brief({
            "brief_id": brief_id,
            "business_date": "2026-06-12",
            "status": "REVIEW_REQUIRED",
            "executive_summary": "Test Brief"
        })

    def test_state_01_review_required_to_approved(self, db_session):
        repo = AnalystRepository(db_session)
        self._create_sample_brief(repo, "BRF-01")
        brief = repo.update_brief_status("BRF-01", "APPROVED", "CEO", "Approved")
        assert brief.status == "APPROVED"

    def test_state_02_review_required_to_rejected(self, db_session):
        repo = AnalystRepository(db_session)
        self._create_sample_brief(repo, "BRF-02")
        brief = repo.update_brief_status("BRF-02", "REJECTED", "GENERAL_MANAGER", "Rejected")
        assert brief.status == "REJECTED"

    def test_state_03_approved_to_approved_disallowed(self, db_session):
        repo = AnalystRepository(db_session)
        self._create_sample_brief(repo, "BRF-03")
        repo.update_brief_status("BRF-03", "APPROVED", "CEO", "First approval")
        with pytest.raises(InvalidStateTransitionError):
            repo.update_brief_status("BRF-03", "APPROVED", "CEO", "Double approval")

    def test_state_04_approved_to_rejected_disallowed(self, db_session):
        repo = AnalystRepository(db_session)
        self._create_sample_brief(repo, "BRF-04")
        repo.update_brief_status("BRF-04", "APPROVED", "CEO", "Approved")
        with pytest.raises(InvalidStateTransitionError):
            repo.update_brief_status("BRF-04", "REJECTED", "CEO", "Attempted switch")

    def test_state_05_rejected_to_approved_disallowed(self, db_session):
        repo = AnalystRepository(db_session)
        self._create_sample_brief(repo, "BRF-05")
        repo.update_brief_status("BRF-05", "REJECTED", "GENERAL_MANAGER", "Rejected")
        with pytest.raises(InvalidStateTransitionError):
            repo.update_brief_status("BRF-05", "APPROVED", "CEO", "Attempted override")

    def test_state_06_rejected_to_rejected_disallowed(self, db_session):
        repo = AnalystRepository(db_session)
        self._create_sample_brief(repo, "BRF-06")
        repo.update_brief_status("BRF-06", "REJECTED", "GENERAL_MANAGER", "First reject")
        with pytest.raises(InvalidStateTransitionError):
            repo.update_brief_status("BRF-06", "REJECTED", "GENERAL_MANAGER", "Double reject")

