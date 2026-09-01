# AGENTS.md — DAMGA-OPS Agent Guide

> **담가화로 업무자동화 대시보드 (DAMGA-OPS) 에이전트 작업 헌장**  
> 이 문서는 DAMGA-OPS 코드베이스를 탐색하고 작업하는 모든 AI 에이전트의 행동 기준이자 내비게이션 지도입니다.

---

## 1. 프로젝트 미션 (Mission)
- **목적**: 담가화로구이(단일 매장, 연매출 42억원, 인원 풀 65명 기준)의 POS, 근태, 매입, 재고, 고객 데이터를 통합하여 매일 3분 안에 이상을 감지하고 경영 의사결정을 지원하는 자동화 시스템 구축.
- **최상위 원칙**: docs/product/master-specification-v1.0.md 가 모든 결정의 최상위 기준이며, data/synthetic/DAMGA_OPS_Golden_Dataset_V2.xlsx 가 검증용 Ground Truth입니다.

---

## 2. 절대 금지 사항 (NEVER Rules)
1. **No Hallucinated Numbers (GP-01)**: 숫자를 LLM이 임의로 계산하거나 추정하지 마십시오. 모든 수치는 Facts Engine(코드/SQL)에서만 산출합니다.
2. **No Data Forgery (GP-02)**: 필수 데이터가 누락되거나 오류가 있으면 추정치로 채우지 말고 반드시 DATA_INCOMPLETE로 중단(Block)하십시오.
3. **No Accusations (GP-05)**: 재고 차이나 수치 불일치를 절도, 횡령, 직원 과실로 단정하지 마십시오. 확인 요청 대상 이상(Anomaly)으로만 기술하십시오.
4. **No Unauthorized Execution (GP-04)**: 인력 감원, 급여/가격 변경, 발주 변경 등 경영적 영향이 있는 조치를 사람의 승인 없이 자동 실행하지 마십시오.
5. **No Blind Pass**: 테스트와 감사(Audit) 검증을 거치지 않은 기능은 절대 완료(DONE)로 처리하지 마십시오.

---

## 3. 핵심 문서 색인 (Documentation Map)
- **마스터 명세서**: docs/product/master-specification-v1.0.md
- **아키텍처 & 레이어**: ARCHITECTURE.md
- **골든 원칙 (GP-01~10)**: docs/quality/golden-principles.md
- **KPI 정의서**: docs/product/kpi-definition.md
- **골든 테스트 전략**: docs/quality/golden-test-strategy.md
- **실행 계획**: docs/exec-plans/active/ 및 docs/exec-plans/completed/

---

## 4. 에이전트 작업 루프 (Harness Engineering Loop)
모든 기능 개발은 아래 순서를 엄격히 준수합니다:
1. **Plan**: 관련 명세 및 테스트 기준을 확인하고 docs/exec-plans/active/ 에 실행 계획 수립.
2. **Deterministic Implementation**: 도메인 로직 및 계산식을 domains/ 에 결정론적 코드(Python/SQL/TS)로 작성.
3. **Automated Verification**: tests/unit/, tests/golden/ 실행 및 PASS 확인 (GA-001 ~ GA-007 필수).
4. **Evidence Generation**: 검증 결과 및 실행 로그를 evidence/ 에 저장.
5. **Documentation & Review**: 미확정 항목은 UNVERIFIED 표기 후 완료된 계획을 docs/exec-plans/completed/ 로 이동.

---

## 5. 미확정 항목 (Unknowns) 처리
- 실제 매장 POS/근태/매입 데이터가 확보되지 않은 상태입니다.
- 가상 데이터는 UI 및 코드에서 항상 SYNTHETIC 또는 UNVERIFIED로 명시하십시오.
