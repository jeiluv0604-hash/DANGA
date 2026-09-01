# -*- coding: utf-8 -*-
import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
    print('Wrote:', path)

write_file('docs/product/ceo-cockpit-spec-v1.0.md', """# docs/product/ceo-cockpit-spec-v1.0.md — DAMGA-OPS CEO Cockpit Product Specification

> **담가화로구이 CEO Cockpit 웹 대시보드 제품 명세서 (Version 1.0)**  
> 기준: 단일 매장, 연매출 42억원, 일일 매출 ~1,150만원, 좌석 회전율 1.5~2.5회

---

## 1. 제품 비전 및 목적
DAMGA-OPS CEO Cockpit은 담가화로구이 대표가 **매일 아침 3분 안에 매장의 경영 이상을 감지하고 데이터에 기반한 의사결정을 내릴 수 있도록 돕는 경영 인텔리전스 인터페이스**입니다.

---

## 2. 최상위 원칙 및 제약

1. **Backend = Truth, Frontend = Presentation (GP-01)**:
   - 프론트엔드는 어떠한 비즈니스 수식(인건비율, 식재료 원가율, 공헌이익, 재고차이 등)도 직접 계산하지 않습니다.
   - 모든 수치와 상태는 Backend REST API (`/api/v1/*`)로부터 제공받은 Facts 및 Alerts를 그대로 표현합니다.
2. **SYNTHETIC DATA Badge 상시 노출**:
   - 현재 데이터는 가상(Synthetic) 데이터이므로, 화면 최상단에 `SYNTHETIC · 실제 매장 데이터 아님` 배지를 상시 고정 표시합니다.
3. **Missing != Zero Semantics (GP-02)**:
   - `0` (유효한 숫자 0): `0원`, `0건`, `0.0kg` 등으로 명확히 표시.
   - `MISSING_INPUT` (원천 누락): `"데이터 없음"`으로 표시.
   - `BLOCKED_DEPENDENCY` (선행 데이터 부재로 계산 불가): `"계산 불가"`로 표시.
   - `NOT_PROVIDED` (선택 입력 미입력): `"미입력"`으로 표시.
4. **DATA_INCOMPLETE 처리 원칙 (Partial Facts)**:
   - 특정 일자에 데이터 누락(예: `2026-08-21` Food Cost 누락)이 발생해도, 매출·인건비·재고·고객 평점 등 **독립 관측치는 정상 표시**하며 전체 화면을 블라인드 처리하지 않습니다.
   - 누락 및 계산 불가 항목에 대해서만 Warning Banner와 `계산 불가` 라벨을 적용합니다.
5. **표현 윤리 및 단정 금지 (GP-05)**:
   - 재고 이상 또는 수치 불일치에 대해 절도, 횡령, 직원 문제 등의 표현을 절대 사용하지 않으며, `"재고 차이 확인 필요"`, `"실사 확인 권고"`로 기술합니다.

---

## 3. 화면 레이아웃 및 핵심 컴포넌트 구성

```
+----------------------------------------------------------------------------------------+
| Header: [DAMGA] 담가화로구이 CEO Cockpit | [◀ 이전일] [2026-08-31 📅] [다음일 ▶] | [SYNTHETIC 배지] |
+----------------------------------------------------------------------------------------+
| (DATA_INCOMPLETE 시만 노출) ⚠️ 경고 배너: 필수 데이터 누락 안내 (독립 지표 정상 보존)      |
+----------------------------------------------------------------------------------------+
| [4대 핵심 Hero KPI 그리드]                                                             |
| 1. 오늘 매출 (Sales & 객수, 객단가)                                                    |
| 2. 인건비율 (Labor Ratio & 인건비액, 기준 33%)                                         |
| 3. 식재료 원가율 (Food Cost Ratio & 식재료비, 기준 38%)                                 |
| 4. 공헌이익 (Contribution & 공헌이익률)                                                 |
+----------------------------------------------------------------------------------------+
| [최근 7일 경영 추세 차트 (Recharts)]                                                   |
| - 매출 & 공헌이익 추이 (만원) / 인건비율 & 원가율 추이 (%) (결측 일자 선 단절 처리)    |
+----------------------------------------------------------------------------------------+
| +----------------------------------------+ +-----------------------------------------+ |
| | 오늘의 경영 이상 경보 (Alert Priority) | | 식재료 재고 & 폐기 패널 (Inventory)     | |
| | (CRITICAL > HIGH > MEDIUM 정렬)        | +-----------------------------------------+ |
| | - 규칙명, 관측치 vs 관리기준           | | 고객 반응 & 서비스 품질 패널 (Customer) | |
| | - [Evidence 확인] -> Drawer 호출        | |                                         | |
| +----------------------------------------+ +-----------------------------------------+ |
+----------------------------------------------------------------------------------------+
| [전체 기간 경영 요약 (Summary)]                                                        |
| - 기간 총매출, 평균 인건비율, 평균 원가율, 총 공헌이익, KPI Coverage (91/92일 표시)    |
+----------------------------------------------------------------------------------------+
```
""")

