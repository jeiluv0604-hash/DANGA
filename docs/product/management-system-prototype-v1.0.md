# 담가화로구이 경영체계 프로토타입 명세 V1.0

## 1. 목적

본 기능은 실제 사용 전 검증을 위한 프로토타입이다. 모든 운영·재무·메뉴·조직·조치 데이터는 `SYNTHETIC`이며 실제 담가화로구이 매장 실적이 아니다.

시스템 명칭과 화면 브랜드는 `담가화로구이`를 사용한다.

## 2. 정책 상태

다음 정책은 사용자 승인 전까지 모두 `UNVERIFIED POLICY`다.

1. 월 손익 비용 계정 및 부문별 배부 기준
2. 메뉴 ABCD의 판매량·영업이익 표시값 높음/낮음 기준
3. 총괄점장·관리자 Scorecard 가중치

프로토타입은 검증용 Synthetic 정책값으로 계산할 수 있지만 실제 운영정책으로 표현하거나 자동 실행에 사용하지 않는다.

## 3. 구현 범위

- 6개월 Synthetic Management Dataset
- 월 손익 및 영업이익
- Budget vs Actual
- Cash Flow
- Recipe/BOM 원가
- Menu ABCD Engineering
- 조직 역할과 보고선
- 관리자 Scorecard
- SOP/Checklist 원본 API(대시보드 미표시)
- Action Closure (`OPEN -> IN_PROGRESS -> CLOSED -> VERIFIED`)
- 월간 Management Review 원본 API(대시보드 미표시)
- 오늘 매출 최상단 및 6개 탭형 CEO Cockpit
- 전체 대시보드 하단의 간소화된 AI 경영분석 및 의사결정 지원

사용자 화면에서는 기존 `공헌이익` 용어를 `영업이익`으로 표시한다. 기존 API·계산 호환성을 위해 내부 필드명 `contribution`은 유지한다.

## 4. 안전 경계

- 자동 가격 변경: 금지
- 자동 발주·지급: 금지
- 자동 직원 평가·승진·보상·징계·해고: 금지
- AI의 숫자 계산: 금지
- 승인 없는 경영행위 실행: 금지
- 실제 세무 신고·M&A·지분승계 실행: 범위 밖

## 5. Truth Source

`Synthetic Input -> Deterministic Facts -> Rules -> Management Review -> Human Approval -> Action -> Evidence`

프런트엔드와 AI는 Truth Source가 아니다.
