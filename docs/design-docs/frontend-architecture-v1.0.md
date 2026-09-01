# docs/design-docs/frontend-architecture-v1.0.md — Frontend Architecture

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
