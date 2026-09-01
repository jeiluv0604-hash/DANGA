# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from domains.adapters.schemas import DataProfile, MappingManifest, MappingResult

class SourceAdapter(ABC):
    """
    Abstract Source Adapter.
    No vendor-specific hardcoding (e.g. OKPOS, EasyPOS).
    Provides generic file profiling, mapping, structural validation, and canonical conversion.
    """
    @abstractmethod
    def detect_source_type(self, file_path: str) -> str:
        """Detect whether file is POS, ATTENDANCE, PURCHASE, INVENTORY, or UNKNOWN"""
        pass

    @abstractmethod
    def profile(self, file_path: str, sheet_name: Optional[str] = None) -> DataProfile:
        """Generate structured metadata profile for file"""
        pass

    @abstractmethod
    def map_to_canonical(
        self,
        file_path: str,
        manifest: MappingManifest,
        sheet_name: Optional[str] = None
    ) -> MappingResult:
        """Transform source rows to Canonical Records and Quarantine invalid rows"""
        pass

