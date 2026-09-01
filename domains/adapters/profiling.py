# -*- coding: utf-8 -*-
import hashlib
import os
from typing import List, Dict, Any, Optional
import pandas as pd
from domains.adapters.schemas import DataProfile
from domains.adapters.privacy import SensitiveColumnDetector

class SourceProfiler:
    """
    Profiles incoming source data files (CSV or Excel) to generate structural metadata,
    detect columns, infer data types, calculate nulls, duplicates, and ranges without leaking PII.
    """
    @staticmethod
    def profile_file(file_path: str, sheet_name: Optional[str] = None) -> DataProfile:
        with open(file_path, "rb") as f:
            content_bytes = f.read()
        file_sha256 = hashlib.sha256(content_bytes).hexdigest()
        file_size = len(content_bytes)
        filename = os.path.basename(file_path)

        sheet_names = []
        if file_path.lower().endswith((".xlsx", ".xls")):
            with pd.ExcelFile(file_path) as xl:
                sheet_names = xl.sheet_names
                target_sheet = sheet_name or sheet_names[0]
                df = pd.read_excel(xl, sheet_name=target_sheet)
        else:
            df = pd.read_csv(file_path)

        columns = [str(c).strip() for c in df.columns]
        row_count = len(df)
        null_counts = {c: int(df[c].isnull().sum()) for c in df.columns}
        dup_count = int(df.duplicated().sum())

        inferred_types = {}
        for c in df.columns:
            dtype_str = str(df[c].dtype)
            if "int" in dtype_str:
                inferred_types[str(c)] = "INTEGER"
            elif "float" in dtype_str:
                inferred_types[str(c)] = "FLOAT"
            elif "datetime" in dtype_str:
                inferred_types[str(c)] = "DATETIME"
            else:
                inferred_types[str(c)] = "STRING"

        # Date range detection
        min_date, max_date = None, None
        date_candidates = [c for c in columns if any(k in c.lower() for k in ["일자", "date", "시간", "time"])]
        for dc in date_candidates:
            try:
                dt_series = pd.to_datetime(df[dc].dropna(), errors="coerce")
                valid_dts = dt_series.dropna()
                if not valid_dts.empty:
                    min_date = valid_dts.min().strftime("%Y-%m-%d")
                    max_date = valid_dts.max().strftime("%Y-%m-%d")
                    break
            except Exception:
                pass

        # Numeric ranges
        numeric_ranges = {}
        for c in df.columns:
            if pd.api.types.is_numeric_dtype(df[c]):
                valid_num = df[c].dropna()
                if not valid_num.empty:
                    numeric_ranges[str(c)] = {
                        "min": float(valid_num.min()),
                        "max": float(valid_num.max()),
                        "mean": float(valid_num.mean())
                    }

        # Masked sample values (at most 3 samples per column)
        sample_masked = {}
        for c in df.columns:
            samples = df[c].dropna().head(3).tolist()
            sample_masked[str(c)] = [SensitiveColumnDetector.mask_sample_value(str(c), s) for s in samples]

        # Sensitive columns scan
        sensitive_cols = SensitiveColumnDetector.scan_columns(columns)

        return DataProfile(
            filename=filename,
            file_sha256=file_sha256,
            file_size_bytes=file_size,
            sheet_names=sheet_names,
            row_count=row_count,
            column_names=columns,
            inferred_types=inferred_types,
            null_counts=null_counts,
            duplicate_count=dup_count,
            min_date=min_date,
            max_date=max_date,
            numeric_ranges=numeric_ranges,
            sample_values_masked=sample_masked,
            sensitive_columns_detected=sensitive_cols
        )