write_file('docs/design-docs/frontend-architecture-v1.0.md', """# docs/design-docs/frontend-architecture-v1.0.md — Frontend Architecture

> **DAMGA-OPS CEO Cockpit 프론트엔드 아키텍처 및 상태 관리 설계서 (Version 1.0)**

---

## 1. 아키텍처 다이어그램

```
+----------------------------------------------------------+
|              React 18 + TypeScript (SPA)                 |
|                                                          |
|  +-----------------+       +--------------------------+  |
|  | CeoCockpitPage  | <---> | useDailyDashboard Hook   |  |
|  +--------+--------+       +------------+-------------+  |
|           |                             |                |
|           v                             v                |
|  +-----------------+       +--------------------------+  |
|  | UI Presentation |       | REST API Client Layer    |  |
|  | Components      |       | (/api/v1/dashboard/*)    |  |
|  +-----------------+       +------------+-------------+  |
+-----------------------------------------+----------------+
                                          | HTTP / JSON
                                          v
+----------------------------------------------------------+
|              FastAPI Backend Application                 |
|         (Truth: Facts Engine, Rule Engine, Storage)      |
+----------------------------------------------------------+
```

---

## 2. 컴포넌트 계층 구조 및 책임

1. **`pages/CeoCockpitPage.tsx`**:
   - 일자 선택 상태(`selectedDate`), 증적 드로어 활성 상태(`activeEvidenceId`) 관리.
   - 데이터 로딩, 에러 핸들링 오케스트레이션.
2. **`components/layout/`**:
   - `Header.tsx`: 글로벌 타이틀 및 네비게이션.
   - `DateSelector.tsx`: 이전/다음/달력 일자 탐색.
   - `SyntheticBadge.tsx`: 합성 데이터 상시 고정 배지.
   - `DataIncompleteBanner.tsx`: 데이터 누락 시 독립 지표 보존 안내 배너.
3. **`components/kpi/`**:
   - `KpiGrid.tsx`, `KpiHeroCard.tsx`: 4대 Hero 지표 및 KPI 상태별 서식 렌더링.
4. **`components/alerts/`**:
   - `AlertPriorityPanel.tsx`, `AlertCard.tsx`: 심각도별 정렬 및 Evidence 연결.
5. **`components/charts/`**:
   - `TrendCharts.tsx`: Recharts 기반 7일 추세선 (Null 단절 지원).
6. **`components/evidence/`**:
   - `EvidenceDrawer.tsx`: `/verify` 엔드포인트를 통한 SHA-256 실시간 검증 표시.
7. **`utils/formatters.ts` & `utils/status.ts`**:
   - Missing != Zero 시맨틱스를 100% 보장하는 순수 포맷터.
""")

