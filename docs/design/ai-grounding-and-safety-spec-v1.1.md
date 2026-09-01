# AI Grounding & Safety Specification v1.1

## 1. 개요
DAMGA-OPS AI Analyst Layer는 LLM의 환각(Hallucination), 의미 왜곡(Semantic Swap), 주입 공격(Prompt Injection)을 원천 차단하기 위해 다단계 검증 시스템을 갖춥니다.

## 2. Semantic FactRef Grounding (GROUND-01 ~ 06)
- **원칙**: 단순 숫자 일치가 아닌 지표명(metric), 수치(value), 영업일자(business_date), 증적 ID(evidence_id)가 Facts Engine 산출물과 100% 일치해야 함.
- **차단 대상**:
  - GROUND-01: 매출액을 인건비로 주장하는 수치 전용 왜곡
  - GROUND-02: 인건비율을 식재료 원가율로 주장하는 비율 전용 왜곡
  - GROUND-03: 과거/미래 날짜의 수치를 당일 수치로 주장하는 일자 불일치
  - GROUND-04: 미존재 증적 ID 바인딩
  - GROUND-05: 미정의 가상 지표명 사용

## 3. Provider Failure Contract (PROVIDER-01 ~ 08)
- **Silent Fallback 금지**: OpenAI 호출 실패 시 조용히 MOCK으로 전환하지 않고 status=PROVIDER_UNAVAILABLE, ctual_provider=none, 명시적 allback_reason을 반환.
- **명시적 Fallback 허용 조건**: 시스템 구성 시 명시적으로 llow_fallback=True가 지정된 경우에만 allback_used=True, ctual_provider=mock 기록 후 폴백 허용.
