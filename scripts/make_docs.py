#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

def save(path, text):
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8') as out:
        out.write(text.strip() + '\n')
    print('Generated:', path)

# 1. ARCHITECTURE.md
save('ARCHITECTURE.md', '''# ARCHITECTURE.md — DAMGA-OPS System Architecture

## 1. 시스템 개요 및 설계 철학
DAMGA-OPS는 **Harness Engineering** 원칙에 기반하여 설계된 외식업 경영 자동화 인텔리전스 시스템입니다.

> **핵심 철학**: “AI가 숫자를 만드는 시스템”이 아니라 **“정확한 계산 엔진(Facts Engine)이 산출한 사실을 AI가 경영 언어로 해석하는 시스템”**

---

## 2. 책임 분리 아키텍처 (Layered Architecture)

```
[Raw Sources: POS, Attendance, Purchases, Inventory, Reviews]
                           │
                           ▼
          ┌───────────────────────────────────┐
          │  Data Layer & Validation Gate     │ ➔ 누락/오류 시 DATA_INCOMPLETE 차단
          └───────────────────────────────────┘
                           │
                           ▼
          ┌───────────────────────────────────┐
          │  Facts Engine (Deterministic)     │ ➔ 코드/SQL 기반 100% 결정론적 계산
          └───────────────────────────────────┘
                           │
                           ▼
          ┌───────────────────────────────────┐
          │  Rule Engine (Threshold & Match)  │ ➔ 7대 Golden Anomaly 및 경보 탐지
          └───────────────────────────────────┘
                           │
                           ▼
          ┌───────────────────────────────────┐
          │  AI Analyst Layer (LLM)           │ ➔ 사실 해석, 원인 후보, 조치안 제안
          └───────────────────────────────────┘
                           │
                           ▼
          ┌───────────────────────────────────┐
          │  Human Approval & Cockpit UI      │ ➔ 대표/관리자 검토 및 실행 승인
          └───────────────────────────────────┘
                           │
                           ▼
          ┌───────────────────────────────────┐
          │  Evidence & Audit Store           │ ➔ 전 과정 추적성 및 재현성 보장
          └───────────────────────────────────┘
```

### 레이어별 세부 역할 및 제약
1. **Data Layer (`domains/*/data`)**:
   - 원천 CSV/XLSX 파일 수집, 스키마 검증, 결측치 필터링.
   - 필수 필드 누락 시 `DATA_INCOMPLETE` 반환 및 하위 프로세스 차단.
2. **Facts Engine (`domains/*/facts`)**:
   - 매출, 인건비율, 식재료 원가율, 공헌이익, 재고차이 등 경영 지표를 순수 함수로 계산.
   - LLM에 계산 위임 절대 금지.
3. **Rule Engine (`domains/*/rules`)**:
   - 사전 정의된 임계값(R-LAB-01, R-INV-01, R-FC-01, R-WST-01, R-CUS-01, R-DQ-01, R-PRO-01)에 따라 경보(Alert) 판정.
4. **AI Analyst Layer (`apps/api/ai`)**:
   - Facts와 Rules 결과 JSON을 입력받아 경영 언어로 1~2문장 요약, 원인 가설, 조치안 제시.
   - 출력에 반드시 Evidence ID와 비교 기준 명시.
5. **Evidence Store (`evidence/`)**:
   - 모든 계산 입력값, 룰 판정, AI 출력, 테스트 결과를 타임스탬프와 해시로 보존.

---

## 3. 디렉터리 구조 및 도메인 분할

```
DAMGA-OPS/
├─ AGENTS.md                  # 에이전트 작업 헌장 및 탐색 지도
├─ README.md                  # 프로젝트 개요 및 실행 가이드
├─ ARCHITECTURE.md            # 시스템 아키텍처 및 책임 분리 정의
├─ docs/                      # 세부 문서화
│  ├─ product/                # 마스터 명세서, KPI 정의, 대시보드 스펙
│  ├─ data/                   # 데이터 계약, 스키마, 마이그레이션 전략
│  ├─ operations/             # 관리자 워크플로우, 운영 런북
│  ├─ design-docs/            # 세부 설계 문서
│  ├─ exec-plans/             # 실행 계획 (active / completed)
│  └─ quality/                # 골든 원칙, 테스트 전략, 증거 정책
├─ apps/                      # 애플리케이션 계층
│  ├─ frontend/               # CEO Cockpit & Dashboard UI
│  └─ api/                    # REST / GraphQL API 백엔드
├─ domains/                   # 비즈니스 도메인 로직 (Facts & Rules)
│  ├─ sales/                  # 매출, 객수, 객단가, 시간대 분석
│  ├─ labor/                  # 근태, 근무시간, 인건비율, 생산성
│  ├─ food-cost/              # 식재료비, 매입단가, 원가율
│  ├─ inventory/              # 육류 입출고, 폐기, 재고 실사 차이
│  ├─ customer/               # 평점, 리뷰, 클레임 VOC
│  └─ management/             # 공헌이익, 경영 종합 요약
├─ data/                      # 데이터 저장소
│  ├─ synthetic/              # V2 골든 데이터셋 및 가상 데이터
│  └─ fixtures/               # 테스트용 단위 Mock Fixture
├─ tests/                     # 4계층 테스트 스위트
│  ├─ unit/                   # 계산식 단위 테스트
│  ├─ integration/            # 도메인 통합 테스트
│  ├─ golden/                 # GA-001 ~ GA-007 골든 시나리오 테스트
│  └─ e2e/                    # 대시보드 UI/승인 플로우 E2E 테스트
├─ scripts/                   # 빌드, 데이터 로더, 하네스 실행 스크립트
└─ evidence/                  # 실행 및 검증 증적(Evidence) 저장소
```
''')

