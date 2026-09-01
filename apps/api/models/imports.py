# -*- coding: utf-8 -*-
import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text
from apps.api.database import Base

class SourceImportModel(Base):
    __tablename__ = 'source_imports'

    import_id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    source_sha256 = Column(String, index=True, nullable=False)
    source_type = Column(String, nullable=False) # POS, ATTENDANCE, PURCHASE, INVENTORY
    source_system = Column(String, default='GENERIC')
    mapping_id = Column(String, nullable=True)
    mapping_version = Column(String, default='1.0.0')
    dataset_type = Column(String, default='SHADOW_REAL') # SYNTHETIC, ADVERSARIAL, SHADOW_REAL, REAL
    verification_status = Column(String, default='UNVERIFIED') # UNVERIFIED, MAPPED, VALIDATED, RECONCILED, APPROVED
    readiness = Column(String, default='REVIEW_REQUIRED') # BLOCKED, REVIEW_REQUIRED, SHADOW_READY, REAL_READY
    
    rows_received = Column(Integer, default=0)
    rows_valid = Column(Integer, default=0)
    rows_quarantined = Column(Integer, default=0)
    rows_duplicate = Column(Integer, default=0)
    rows_reconciled = Column(Integer, default=0)
    
    profile_json = Column(Text, nullable=True)
    quality_report_json = Column(Text, nullable=True)
    reconciliation_json = Column(Text, nullable=True)
    
    started_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    completed_at = Column(DateTime, nullable=True)

class QuarantineRecordModel(Base):
    __tablename__ = 'quarantine_records'

    quarantine_id = Column(String, primary_key=True, index=True)
    import_id = Column(String, index=True, nullable=False)
    source_file = Column(String, nullable=False)
    source_row = Column(Integer, nullable=False)
    reason = Column(String, nullable=False)
    field_name = Column(String, nullable=True)
    safe_value_preview = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

class MappingManifestModel(Base):
    __tablename__ = 'mapping_manifests'

    mapping_id = Column(String, primary_key=True, index=True)
    source_type = Column(String, nullable=False)
    mapping_version = Column(String, default='1.0.0')
    status = Column(String, default='SUGGESTED') # SUGGESTED, CONFIRMED, REJECTED
    column_mapping_json = Column(Text, nullable=False)
    transform_rules_json = Column(Text, nullable=True)
    confirmed_by = Column(String, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
