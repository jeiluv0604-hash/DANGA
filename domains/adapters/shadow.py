# -*- coding: utf-8 -*-
import datetime
from typing import List, Dict, Any, Optional
from domains.pipeline import process_daily_record

class ShadowProcessor:
    """
    Shadow Mode Processor.
    Processes real canonical records in SHADOW_REAL mode without affecting production truth.
    - AI Analyst operational recommendations are disabled (ai_eligible=False).
    - Thresholds explicitly labeled with 'SYNTHETIC CALIBRATION'.
    """
    @staticmethod
    def process_shadow_daily_facts(
        business_date: str,
        pos_records: List[Dict[str, Any]],
        attendance_records: Optional[List[Dict[str, Any]]] = None,
        purchase_records: Optional[List[Dict[str, Any]]] = None,
        inventory_records: Optional[List[Dict[str, Any]]] = None,
        dataset_type: str = "SHADOW_REAL",
        verification_status: str = "RECONCILED"
    ) -> Dict[str, Any]:
        # 1. Aggregate POS
        total_sales = sum(float(r.get("net_sales", 0.0) or 0.0) for r in pos_records if not r.get("cancelled", False))
        guests_sum = sum(int(r.get("guests", 0) or 0) for r in pos_records if r.get("guests") is not None)
        guests = guests_sum if guests_sum > 0 else (len(pos_records) or None)

        # 2. Aggregate Attendance
        labor_cost = None
        if attendance_records:
            costs = [float(r["labor_cost"]) for r in attendance_records if r.get("labor_cost") is not None]
            if costs:
                labor_cost = sum(costs)

        # 3. Aggregate Purchases / Food Cost
        food_cost = None
        if purchase_records:
            fc_list = [float(r["amount"]) for r in purchase_records if r.get("amount") is not None]
            if fc_list:
                food_cost = sum(fc_list)

        # 4. Aggregate Inventory
        actual_end_kg = None
        incoming_kg = None
        sold_kg = None
        service_kg = None
        waste_kg = None
        if inventory_records:
            act_list = [float(r.get("actual_end_qty", 0.0)) for r in inventory_records if r.get("actual_end_qty") is not None]
            if act_list:
                actual_end_kg = sum(act_list)

        raw_ops = {
            "Date": business_date,
            "Sales": total_sales if total_sales > 0 else None,
            "Guests": guests,
            "Labor_Cost": labor_cost,
            "Food_Cost": food_cost,
            "Actual_End_KG": actual_end_kg,
            "Incoming_KG": incoming_kg,
            "Sold_KG": sold_kg,
            "Service_KG": service_kg,
            "Waste_KG": waste_kg
        }

        # Run pipeline
        res = process_daily_record(raw_ops)

        return {
            "business_date": business_date,
            "dataset_type": dataset_type,
            "verification_status": verification_status,
            "calibration_mode": "SYNTHETIC CALIBRATION",
            "ai_eligible": False,  # Strict shadow AI policy
            "data_status": res.get("data_status", "OK"),
            "facts": res.get("facts", {}),
            "alerts": res.get("alerts", [])
        }