# 2. README.md
save('README.md', '''# DAMGA-OPS (담가화로 업무자동화 대시보드)

> **Harness Engineering 기반 외식업 경영자동화 인텔리전스 시스템**  
> 연매출 42억원 · 재직 인원 65명 (단일 매장 기준)

---

## ⚠️ 데이터 상태 및 주의사항 (Important Notice)
- **현재 데이터 상태**: `100% Synthetic / Golden Dataset V2`
- 실제 담가화로구이 매장의 POS, 근태, 매입, 재고 데이터가 확보되기 전까지 모든 수치와 운영 조건은 **SYNTHETIC** 또는 **UNVERIFIED**로 취급됩니다.
- 본 시스템은 **결정론적 계산 엔진(Facts Engine)**과 **원인 해석 AI(AI Analyst)**의 책임을 엄격히 분리하여 숫자 환각(Hallucination)을 원천 차단합니다.

---

## 🚀 빠른 시작 (Quick Start)

### 1. 환경 요구사항
- Python 3.10+
- Git

### 2. 저장소 클론 및 설정
```bash
git clone <repository-url>
cd damga
```

### 3. 골든 하네스 테스트 실행
담가화로 7대 핵심 이상 징후(GA-001 ~ GA-007) 자동 검증:
```bash
python scripts/run_golden_tests.py
```

---

## 📂 프로젝트 구조
- **[AGENTS.md](AGENTS.md)**: AI 에이전트 작업 헌장 및 내비게이션 맵
- **[ARCHITECTURE.md](ARCHITECTURE.md)**: 책임 분리 및 레이어드 아키텍처
- **[docs/](docs/)**:
  - `product/`: [마스터 명세서](docs/product/master-specification-v1.0.md), [KPI 정의서](docs/product/kpi-definition.md)
  - `quality/`: [골든 원칙](docs/quality/golden-principles.md), [테스트 전략](docs/quality/golden-test-strategy.md)
  - `exec-plans/`: [실행 계획](docs/exec-plans/active/phase-1-bootstrap-and-facts.md)
- **[domains/](domains/)**: 매출, 인건비, 식재료비, 재고, 고객 도메인별 계산 및 룰 엔진
- **[tests/](tests/)**: 단위(Unit), 통합(Integration), 골든(Golden), E2E 테스트
- **[evidence/](evidence/)**: 테스트 실행 결과 및 감사 증적

---

## 🎯 7대 골든 이상 시나리오 (Ground Truth)
1. **GA-001**: 금요일 비피크 과잉 인력 투입 (`Labor_Ratio >= 33%`)
2. **GA-002**: 육류 실재고 부족 (`Variance_kg <= -5kg`)
3. **GA-003**: 한우 원가 압박 7일 지속 (`Food_Cost_Ratio >= 39%`)
4. **GA-004**: 육류 폐기량 급증 (`Waste / Sold >= 5%`)
5. **GA-005**: 매출 상승 대비 공헌이익 역행 악화
6. **GA-006**: 고객 클레임 급증 및 평점 하락
7. **GA-007**: 필수 데이터 누락 차단 (`DATA_INCOMPLETE`)
''')

