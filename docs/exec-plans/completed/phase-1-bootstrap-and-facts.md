# Execution Plan: Phase 1 — Harness Bootstrap & Facts Engine

- **상태**: `COMPLETED`
- **시작일**: 2026-09-01
- **책임자**: DAMGA-OPS Lead Engineer Agent

---

## 1. 목표 (Goal)
Harness Engineering 기반 프로젝트 저장소 구조를 완비하고, 골든 데이터셋(V2)을 기반으로 결정론적 Facts Engine 및 7대 이상 징후 검증 테스트 하네스를 구축한다.

---

## 2. 세부 태스크 (Tasks)

### Task 1: Repository & Harness Bootstrap (완료)
- [x] 표준 디렉터리 구조 (`domains/`, `docs/`, `apps/`, `tests/`, `evidence/` 등) 생성
- [x] `AGENTS.md`, `ARCHITECTURE.md`, `README.md` 작성
- [x] Golden Principles 및 KPI 정의서, 마스터 명세서 동기화
- [x] 골든 데이터셋(`DAMGA_OPS_Golden_Dataset_V2.xlsx`, JSON) 적재

### Task 2: Golden Dataset Loader & Test Runner 구축 (완료)
- [x] `scripts/run_golden_tests.py` 하네스 테스트 스크립트 작성
- [x] `tests/golden/test_golden_anomalies.py` 골든 7대 시나리오 검증 러너 작성
- [x] 첫 실행 및 Evidence 생성

### Task 3: Facts Engine Core 구현 (완료)
- [x] `domains/sales/facts.py` (매출, 객수, 객단가 결정론적 계산식)
- [x] `domains/labor/facts.py` (인건비, 인건비율 결정론적 계산식)
- [x] `domains/food_cost/facts.py` (식재료비, 원가율 결정론적 계산식)
- [x] `domains/inventory/facts.py` (이론재고, 폐기율, 재고차이 결정론적 계산식)
- [x] `domains/customer/facts.py` (평점, 클레임 집계)
- [x] `domains/management/facts.py` (공헌이익, 공헌이익률)
- [x] `domains/data_quality/gate.py` (GP-02, GP-10 Data Quality Gate)

### Task 4: Rule Engine & Real Golden Harness 구현 (완료)
- [x] `domains/rules.py` (R-DQ-01, R-LAB-01, R-INV-01, R-FC-01, R-WST-01, R-CUS-01, R-PRO-01)
- [x] `domains/pipeline.py` (Data Gate -> Facts -> Rules -> Alerts -> Evidence 통합 파이프라인)
- [x] `tests/unit/` (Facts, Data Quality, Rules 단위 테스트 35건 100% PASS)
- [x] `tests/integration/` (92일 파이프라인 통합 테스트 PASS)
- [x] `tests/golden/test_real_golden_harness.py` (GA-001 ~ GA-007 실제 탐지 100% PASS)
- [x] Zero Test Leakage 검증 (Expected_Anomaly_ID 입력 차단)
- [x] 세분화된 Evidence 생성 (`EV-FACTS`, `EV-RULES`, `EV-INTEGRATION`, `EV-GOLDEN`)

---

## 3. 완료 판정 기준 (Acceptance Criteria)
- [x] 저장소 디렉터리 및 문서화 100% 일치
- [x] Golden Dataset V2 데이터 로드 및 7대 시나리오 스켈레톤 통과
- [x] Facts Engine 및 Rule Engine 결정론적 구현 완료
- [x] 단위/통합/골든 하네스 테스트 35건 전체 통과 (REAL GOLDEN DETECTION TEST = PASS)
- [x] 92일간 Clean Day 오탐(False Positive) 0건 확인
- [x] 증적(`evidence/EV-FACTS-*.json`, `evidence/EV-RULES-*.json`, `evidence/EV-INTEGRATION-*.json`, `evidence/EV-GOLDEN-*.json`) 생성

