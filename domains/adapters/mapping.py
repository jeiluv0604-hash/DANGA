# -*- coding: utf-8 -*-
from typing import List, Dict, Any, Optional, Tuple
from domains.adapters.schemas import MappingSuggestionItem, MappingManifest

ALIAS_DICTIONARY: Dict[str, Dict[str, List[str]]] = {
    "POS": {
        "business_date": ["매출일자", "영업일자", "판매일자", "date", "sales_date", "biz_date", "일자"],
        "transaction_time": ["거래시간", "결제시간", "주문시간", "time", "trans_time", "시간"],
        "receipt_id": ["영수증번호", "주문번호", "결제번호", "order_no", "receipt_no", "영수증"],
        "table_id": ["테이블번호", "테이블", "table", "table_no", "좌석번호"],
        "menu_id": ["메뉴코드", "상품코드", "item_code", "menu_code", "product_id", "코드"],
        "menu_name": ["메뉴명", "상품명", "품명", "item_name", "menu_name", "메뉴"],
        "quantity": ["수량", "판매수량", "주문수량", "qty", "quantity"],
        "gross_sales": ["총매출액", "총매출", "판매금액", "gross_sales", "gross_amount", "총금액"],
        "discount": ["할인금액", "할인액", "할인", "discount", "dc_amount"],
        "net_sales": ["실매출액", "결제금액", "실매출", "순매출", "net_sales", "paid_amount", "금액", "매출액"],
        "guests": ["객수", "방문객수", "고객수", "guests", "covers", "guest_count", "인원"],
        "payment_type": ["결제수단", "결제구분", "payment_method", "pay_type", "수단"]
    },
    "ATTENDANCE": {
        "business_date": ["근무일자", "영업일자", "일자", "date", "work_date"],
        "employee_id": ["직원번호", "사번", "직원코드", "emp_id", "employee_id", "staff_id"],
        "department": ["부서", "소속", "구분", "dept", "department"],
        "role": ["직책", "역할", "직급", "role", "position"],
        "clock_in": ["출근시간", "출근", "in_time", "clock_in"],
        "clock_out": ["퇴근시간", "퇴근", "out_time", "clock_out"],
        "worked_minutes": ["근무시간(분)", "총근무분", "근무분", "worked_minutes", "work_mins", "근무시간"],
        "regular_minutes": ["기본근무분", "기본분", "regular_minutes"],
        "overtime_minutes": ["연장근무분", "연장분", "overtime_minutes"],
        "labor_cost": ["인건비", "지급액", "급여", "labor_cost", "wage"]
    },
    "PURCHASE": {
        "purchase_date": ["매입일자", "입고일자", "일자", "purchase_date", "in_date"],
        "supplier_id": ["거래처코드", "공급처", "거래처", "supplier_id", "vendor_id", "거래처명"],
        "category": ["카테고리", "분류", "품목분류", "category"],
        "item_id": ["품목코드", "자재코드", "item_id", "item_code", "코드"],
        "item_name": ["품목명", "자재명", "품명", "item_name"],
        "quantity": ["수량", "입고수량", "qty", "quantity"],
        "unit": ["단위", "규격단위", "unit"],
        "unit_price": ["단가", "입고단가", "unit_price", "price"],
        "amount": ["공급가액", "매입금액", "금액", "amount", "total_price"],
        "tax": ["부가세", "세액", "tax", "vat"],
        "invoice_id": ["계산서번호", "전표번호", "invoice_id", "bill_no"]
    },
    "INVENTORY": {
        "business_date": ["조사일자", "실사일자", "일자", "date", "biz_date"],
        "item_id": ["품목코드", "자재코드", "item_id", "item_code", "코드"],
        "item_name": ["품목명", "자재명", "품명", "item_name"],
        "opening_qty": ["기초재고", "전일재고", "opening_qty", "start_qty"],
        "incoming_qty": ["입고량", "입고수량", "incoming_qty", "in_qty"],
        "sold_qty": ["판매량", "출고량", "sold_qty", "out_qty"],
        "service_qty": ["서비스량", "서비스수량", "service_qty"],
        "waste_qty": ["폐기량", "폐기수량", "waste_qty", "scrap_qty"],
        "staff_meal_qty": ["직원식사량", "직원식사", "staff_meal_qty"],
        "transfer_qty": ["이동수량", "이동량", "transfer_qty"],
        "theory_end_qty": ["이론재고", "장부재고", "theory_end_qty", "book_qty"],
        "actual_end_qty": ["실사재고", "실재고", "actual_end_qty", "real_qty"],
        "unit": ["단위", "unit"]
    }
}

class MappingEngine:
    """
    Deterministic Mapping Suggestion and Validation Engine.
    Uses canonical alias dictionaries to propose source-to-canonical mappings.
    Requires human confirmation before production execution.
    """
    @staticmethod
    def suggest_mapping(source_type: str, columns: List[str]) -> List[MappingSuggestionItem]:
        st = source_type.upper()
        alias_map = ALIAS_DICTIONARY.get(st, {})
        suggestions = []

        for col in columns:
            normalized = col.strip().lower().replace(" ", "").replace("_", "")
            matched_canonical = None
            confidence = "UNMAPPED"

            for canonical_field, aliases in alias_map.items():
                for alias in aliases:
                    alias_norm = alias.strip().lower().replace(" ", "").replace("_", "")
                    if normalized == alias_norm:
                        matched_canonical = canonical_field
                        confidence = "HIGH"
                        break
                    elif alias_norm in normalized or normalized in alias_norm:
                        if matched_canonical is None:
                            matched_canonical = canonical_field
                            confidence = "MEDIUM"
                if confidence == "HIGH":
                    break

            suggestions.append(MappingSuggestionItem(
                source_column=col,
                suggested_canonical_field=matched_canonical,
                confidence=confidence,
                status="SUGGESTED" if matched_canonical else "UNMAPPED"
            ))

        return suggestions

    @staticmethod
    def build_manifest(mapping_id: str, source_type: str, suggestions: List[MappingSuggestionItem], version: str = "1.0.0") -> MappingManifest:
        col_map = {}
        for s in suggestions:
            if s.suggested_canonical_field:
                col_map[s.source_column] = s.suggested_canonical_field

        return MappingManifest(
            mapping_id=mapping_id,
            source_type=source_type.upper(),
            mapping_version=version,
            status="SUGGESTED",
            column_mappings=col_map
        )