# 3. docs/product/master-specification-v1.0.md
save('docs/product/master-specification-v1.0.md', '''# DAMGA-OPS | MASTER SPECIFICATION V1.0

## 담가화로 업무자동화 대시보드 MASTER SPECIFICATION V1.0
- **Baseline**: 연매출 42억원 · 재직 인원 65명 · Synthetic / Golden Dataset V2
- **문서상태**: DEVELOPMENT BASELINE
- **원칙**: 실제 POS·근태·매입·재고·회계자료 확보 전까지 모든 운영 수치는 SYNTHETIC 또는 UNVERIFIED로 취급한다.

---

### 0. 문서 통제 및 사용 원칙
| 항목 | 정의 |
| :--- | :--- |
| **문서 목적** | DAMGA-OPS의 제품·데이터·규칙·AI·테스트·운영 의사결정을 통제하는 최상위 개발 기준문서 |
| **현재 데이터 상태** | Synthetic-first. 실제 담가화로 데이터 미확보 상태 |
| **검증 기준 데이터** | `DAMGA_OPS_Golden_Dataset_V2.xlsx` |
| **변경 원칙** | 실데이터 확보 시 숫자·필드·임계값은 변경 가능하나 계산 책임 분리와 Audit/Evidence 원칙은 유지 |
| **AI 권한** | 설명·요약·원인 후보·조치 제안. 회계 수치 생성, 임의 보정, 직원 처분, 자동 인력감축은 금지 |
| **승인 권한** | 경영적 영향이 있는 조치는 관리자/대표의 Human Approval 필요 |

> **핵심 선언**: DAMGA-OPS는 “AI가 숫자를 만드는 시스템”이 아니라 “정확한 계산 엔진이 만든 사실을 AI가 경영 언어로 해석하는 시스템”으로 설계한다.

---

### 1. 프로젝트 정의
- **프로젝트명**: DAMGA-OPS (Damga Operations Intelligence & Automation System)
- **한 줄 정의**: POS·근태·매입·재고·메뉴원가·고객 데이터를 통합하여, 이상을 자동 탐지하고 원인과 예상 영향 및 조치안을 관리자에게 제시하는 담가화로 경영자동화 대시보드.

#### 1.1 비즈니스 기준선
- 연매출: 42억원 (`VERIFIED BY USER`)
- 월평균 매출: 약 3.5억원 (`DERIVED`)
- 재직 인원 Pool: 65명 (`VERIFIED BY USER`)
- 매장 수: 단일 매장 (`VERIFIED BY USER`)
- 식재료 관리기준: 32.5% (`SYNTHETIC`)
- 인건비 관리기준: 27.0% (`SYNTHETIC`)
- 테이블/좌석/임대료/영업시간: V1 가상값 사용 (`UNVERIFIED`)

#### 1.2 성공의 정의
1. 대표가 매일 매장에 상주하지 않아도 전일 실적과 핵심 이상을 3분 안에 파악할 수 있다.
2. 인건비·원가·재고·폐기·고객 이상을 사람이 엑셀을 뒤지기 전에 시스템이 먼저 포착한다.
3. 모든 경영 숫자는 재현 가능한 코드/SQL 계산식으로 산출되며, 원천 데이터까지 추적할 수 있다.
4. AI 설명은 반드시 근거 KPI, 기준값, 비교기간, Evidence ID를 포함한다.
5. 실데이터로 전환할 때 Synthetic 모듈을 교체하고도 UI·Rule·Test 구조가 유지된다.

---

### 2. 범위와 비범위
| 범위(In Scope) | 비범위(Out of Scope) |
| :--- | :--- |
| 매출·객수·객단가·시간대 분석 | POS 결제/주문 시스템 자체 개발 |
| 근태·근무시간·인건비 생산성 | 급여이체·세무신고 자동화 |
| 식재료 원가·매입단가·메뉴 공헌이익 | AI가 임의로 원가/매출 수치를 생성 |
| 육류 입고·수율·서비스·폐기·재고차이 | 재고차이를 절도/부정행위로 자동 판정 |
| 고객 리뷰·평점·클레임 추이 | 직원 자동평가·징계·해고 |
| 대표/관리자용 Dashboard 및 AI Brief | 대표 승인 없는 고위험 자동 실행 |
| CSV/XLSX 업로드 기반 MVP | 실데이터 연결 전 POS API 직접연동 보장 |

---

### 3. 책임 분리 아키텍처
`POS + Attendance + Purchases + Inventory + Menu Cost + Customer`  
→ `Raw/Staging` → `Validation (Data Gate)` → `Facts Engine` → `Rule Engine` → `Analytics` → `AI Briefing` → `Manager Approval/Action` → `Action Log` → `Outcome/Evidence` → `Feedback`

| Layer | 책임 | 금지사항 |
| :--- | :--- | :--- |
| **Data Layer** | 원천자료 수집, 스키마 검증, 정규화, 누락/중복 검출 | 원천값 임의 수정 |
| **Facts Engine** | 매출·비율·원가·공헌이익·재고차이 등 결정론 계산 | LLM 호출에 계산 위임 |
| **Rule Engine** | 임계값 및 비교규칙에 따라 경보 판정 | 근거 없는 추론 |
| **Analytics** | 요일/시간/메뉴/추세/분해 분석 | 원천데이터 없는 가설 확정 |
| **AI Analyst** | 사실 요약, 원인 후보, 조치안, 질문응답 | 숫자 생성·회계 사실 단정 |
| **Auditor** | Facts/Rules/AI 설명 일치성 독립 검증 | 검증 없는 PASS |
| **Evidence Store**| 입력·계산·경보·조치·테스트 결과 보존 | 추적 불가능한 결과 |

---

### 4. Golden Principles (GP-01 ~ GP-10)
- **GP-01 (No Hallucinated Numbers)**: AI는 숫자를 계산하거나 빈 값을 추정하지 않는다. 숫자는 Facts Engine에서만 생성한다.
- **GP-02 (Data Quality First)**: 필수 입력 누락/오류 시 분석을 BLOCK하고 `DATA_INCOMPLETE`를 반환한다.
- **GP-03 (Evidence Required)**: 모든 경보와 AI 설명은 Evidence ID와 계산근거를 가져야 한다.
- **GP-04 (Human Approval)**: 인력·구매·가격·재고조정 등 경영적 영향이 있는 실행은 승인 전 자동 적용하지 않는다.
- **GP-05 (No Accusation)**: 재고차이를 절도, 고의, 직원 과실로 단정하지 않는다. 확인이 필요한 이상으로만 표현한다.
- **GP-06 (Deterministic First)**: 계산 가능한 것은 코드/SQL로 처리하고 LLM은 비정형 해석에만 사용한다.
- **GP-07 (Explain Comparison)**: 경보는 무엇과 비교했는지(전주/4주 평균/목표/동요일)를 명시한다.
- **GP-08 (Synthetic Labeling)**: 가상 데이터와 실제 데이터를 UI/DB에서 명확히 구분한다.
- **GP-09 (Auditability)**: 원천→변환→계산→판정→설명→조치 이력의 역추적이 가능해야 한다.
- **GP-10 (Fail Safe)**: 판단이 불가능하면 조용히 정상처리하지 말고 `UNKNOWN`/`BLOCKED`로 실패한다.
''')

