# -*- coding: utf-8 -*-
import uuid
from typing import List, Dict, Any, Optional
from domains.adapters.schemas import QuarantineRecord

class QuarantineManager:
    """
    Quarantine Isolation Manager.
    Logs invalid rows without crashing the entire batch ingestion.
    Provides PII-safe value previews.
    """
    @staticmethod
    def create_record(
        source_file: str,
        source_row: int,
        reason: str,
        field_name: Optional[str] = None,
        raw_val: Any = None
    ) -> QuarantineRecord:
        safe_preview = None
        if raw_val is not None:
            s = str(raw_val)
            safe_preview = s[:20] if len(s) <= 20 else s[:17] + "..."

        return QuarantineRecord(
            quarantine_id=f"QRN-{uuid.uuid4().hex[:8].upper()}",
            source_file=source_file,
            source_row=source_row,
            reason=reason,
            field_name=field_name,
            safe_value_preview=safe_preview
        )

