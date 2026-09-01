# Management System Synthetic Data Contract V1.0

## 공통 필드

- `brand_name = 담가화로구이`
- `dataset_type = SYNTHETIC`
- `policy_status = UNVERIFIED POLICY`
- 금액 단위: integer KRW
- 비율: numerator와 denominator에서 결정론적으로 계산한 소수
- 결측: `None` 유지, 0으로 대체 금지

## 월 손익

`Operating Profit = Sales - Food Cost - Labor Cost - Rent - Utilities - Card/Platform Fees - Other Expenses`

필수 비용 중 하나라도 누락되면 `operating_profit = None`, `data_status = DATA_INCOMPLETE`다. 매출 등 독립 관측치는 보존한다.

## 현금흐름

`Ending Cash = Beginning Cash + Cash Inflows - Cash Outflows`

손익과 현금흐름은 별도 Truth로 관리한다.

## Recipe/BOM

`Effective Quantity = Standard Quantity / Yield Rate`

`Ingredient Cost = Effective Quantity * Applied Unit Price`

`Menu Standard Cost = SUM(Ingredient Cost)`

재료의 사용량·단가·수율 중 하나라도 누락되면 메뉴 원가는 `DATA_INCOMPLETE`다.

## Menu ABCD

현재 프로토타입은 Synthetic 중앙값 기준을 사용한다. 실제 기준으로 승인되지 않았으므로 상태는 항상 `UNVERIFIED POLICY`다.

## Action Closure

주 경로는 `OPEN -> IN_PROGRESS -> CLOSED -> VERIFIED`다. 모든 상태변경은 actor, timestamp, previous status, new status, comment 및 SHA-256 감사 이벤트를 남긴다.