# 4. docs/quality/golden-principles.md
save('docs/quality/golden-principles.md', '''# Golden Principles (GP-01 ~ GP-10)

DAMGA-OPS 시스템 전반에서 타협 없이 지켜져야 하는 10대 핵심 엔지니어링 및 경영 원칙입니다.

---

### GP-01: No Hallucinated Numbers (숫자 환각 금지)
- **정의**: AI(LLM)는 매출, 원가, 인건비율, 재고량 등 어떠한 숫자도 직접 계산하거나 추측해서는 안 됩니다.
- **규칙**: 모든 수치는 `domains/*/facts`의 결정론적 코드(Python/SQL)에서만 계산되며, AI는 이미 계산된 JSON 수치만을 인용하여 해석합니다.

### GP-02: Data Quality First (데이터 품질 최우선 & Data Gate)
- **정의**: 필수 입력값에 결측(NULL), 형식 불일치, 비정상 음수값 등이 존재할 경우 파이프라인을 즉시 차단합니다.
- **규칙**: 결측치를 임의로 0이나 평균값으로 대체하지 않고 `DATA_INCOMPLETE` 경보를 발생시켜 관리자에게 데이터 입력을 요구합니다.

### GP-03: Evidence Required (모든 결과의 증거 보존)
- **정의**: 모든 경보(Alert), AI 브리핑, 계산 결과는 고유한 `Evidence ID`와 원천 데이터 추적 경로를 가집니다.
- **규칙**: `EV-DATA`, `EV-CALC`, `EV-RULE`, `EV-AI`, `EV-ACT` 체계로 모든 단계의 입출력을 저장합니다.

### GP-04: Human Approval (사람의 승인 필수)
- **정의**: 경영적·인사적 영향이 있는 모든 조치는 사람(점주/총괄관리자)의 명시적 승인(Approval)이 필요합니다.
- **규칙**: 인력 감축, 근무 스케줄 변경, 매입처 변경, 판매가 조정 등은 시스템이 제안(Recommendation)만 수행하며 자동 실행하지 않습니다.

### GP-05: No Accusation (부정행위 단정 금지)
- **정의**: 재고 부족, 로스, 계산 차이를 절도, 횡령, 근무태만 등의 부정행위로 단정하지 않습니다.
- **규칙**: “확인이 필요한 재고 불일치”, “실사 및 기록 대조 권고”와 같은 중립적이고 사실 기반의 운영 언어로만 표현합니다.

### GP-06: Deterministic First (결정론적 로직 우선)
- **정의**: 비즈니스 규칙과 KPI 산식은 100% 재현 가능한 코드로 구현합니다.
- **규칙**: 동일한 입력 데이터셋에 대해 Facts Engine과 Rule Engine은 항상 100% 동일한 결과를 반환해야 합니다.

### GP-07: Explain Comparison (비교 기준 명시)
- **정의**: 이상 징후나 경보를 제시할 때는 반드시 비교 대상(전주 동요일, 4주 이동평균, 목표치)을 명시합니다.
- **규칙**: 단순 "높음/낮음"이 아닌 `[실제값: 34.2% vs 목표기준: 27.0%]`와 같이 기준선 대비 편차를 제공합니다.

### GP-08: Synthetic Labeling (가상 데이터 식별)
- **정의**: 실데이터와 가상(Synthetic) 데이터를 시스템과 UI 전반에서 명확히 구분합니다.
- **규칙**: 실데이터 확보 전까지 모든 화면 및 리포트에 `SYNTHETIC BASELINE` 라벨을 노출합니다.

### GP-09: Auditability (완전한 감사 추적성)
- **정의**: 데이터 입력부터 변환, 계산, 경보 판정, AI 설명, 관리자 승인까지 전 과정의 감사 로그를 기록합니다.
- **규칙**: 언제, 누가, 어떤 규칙과 프롬프트 버전으로 결과를 도출했는지 역추적 가능해야 합니다.

### GP-10: Fail Safe (실패 시 안전 정지)
- **정의**: 판단이 모호하거나 규칙 충돌 발생 시 조용히 정상(OK)으로 넘기지 않고 `UNKNOWN` 또는 `BLOCKED`로 처리합니다.
- **규칙**: 실패 상황을 가시화하여 관리자의 개입을 유도합니다.
''')

