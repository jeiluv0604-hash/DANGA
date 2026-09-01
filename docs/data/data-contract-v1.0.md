# DAMGA-OPS Data Contract V1.0

## 1. 개요 및 원칙
본 문서는 DAMGA-OPS 시스템의 데이터 품질 계약(Data Contract)을 정의합니다.
Golden Principle **GP-02(Data Quality First)** 및 **GP-10(Fail Safe)**에 따라, 필수 필드의 누락·타입 오류·비정상 값 발생 시 Facts Engine 실행 전에 즉시 파이프라인을 차단(`DATA_INCOMPLETE`)합니다.

---

## 2. 결측치(Missing) vs 실제 0(Zero)의 엄격한 분리
- **`0` (Zero)**: 실제 관측된 값이 0인 상태 (예: 당일 클레임 0건, 당일 폐기량 0.0kg, 입고량 0.0kg).
- **`NULL / None / "" / NaN` (Missing)**: 데이터가 누락되거나 입력되지 않은 상태.
- **원칙**: 결측치를 절대로 `0`, 평균값, 또는 이전 일자 값으로 임의 대체하거나 보정하지 않습니다.

---

## 3. 필드별 Data Contract Specification

| Field Name | Domain | Type | Required | Nullable | Min | Max | Unit | Description | Failure Behavior |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| `Date` | Common | date / int | **Yes** | No | 1 | - | - | 영업 일자 (YYYY-MM-DD 또는 Serial) | `DATA_INCOMPLETE` 차단 |
| `Sales` | Sales | numeric | **Yes** | No | 0 | - | KRW (원) | 당일 순매출액 | `DATA_INCOMPLETE` 차단 |
| `Guests` | Sales | integer | **Yes** | No | 1 | - | 명 | 당일 총 방문 객수 | `DATA_INCOMPLETE` 차단 |
| `Labor_Cost` | Labor | numeric | **Yes** | No | 0 | - | KRW (원) | 당일 총 인건비 지급액 | `DATA_INCOMPLETE` 차단 |
| `Food_Cost` | FoodCost | numeric | **Yes** | No | 0 | - | KRW (원) | 당일 식재료 사용 원가 | `DATA_INCOMPLETE` 차단 |
| `Incoming_kg` | Inventory | numeric | **Yes** | No | 0 | - | kg | 당일 육류 총 입고 중량 | `DATA_INCOMPLETE` 차단 |
| `Sold_kg` | Inventory | numeric | **Yes** | No | 0 | - | kg | 당일 육류 레시피 기준 판매 중량 | `DATA_INCOMPLETE` 차단 |
| `Service_kg` | Inventory | numeric | No | Yes | 0 | - | kg | 고객 서비스 제공 중량 (기본값 0.0kg) | 유효성 검사 실패 시 차단 |
| `Waste_kg` | Inventory | numeric | **Yes** | No | 0 | - | kg | 손질 및 변질 폐기 중량 | `DATA_INCOMPLETE` 차단 |
| `Actual_End_kg` | Inventory | numeric | **Yes** | No | 0 | - | kg | 마감 시점 물리적 실사 재고 중량 | `DATA_INCOMPLETE` 차단 |
| `Theory_End_kg` | Inventory | numeric | No | Yes | 0 | - | kg | 시스템 계산/제공 이론재고 | 미제공 시 Facts에서 계산 |
| `Rating` | Customer | numeric | No | Yes | 0.0 | 5.0 | 점 (0~5) | 당일 고객 리뷰 평균 평점 | 결측 시 `None` (0으로 채우지 않음) |
| `Review_Count` | Customer | integer | No | Yes | 0 | - | 건 | 당일 신규 등록 리뷰 수 | 결측 시 `None` (0으로 채우지 않음) |
| `Complaints` | Customer | integer | No | Yes | 0 | - | 건 | 당일 접수된 고객 불만/클레임 건수 | 결측 시 `None` (0으로 채우지 않음) |

---

## 4. 검증 Gate 실패 및 Partial Facts 처리 절차 (Phase 2.1 Hardening)
1. `domains/data_quality/gate.py`의 `validate_required_fields()`가 유효성 검사를 수행합니다.
2. Required 필드 누락 또는 타입/범위 오류 발견 시:
   - `data_status: "DATA_INCOMPLETE"`, `blocked: True`, `ai_eligible: False` 반환.
   - `R-DQ-01` 경보(CRITICAL)를 발행하고 Evidence Index와 1:1 연결합니다.
3. **Partial Facts 원칙**:
   - 누락되지 않은 독립 관측치(Sales, Guests, Labor_Cost 등)는 폐기하지 않고 정상 산출 및 저장합니다 (`kpi_status: "AVAILABLE"`).
   - 누락된 필드에 종속된 지표(Food_Cost_Ratio, Contribution 등)만 `Null`로 보존합니다 (`kpi_status: "BLOCKED_DEPENDENCY"`).
4. **Summary 독립 분모 집계**:
   - 기간 집계 시 결측 일자를 일괄 삭제하지 않고, 각 지표별 유효 관측 일수를 분모로 집계하며 `coverage` 메타데이터를 제공합니다.


