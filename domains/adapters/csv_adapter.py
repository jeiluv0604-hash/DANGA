# -*- coding: utf-8 -*-
import os
import pandas as pd
from typing import List, Dict, Any, Optional
from domains.adapters.base import SourceAdapter
from domains.adapters.schemas import DataProfile, MappingManifest, MappingResult, QuarantineRecord
from domains.adapters.profiling import SourceProfiler
from domains.adapters.quarantine import QuarantineManager

KNOWN_UNITS = {"kg", "g", "box", "ea", "pack", "can", "btl", "pk", "l", "ml", "개", "박스", "팩", "병", "캔"}

class GenericCSVAdapter(SourceAdapter):
    """
    Generic CSV Source Adapter.
    Processes CSV files into Canonical Records with Quarantine isolation.
    """
    def detect_source_type(self, file_path: str) -> str:
        df = pd.read_csv(file_path, nrows=5)
        cols_lower = [str(c).lower() for c in df.columns]
        
        if any(k in c for c in cols_lower for k in ["실사", "기초재고", "이론재고", "variance", "조사일자", "실재고"]):
            return "INVENTORY"
        if any(k in c for c in cols_lower for k in ["매입", "공급처", "거래처", "supplier", "단가", "입고일자"]):
            return "PURCHASE"
        if any(k in c for c in cols_lower for k in ["receipt", "영수증", "주문번호", "판매일자", "실매출", "총매출"]):
            return "POS"
        if any(k in c for c in cols_lower for k in ["사번", "직원번호", "출근", "퇴근", "clock_in", "근무시간"]):
            return "ATTENDANCE"
        return "UNKNOWN"

    def profile(self, file_path: str, sheet_name: Optional[str] = None) -> DataProfile:
        return SourceProfiler.profile_file(file_path)

    def map_to_canonical(
        self,
        file_path: str,
        manifest: MappingManifest,
        sheet_name: Optional[str] = None
    ) -> MappingResult:
        df = pd.read_csv(file_path)
        col_map = manifest.column_mappings
        st = manifest.source_type.upper()
        filename = os.path.basename(file_path)

        canonical_records = []
        quarantine_records = []
        issues = []

        seen_keys = set()

        for idx, row in df.iterrows():
            source_row_num = idx + 2 # 1-indexed header + data
            mapped_row = {}
            for src_col, canon_field in col_map.items():
                if src_col in df.columns:
                    mapped_row[canon_field] = row[src_col] if pd.notnull(row[src_col]) else None

            mapped_row["source_file"] = filename
            mapped_row["source_row"] = source_row_num
            mapped_row["source_system"] = "GENERIC_CSV"

            # Domain validation
            q_rec = self._validate_row(st, mapped_row, filename, source_row_num, seen_keys)
            if q_rec:
                quarantine_records.append(q_rec)
            else:
                canonical_records.append(mapped_row)

        return MappingResult(
            source_type=st,
            source_system="GENERIC_CSV",
            rows_received=len(df),
            rows_mapped=len(canonical_records),
            rows_quarantined=len(quarantine_records),
            mapping_version=manifest.mapping_version,
            canonical_records=canonical_records,
            quarantine_records=quarantine_records,
            issues=issues
        )

    def _validate_row(
        self,
        source_type: str,
        row: Dict[str, Any],
        filename: str,
        row_num: int,
        seen_keys: set
    ) -> Optional[QuarantineRecord]:
        if source_type == "POS":
            # Required: business_date, receipt_id, menu_id, quantity, net_sales
            if not row.get("business_date"):
                return QuarantineManager.create_record(filename, row_num, "MISSING_REQUIRED_FIELD", "business_date")
            if not row.get("receipt_id"):
                return QuarantineManager.create_record(filename, row_num, "MISSING_REQUIRED_FIELD", "receipt_id")
            if not row.get("menu_id"):
                return QuarantineManager.create_record(filename, row_num, "MISSING_REQUIRED_FIELD", "menu_id")
            
            # Date validation
            d_str = str(row["business_date"]).strip()
            if len(d_str) != 10 or d_str[4] != "-" or d_str[7] != "-":
                return QuarantineManager.create_record(filename, row_num, "INVALID_DATE", "business_date", d_str)

            # Duplicate check
            dup_key = f"{row.get('business_date')}_{row.get('receipt_id')}_{row.get('menu_id')}_{row.get('quantity')}"
            if dup_key in seen_keys:
                return QuarantineManager.create_record(filename, row_num, "DUPLICATE_RECEIPT", "receipt_id", row.get("receipt_id"))
            seen_keys.add(dup_key)

            # Number validation
            try:
                qty = int(row.get("quantity", 1))
                if qty <= 0:
                    return QuarantineManager.create_record(filename, row_num, "INVALID_NUMBER", "quantity", qty)
            except Exception:
                return QuarantineManager.create_record(filename, row_num, "INVALID_NUMBER", "quantity", row.get("quantity"))

            try:
                sales = float(row.get("net_sales", 0.0))
                if sales < 0:
                    return QuarantineManager.create_record(filename, row_num, "NEGATIVE_SALES", "net_sales", sales)
            except Exception:
                return QuarantineManager.create_record(filename, row_num, "INVALID_NUMBER", "net_sales", row.get("net_sales"))

        elif source_type == "ATTENDANCE":
            if not row.get("business_date"):
                return QuarantineManager.create_record(filename, row_num, "MISSING_REQUIRED_FIELD", "business_date")
            if not row.get("employee_id"):
                return QuarantineManager.create_record(filename, row_num, "MISSING_REQUIRED_FIELD", "employee_id")
            
            cin = str(row.get("clock_in", "")).strip()
            cout = str(row.get("clock_out", "")).strip()
            if cin and cout and cout < cin:
                return QuarantineManager.create_record(filename, row_num, "INVALID_TIME_RANGE", "clock_out", f"{cin}->{cout}")

        elif source_type == "PURCHASE":
            if not row.get("purchase_date"):
                return QuarantineManager.create_record(filename, row_num, "MISSING_REQUIRED_FIELD", "purchase_date")
            if not row.get("item_id"):
                return QuarantineManager.create_record(filename, row_num, "MISSING_REQUIRED_FIELD", "item_id")
            
            unit = str(row.get("unit", "")).strip().lower()
            if unit and unit not in KNOWN_UNITS:
                return QuarantineManager.create_record(filename, row_num, "UNIT_UNKNOWN", "unit", unit)

        elif source_type == "INVENTORY":
            if not row.get("business_date"):
                return QuarantineManager.create_record(filename, row_num, "MISSING_REQUIRED_FIELD", "business_date")
            if not row.get("item_id"):
                return QuarantineManager.create_record(filename, row_num, "MISSING_REQUIRED_FIELD", "item_id")

        return None