# 5. docs/product/kpi-definition.md
save('docs/product/kpi-definition.md', '''# KPI Definition V1.0 (담가화로 경영 지표 정의서)

## 1. 핵심 경영 지표 목록

| KPI명 | 영문 필드명 | 도메인 | 산식 (Formula) | 단위 | 상태 | 비고 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **순매출** | `Sales` (`net_sales`) | Sales | SUM(item_price * qty - discount) | 원 (KRW) | `READY` | 기본 일일 실적 |
| **객수** | `Guests` | Sales | SUM(guest_count) | 명 | `READY` | 방문 고객 수 |
| **객단가** | `Avg_Check` | Sales | Sales / Guests | 원/명 | `READY` | 1인당 평균 결제액 |
| **인건비** | `Labor_Cost` | Labor | SUM(work_hours * hourly_wage + allowance) | 원 (KRW) | `READY` | 당일 총 인건비 |
| **인건비율** | `Labor_Ratio` | Labor | Labor_Cost / Sales | % | `READY` | 정상 기준: 27.0% |
| **식재료비** | `Food_Cost` | FoodCost | SUM(used_qty * unit_purchase_price) | 원 (KRW) | `READY` | 당일 식재료 원가 |
| **식재료 원가율** | `Food_Cost_Ratio` | FoodCost | Food_Cost / Sales | % | `READY` | 정상 기준: 32.5% |
| **공헌이익** | `Contribution` | Management | Sales - (Food_Cost + Labor_Cost) | 원 (KRW) | `READY` | 1차 영업 수익성 |
| **공헌이익률** | `Contribution_Ratio`| Management | Contribution / Sales | % | `READY` | 정상 기준: 약 40.5% |
| **입고량** | `Incoming_kg` | Inventory | SUM(incoming_weight) | kg | `READY` | 당일 육류 입고량 |
| **판매량** | `Sold_kg` | Inventory | SUM(menu_sold_qty * recipe_portion) | kg | `READY` | 레시피 기반 판매량 |
| **서비스량** | `Service_kg` | Inventory | SUM(service_portion) | kg | `READY` | 고객 서비스 제공량 |
| **폐기량** | `Waste_kg` | Inventory | SUM(waste_weight) | kg | `READY` | 손질 로스 및 변질 폐기 |
| **이론재고** | `Theory_End_kg` | Inventory | Prev_End + Incoming - (Sold + Service + Waste) | kg | `READY` | 계산상 잔여 재고 |
| **실사재고** | `Actual_End_kg` | Inventory | Physical Count Weight | kg | `READY` | 마감 실측 재고 |
| **재고차이** | `Variance_kg` | Inventory | Actual_End_kg - Theory_End_kg | kg | `READY` | 허용 오차: +-1.5kg |
| **폐기율** | `Waste_Ratio` | Inventory | Waste_kg / Sold_kg | % | `READY` | 경보 기준: >= 5.0% |
| **고객 평점** | `Rating` | Customer | Daily Average Star Rating | 점 (1~5) | `READY` | 정상 하한: 4.4점 |
| **리뷰 수** | `Review_Count` | Customer | SUM(new_reviews) | 건 | `READY` | 신규 등록 리뷰 수 |
| **클레임 건수** | `Complaints` | Customer | SUM(complaint_voc_count) | 건 | `READY` | 경보 기준: >= 5건/일 |

---

## 2. Phase 2 확장 KPI (NEXT / UNVERIFIED)
- `Hourly_Sales_Per_Labor`: 시간당 인력 매출 (`sales / labor_hours`)
- `Menu_Contribution_Margin`: 메뉴별 개별 공헌이익 (`price - standard_cost`)
- `Meat_Yield_Rate`: 육류 손질 수율 (`usable_weight / raw_weight`)
- `Complaint_Per_Guest`: 객수 대비 클레임 발생률 (`complaints / guests`)
''')

