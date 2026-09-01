# DAMGA-OPS | MASTER SPECIFICATION V1.0

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
