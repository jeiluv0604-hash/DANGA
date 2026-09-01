# -*- coding: utf-8 -*-
from fastapi import APIRouter
from typing import List, Dict, Any
from domains.rules import RULES

router = APIRouter(prefix="/api/v1/rules", tags=["Rules Metadata"])

@router.get("/metadata")
def get_rules_metadata() -> List[Dict[str, Any]]:
    """
    Returns exact Rule Engine truth metadata to ensure zero drift with UI.
    """
    return RULES