# 6. docs/quality/golden-test-strategy.md
save('docs/quality/golden-test-strategy.md', '''# Golden Dataset Test Strategy & Harness Specification

DAMGA-OPS 시스템의 핵심 이상 탐지 정확성과 안전성을 보장하기 위한 테스트 전략 문서입니다.

---

## 1. 7대 골든 시나리오 (Golden Anomalies) & 테스트 하네스 매핑

| Test ID | Anomaly ID | 대상 일자 | 도메인 | 등급 | 탐지 조건 (Rule) | 정답 시나리오 (Ground Truth) | 안전/통과 기준 (Pass Criteria) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **HT-001** | **GA-001** | 2026-06-12 | Labor | `HIGH` | `Labor_Ratio >= 33%` | 금요일 비피크 과잉 인력 투입 | GA-001 탐지 + 원인 설명 + 인력 재배치 권고 (자동감원 금지) |
| **HT-002** | **GA-002** | 2026-06-24 | Inventory | `CRITICAL` | `Variance_kg <= -5.0` | 육류 실재고 6.2kg 부족 | CRITICAL 경보 + 재실사/기록대조 권고 (부정행위 단정 금지) |
| **HT-003** | **GA-003** | 2026-07-07 ~ 2026-07-13 | FoodCost | `HIGH` | `Food_Cost_Ratio >= 39%` (7일 지속) | 한우 매입 원가 상승 시나리오 | 7일간의 기간성 원가 이상을 단일 패턴으로 인지 + 단가/메뉴믹스 검토 |
| **HT-004** | **GA-004** | 2026-07-18 | Waste | `HIGH` | `Waste_kg / Sold_kg >= 5%` | 육류 폐기량 급증 | 폐기율 급증 탐지 + 보관/손질/FIFO 점검 권고 |
| **HT-005** | **GA-005** | 2026-08-01 ~ 2026-08-07 | Profit | `HIGH` | 매출 상승 대비 공헌이익률 급락 | 매출 증가에도 비용 동반 급등 | 매출 증가만 긍정 평가하지 않고 수익성 역행 이상 탐지 |
| **HT-006** | **GA-006** | 2026-08-15 | Customer | `MEDIUM` | `Complaints >= 5 OR Rating < 4.2` | 클레임 8건 / 평점 4.08 발생 | 평점 악화와 클레임 동시 분석 + VOC 원인 분류 |
| **HT-007** | **GA-007** | 2026-08-21 | DataQuality | `CRITICAL` | 필수 KPI NULL (식재료비 누락) | 식재료 원가 입력 누락 | 임의 추정 계산 금지 + `DATA_INCOMPLETE`로 즉시 차단 |

---

## 2. 테스트 실행 계층 (Test Pyramid)

```
       [ E2E / Dashboard Flow Tests ]        ➔ 대시보드 및 승인 UI 흐름 검증
     [ Golden Harness Tests (HT-001~007) ]   ➔ 7대 골든 이상 시나리오 정확성 검증
   [ Integration Tests (Data→Facts→Rules) ] ➔ 파이프라인 연계 및 데이터 품질 Gate
 [ Unit Tests (Deterministic Calculation) ]  ➔ 개별 KPI 산식 및 순수 함수 검증
```

---

## 3. 테스트 통과 및 Done 기준
1. `HT-001 ~ HT-007` 골든 테스트 100% PASS.
2. 미탐(False Negative) 및 오탐(False Positive) 제로.
3. 모든 테스트 결과가 `evidence/` 디렉터리에 타임스탬프와 함께 자동 기록.
''')

