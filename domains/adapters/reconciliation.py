# -*- coding: utf-8 -*-
import uuid
import datetime
from typing import List, Dict, Any, Optional
from domains.adapters.schemas import ReconciliationMetric, ReconciliationReport

class ReconciliationEngine:
    """
    Reconciles Granular Canonical Transactions vs Aggregate / Calculated Totals.
    Produces MATCH, MINOR_MISMATCH, MAJOR_MISMATCH, or NOT_COMPARABLE.
    """
    @staticmethod
    def reconcile_pos_sales(
        import_id: str,
        transaction_rows: List[Dict[str, Any]],
        expected_daily_sales: Optional[float] = None
    ) -> ReconciliationReport:
        rec_id = f"REC-POS-{uuid.uuid4().hex[:8].upper()}"
        metrics = []

        total_net_sales = sum(float(r.get("net_sales", 0.0) or 0.0) for r in transaction_rows if not r.get("cancelled", False))
        
        if expected_daily_sales is None:
            metrics.append(ReconciliationMetric(
                name="POS_TOTAL_NET_SALES_AGGREGATE",
                source_value=total_net_sales,
                calculated_value=total_net_sales,
                diff_abs=0.0,
                diff_pct=0.0,
                status="MATCH",
                detail="Transaction sum established as baseline"
            ))
            overall = "MATCH"
        else:
            diff_abs = abs(total_net_sales - expected_daily_sales)
            diff_pct = (diff_abs / expected_daily_sales) if expected_daily_sales > 0 else 0.0
            
            if diff_abs < 1.0:
                st = "MATCH"
            elif diff_pct <= 0.02:
                st = "MINOR_MISMATCH"
            else:
                st = "MAJOR_MISMATCH"

            metrics.append(ReconciliationMetric(
                name="POS_NET_SALES_VS_DAILY_TOTAL",
                source_value=expected_daily_sales,
                calculated_value=total_net_sales,
                diff_abs=round(diff_abs, 2),
                diff_pct=round(diff_pct, 4),
                status=st,
                detail=f"Source={expected_daily_sales:,.0f} vs TransSum={total_net_sales:,.0f}"
            ))
            overall = st

        return ReconciliationReport(
            reconciliation_id=rec_id,
            import_id=import_id,
            source_type="POS",
            overall_status=overall,
            metrics=metrics,
            generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )

    @staticmethod
    def reconcile_purchases(
        import_id: str,
        purchase_rows: List[Dict[str, Any]]
    ) -> ReconciliationReport:
        rec_id = f"REC-PUR-{uuid.uuid4().hex[:8].upper()}"
        metrics = []
        overall = "MATCH"

        for r in purchase_rows:
            source_amt = r.get("source_amount") or r.get("amount")
            qty = float(r.get("quantity", 0.0) or 0.0)
            price = float(r.get("unit_price", 0.0) or 0.0)
            calc_amt = qty * price

            if source_amt is None:
                st = "NOT_COMPARABLE"
                diff_abs, diff_pct = 0.0, 0.0
            else:
                source_amt = float(source_amt)
                diff_abs = abs(calc_amt - source_amt)
                diff_pct = (diff_abs / source_amt) if source_amt > 0 else 0.0
                if diff_abs < 1.0:
                    st = "MATCH"
                elif diff_pct <= 0.02:
                    st = "MINOR_MISMATCH"
                else:
                    st = "MAJOR_MISMATCH"

            if st == "MAJOR_MISMATCH":
                overall = "MAJOR_MISMATCH"
            elif st == "MINOR_MISMATCH" and overall != "MAJOR_MISMATCH":
                overall = "MINOR_MISMATCH"
            elif st == "NOT_COMPARABLE" and overall == "MATCH":
                overall = "NOT_COMPARABLE"

            metrics.append(ReconciliationMetric(
                name=f"ITEM_{r.get('item_id', 'UNKNOWN')}_AMOUNT",
                source_value=float(source_amt) if source_amt is not None else 0.0,
                calculated_value=round(calc_amt, 2),
                diff_abs=round(diff_abs, 2),
                diff_pct=round(diff_pct, 4),
                status=st,
                detail=f"SourceAmt={source_amt} vs (Qty {qty} * Price {price} = {calc_amt})"
            ))

        return ReconciliationReport(
            reconciliation_id=rec_id,
            import_id=import_id,
            source_type="PURCHASE",
            overall_status=overall,
            metrics=metrics[:20],  # cap metric items
            generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )

    @staticmethod
    def reconcile_inventory(
        import_id: str,
        inventory_rows: List[Dict[str, Any]]
    ) -> ReconciliationReport:
        rec_id = f"REC-INV-{uuid.uuid4().hex[:8].upper()}"
        metrics = []
        overall = "MATCH"

        for r in inventory_rows:
            opening = float(r.get("opening_qty", 0.0) or 0.0)
            incoming = float(r.get("incoming_qty", 0.0) or 0.0)
            sold = float(r.get("sold_qty", 0.0) or 0.0)
            service = float(r.get("service_qty", 0.0) or 0.0)
            waste = float(r.get("waste_qty", 0.0) or 0.0)
            staff = float(r.get("staff_meal_qty", 0.0) or 0.0)
            transfer = float(r.get("transfer_qty", 0.0) or 0.0)
            
            calc_theory = opening + incoming - sold - service - waste - staff + transfer
            actual_end = float(r.get("actual_end_qty", 0.0) or 0.0)
            
            variance = actual_end - calc_theory
            diff_abs = abs(variance)
            diff_pct = (diff_abs / calc_theory) if calc_theory > 0 else 0.0

            if diff_abs < 0.1:
                st = "MATCH"
            elif diff_abs <= 2.0:
                st = "MINOR_MISMATCH"
            else:
                st = "MAJOR_MISMATCH"

            if st == "MAJOR_MISMATCH":
                overall = "MAJOR_MISMATCH"
            elif st == "MINOR_MISMATCH" and overall != "MAJOR_MISMATCH":
                overall = "MINOR_MISMATCH"

            metrics.append(ReconciliationMetric(
                name=f"ITEM_{r.get('item_id', 'UNKNOWN')}_INVENTORY_VARIANCE",
                source_value=actual_end,
                calculated_value=round(calc_theory, 3),
                diff_abs=round(diff_abs, 3),
                diff_pct=round(diff_pct, 4),
                status=st,
                detail=f"Actual={actual_end}kg vs CalcTheory={calc_theory}kg (Variance={variance}kg)"
            ))

        return ReconciliationReport(
            reconciliation_id=rec_id,
            import_id=import_id,
            source_type="INVENTORY",
            overall_status=overall,
            metrics=metrics,
            generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )

