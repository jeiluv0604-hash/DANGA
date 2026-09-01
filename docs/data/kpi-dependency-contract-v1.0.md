# DAMGA-OPS KPI Dependency Contract Specification v1.0

> **문서 상태**: APPROVED (Phase 2.1)  
> **최종 수정일**: 2026-09-01  
> **최상위 원칙**: GP-01 (No Hallucinated Numbers), GP-02 (No Data Forgery), GP-10 (Strict Quality Gate)

---

## 1. 개요 (Overview)
본 문서는 DAMGA-OPS에서 산출되는 모든 일일 경영 KPI 및 파생 지표가 요구하는 원천 입력 데이터 필드(Raw Dependencies)와 종속성 전파 규칙(Dependency Propagation Rules)을 명문화합니다.

---

## 2. 부분 데이터 무결성 원칙 (Partial Facts Principle)
1. **독립 관측치 보존 (Observed Fact Preservation)**: 특정 필수 필드가 누락되거나 오류가 있더라도, 해당 필드에 의존하지 않는 독립적인 다른 관측치(예: Sales, Guests, Labor_Cost)는 임의로 폐기하거나 Null 처리하지 않고 있는 그대로 산출 및 보존합니다.
2. **종속 계산 차단 (Dependent Calculation Blocking)**: 누락된 필드를 선행 조건(Prerequisite)으로 요구하는 파생 지표(예: Food_Cost_Ratio, Contribution)만 `Null`로 처리하며, 가짜 대체값(0, 평균값)을 절대 주입하지 않습니다.
3. **거버넌스 차단 (Governance Blocking)**: 필수 데이터 누락이 단 1건이라도 발생한 날짜는 `data_status = "DATA_INCOMPLETE"`, `blocked = True`, `ai_eligible = False`로 표기하여 자동 의사결정 및 AI 추천 생성을 안전하게 차단합니다.

---

## 3. 필드별 종속성 매트릭스 (Field Dependency Matrix)

| KPI 지표명 | 필수 입력 필드 (Direct Inputs) | 선행 계산 지표 (Prerequisites) | 결측 시 실패 처리 (Failure Behavior) | KPI 상태 코드 |
| :--- | :--- | :--- | :--- | :--- |
| **Sales** | `Sales` | 없음 | `Null` | `MISSING_INPUT` |
| **Guests** | `Guests` | 없음 | `Null` | `MISSING_INPUT` |
| **Avg_Check** | `Sales`, `Guests` | `sales`, `guests` | `Null` | `BLOCKED_DEPENDENCY` |
| **Labor_Cost** | `Labor_Cost` | 없음 | `Null` | `MISSING_INPUT` |
| **Labor_Ratio** | `Labor_Cost`, `Sales` | `labor_cost`, `sales` | `Null` | `BLOCKED_DEPENDENCY` |
| **Food_Cost** | `Food_Cost` | 없음 | `Null` | `MISSING_INPUT` |
| **Food_Cost_Ratio** | `Food_Cost`, `Sales` | `food_cost`, `sales` | `Null` | `BLOCKED_DEPENDENCY` |
| **Incoming_kg** | `Incoming_kg` | 없음 | `Null` | `MISSING_INPUT` |
| **Sold_kg** | `Sold_kg` | 없음 | `Null` | `MISSING_INPUT` |
| **Service_kg** | `Service_kg` (Optional) | 없음 | `Null` (0으로 자동대체 금지) | `NOT_PROVIDED` (0 입력시 `AVAILABLE`) |
| **Waste_kg** | `Waste_kg` | 없음 | `Null` | `MISSING_INPUT` |
| **Waste_Ratio** | `Waste_kg`, `Sold_kg` | `waste_kg`, `sold_kg` | `Null` | `BLOCKED_DEPENDENCY` |
| **Actual_End_kg** | `Actual_End_kg` | 없음 | `Null` | `MISSING_INPUT` |
| **Theory_End_kg** | `Theory_End_kg` 또는 (입고/판매/서비스/폐기) | `incoming`, `sold`, `service`, `waste` | `Null` (직접입력 시 보존) | `AVAILABLE` 또는 `BLOCKED_DEPENDENCY` |
| **Variance_kg** | `Actual_End_kg`, `Theory_End_kg` | `actual_end_kg`, `theory_end_kg` | `Null` | `BLOCKED_DEPENDENCY` |
| **Rating** | `Rating` (Optional) | 없음 | `Null` (0점 대체 금지) | `NOT_PROVIDED` (평점입력시 `AVAILABLE`) |
| **Complaints** | `Complaints` (Optional) | 없음 | `Null` (0건 대체 금지) | `NOT_PROVIDED` (0건입력시 `AVAILABLE`) |
| **Review_Count** | `Review_Count` (Optional) | 없음 | `Null` (0건 대체 금지) | `NOT_PROVIDED` (0건입력시 `AVAILABLE`) |
| **Contribution** | `Sales`, `Food_Cost`, `Labor_Cost` | `sales`, `food_cost`, `labor_cost` | `Null` | `BLOCKED_DEPENDENCY` |
| **Contribution_Ratio**| `Sales`, `Food_Cost`, `Labor_Cost` | `contribution`, `sales` | `Null` | `BLOCKED_DEPENDENCY` |


---

## 4. Summary 기간 집계 독립성 (Aggregation Independence)
- **독립 분모 원칙**: 기간 집계(Summary API) 시 `DATA_INCOMPLETE` 일자 전체를 배제하지 않고, 각 지표별로 `AVAILABLE` 상태인 일자들의 관측치만을 유효 분모(Denominator)로 삼아 정확하게 집계합니다.
- **Coverage 메타데이터**: 모든 기간 집계 응답은 지표별 `available_days`와 `total_days`를 명시하여 데이터 신뢰도를 투명하게 보고합니다.