# 7. docs/exec-plans/active/phase-1-bootstrap-and-facts.md
save('docs/exec-plans/active/phase-1-bootstrap-and-facts.md', '''# Execution Plan: Phase 1 — Harness Bootstrap & Facts Engine

- **상태**: `ACTIVE`
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

### Task 3: Facts Engine Core 구현 (다음 단계)
- [ ] `domains/sales/facts.py` (매출, 객수, 객단가 계산식)
- [ ] `domains/labor/facts.py` (인건비, 인건비율 계산식)
- [ ] `domains/food-cost/facts.py` (식재료비, 원가율 계산식)
- [ ] `domains/inventory/facts.py` (이론재고, 폐기율, 재고차이 계산식)
- [ ] `domains/customer/facts.py` (평점, 클레임 집계)
- [ ] `domains/management/facts.py` (공헌이익, 공헌이익률)

### Task 4: Rule Engine Core 구현 (다음 단계)
- [ ] `domains/*/rules.py` (R-LAB-01, R-INV-01, R-FC-01, R-WST-01, R-CUS-01, R-DQ-01, R-PRO-01)
- [ ] Data Quality Gate (`R-DQ-01`) 우선 검증 파이프라인

---

## 3. 완료 판정 기준 (Acceptance Criteria)
- [x] 저장소 디렉터리 및 문서화 100% 일치
- [x] Golden Dataset V2 데이터 로드 및 7대 시나리오 스켈레톤 통과
- [x] 증적(`evidence/EV-BOOTSTRAP-*.json`) 생성
''')

print('make_docs execution complete.')

