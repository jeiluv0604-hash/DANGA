# DAMGA-OPS (담가화로 업무자동화 대시보드)

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
- Node.js 20+
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

### 4. 재현 가능한 전체 설정·검증

```powershell
.\bootstrap.ps1
```

### 5. 경영체계 프로토타입

- 브랜드: `담가화로구이`
- 데이터: `SYNTHETIC · 실제 담가화로구이 매장 데이터 아님`
- 정책: 비용 배부·메뉴 ABCD·관리자 KPI 가중치는 `UNVERIFIED POLICY`
- 대시보드: 오늘 매출 최상단, 7일 추세·월 매출·연 매출·경영이상·재고/폐기·고객반응 6개 탭, 하단 AI 의사결정 요약
- 표시 용어: 기존 `Contribution` 내부 필드는 화면에서 `영업이익`으로 표시
- SOP와 월간 경영회의 데이터는 API 감사 호환성을 위해 보존하되 현재 대시보드에서는 표시하지 않음

---

## 📂 프로젝트 구조
- **[AGENTS.md](AGENTS.md)**: AI 에이전트 작업 헌장 및 내비게이션 맵
- **[ARCHITECTURE.md](ARCHITECTURE.md)**: 책임 분리 및 레이어드 아키텍처
- **[docs/](docs/)**:
  - `product/`: [마스터 명세서](docs/product/master-specification-v1.0.md), [KPI 정의서](docs/product/kpi-definition.md)
  - `quality/`: [골든 원칙](docs/quality/golden-principles.md), [테스트 전략](docs/quality/golden-test-strategy.md)
  - `exec-plans/`: [Phase 6 완료 계획](docs/exec-plans/completed/phase-6-management-system-prototype.md)
- **[domains/](domains/)**: 매출, 인건비, 식재료비, 재고, 고객 도메인별 계산 및 룰 엔진
- **[tests/](tests/)**: 단위(Unit), 통합(Integration), 골든(Golden), E2E 테스트
- **[evidence/](evidence/)**: 테스트 실행 결과 및 감사 증적

---

## 🎯 7대 골든 이상 시나리오 (Ground Truth)
1. **GA-001**: 금요일 비피크 과잉 인력 투입 (`Labor_Ratio >= 33%`)
2. **GA-002**: 육류 실재고 부족 (`Variance_kg <= -5kg`)
3. **GA-003**: 한우 원가 압박 7일 지속 (`Food_Cost_Ratio >= 39%`)
4. **GA-004**: 육류 폐기량 급증 (`Waste / Sold >= 5%`)
5. **GA-005**: 매출 상승 대비 영업이익 역행 악화
6. **GA-006**: 고객 클레임 급증 및 평점 하락
7. **GA-007**: 필수 데이터 누락 차단 (`DATA_INCOMPLETE`)
