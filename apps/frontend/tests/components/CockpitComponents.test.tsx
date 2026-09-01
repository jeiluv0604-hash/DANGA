import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SyntheticBadge } from '../../src/components/layout/SyntheticBadge';
import { DataIncompleteBanner } from '../../src/components/layout/DataIncompleteBanner';
import { KpiGrid } from '../../src/components/kpi/KpiGrid';
import { AlertPriorityPanel } from '../../src/components/alerts/AlertPriorityPanel';
import { CustomerPanel } from '../../src/components/panels/CustomerPanel';
import { SummarySection } from '../../src/components/summary/SummarySection';
import { ErrorState } from '../../src/components/common/ErrorState';
import { LoadingSkeleton } from '../../src/components/common/LoadingSkeleton';
import { DailyKpis, KpiStatusMap, DailyAlert, DashboardSummaryResponse } from '../../src/types/dashboard';

describe('CEO Cockpit Component Tests (UI-001 ~ UI-015)', () => {
  const normalKpis: DailyKpis = {
    sales: 13092000,
    guests: 286,
    avg_check: 45776,
    labor_cost: 4648000,
    labor_ratio: 0.355,
    food_cost: 4451280,
    food_cost_ratio: 0.34,
    contribution: 3992720,
    contribution_ratio: 0.305,
    inventory_variance_kg: -1.2,
    waste_ratio: 0.021,
    rating: 4.65,
    complaints: 1,
    service_kg: 1.4,
    review_count: 12,
  };

  const normalStatus: KpiStatusMap = {
    sales: 'AVAILABLE',
    guests: 'AVAILABLE',
    avg_check: 'AVAILABLE',
    labor_cost: 'AVAILABLE',
    labor_ratio: 'AVAILABLE',
    food_cost: 'AVAILABLE',
    food_cost_ratio: 'AVAILABLE',
    contribution: 'AVAILABLE',
    contribution_ratio: 'AVAILABLE',
    inventory_variance: 'AVAILABLE',
    waste_ratio: 'AVAILABLE',
    rating: 'AVAILABLE',
    complaints: 'AVAILABLE',
    service_kg: 'AVAILABLE',
    review_count: 'AVAILABLE',
  };

  const highLaborAlert: DailyAlert = {
    alert_id: 'ALT-01',
    business_date: '2026-06-12',
    rule_id: 'R-LAB-01',
    severity: 'HIGH',
    status: 'ALERT',
    actual_value: '35.5%',
    threshold_value: '33.0%',
    comparison: '>=',
    dataset_type: 'SYNTHETIC',
    ingestion_id: 'ING-01',
    evidence_id: 'EV-01',
  };

  it('UI-001: Renders normal day KPI values accurately', () => {
    render(<KpiGrid kpis={normalKpis} kpiStatus={normalStatus} alerts={[]} />);
    expect(screen.getByText('13,092,000원')).toBeInTheDocument();
    expect(screen.getByText('35.5%')).toBeInTheDocument();
    expect(screen.getByText('34.0%')).toBeInTheDocument();
    expect(screen.getByText('3,992,720원')).toBeInTheDocument();
  });

  it('UI-002: Displays Labor HIGH Alert warning badge on KPI card', () => {
    render(<KpiGrid kpis={normalKpis} kpiStatus={normalStatus} alerts={[highLaborAlert]} />);
    expect(screen.getByText('인건비 초과')).toBeInTheDocument();
  });

  it('UI-003: Displays DATA_INCOMPLETE Warning Banner', () => {
    render(<DataIncompleteBanner date="2026-08-21" />);
    expect(screen.getByTestId('data-incomplete-banner')).toBeInTheDocument();
    expect(screen.getByText(/일부 필수 데이터가 누락되었습니다/)).toBeInTheDocument();
  });

  it('UI-004: Displays "데이터 없음" when Food Cost is null (MISSING_INPUT)', () => {
    const incompleteKpis = { ...normalKpis, food_cost: null, food_cost_ratio: null };
    const incompleteStatus: KpiStatusMap = {
      ...normalStatus,
      food_cost: 'MISSING_INPUT',
      food_cost_ratio: 'BLOCKED_DEPENDENCY',
    };
    render(<KpiGrid kpis={incompleteKpis} kpiStatus={incompleteStatus} alerts={[]} />);
    expect(screen.getByText(/식재료비 데이터 없음/)).toBeInTheDocument();
  });

  it('UI-005: Displays "계산 불가" when Contribution is null (BLOCKED_DEPENDENCY)', () => {
    const blockedKpis = { ...normalKpis, contribution: null, contribution_ratio: null };
    const blockedStatus = { ...normalStatus, contribution: 'BLOCKED_DEPENDENCY' as any, contribution_ratio: 'BLOCKED_DEPENDENCY' as any };
    render(<KpiGrid kpis={blockedKpis} kpiStatus={blockedStatus} alerts={[]} />);
    expect(screen.getByText('계산 불가')).toBeInTheDocument();
  });

  it('UI-006: Distinguishes Complaints 0 as "0건"', () => {
    const zeroKpis = { ...normalKpis, complaints: 0 };
    render(<CustomerPanel kpis={zeroKpis} kpiStatus={normalStatus} alerts={[]} />);
    expect(screen.getByText('0건')).toBeInTheDocument();
  });

  it('UI-007: Distinguishes Complaints null as "미입력"', () => {
    const nullKpis = { ...normalKpis, complaints: null };
    const notProvidedStatus = { ...normalStatus, complaints: 'NOT_PROVIDED' as any };
    render(<CustomerPanel kpis={nullKpis} kpiStatus={notProvidedStatus} alerts={[]} />);
    expect(screen.getByText('미입력')).toBeInTheDocument();
  });

  it('UI-010: Sorts Alerts by Severity (CRITICAL > HIGH > MEDIUM)', () => {
    const mixedAlerts: DailyAlert[] = [
      { ...highLaborAlert, alert_id: 'A1', severity: 'MEDIUM', rule_id: 'R-CUS-01' },
      { ...highLaborAlert, alert_id: 'A2', severity: 'CRITICAL', rule_id: 'R-DQ-01' },
      { ...highLaborAlert, alert_id: 'A3', severity: 'HIGH', rule_id: 'R-LAB-01' },
    ];
    render(<AlertPriorityPanel alerts={mixedAlerts} onOpenEvidence={() => {}} />);
    const cards = screen.getAllByTestId('alert-card');
    expect(cards[0]).toHaveTextContent('CRITICAL');
    expect(cards[1]).toHaveTextContent('HIGH');
    expect(cards[2]).toHaveTextContent('MEDIUM');
  });

  it('UI-011: Synthetic Badge is always displayed and non-closable', () => {
    render(<SyntheticBadge />);
    expect(screen.getByTestId('synthetic-badge')).toBeInTheDocument();
    expect(screen.getByText('SYNTHETIC · 실제 매장 데이터 아님')).toBeInTheDocument();
  });

  it('UI-012: Renders Error state with Retry button', () => {
    const onRetry = vi.fn();
    render(<ErrorState message="네트워크 오류" onRetry={onRetry} />);
    expect(screen.getByText('데이터를 불러오지 못했습니다')).toBeInTheDocument();
    expect(screen.getByText('다시 시도')).toBeInTheDocument();
  });

  it('UI-013: Renders Loading skeleton during data fetch', () => {
    const { container } = render(<LoadingSkeleton />);
    expect(container.querySelector('.animate-pulse-subtle')).toBeInTheDocument();
  });

  it('UI-014: Renders Empty alert state when 0 alerts', () => {
    render(<AlertPriorityPanel alerts={[]} onOpenEvidence={() => {}} />);
    expect(screen.getByText('오늘 등록된 이상 경보가 없습니다. 모든 경영 지표가 정상 범위입니다.')).toBeInTheDocument();
  });

  it('UI-015: Shows warning badge when Summary Coverage < 100%', () => {
    const summaryWithGap: DashboardSummaryResponse = {
      start_date: '2026-06-01',
      end_date: '2026-08-31',
      dataset_type: 'SYNTHETIC',
      total_days: 92,
      data_complete_days: 91,
      data_incomplete_days: 1,
      total_sales: 1058152000,
      average_daily_sales: 11501652,
      average_labor_ratio: 0.28,
      average_food_cost_ratio: 0.34,
      total_contribution: 390000000,
      average_contribution_ratio: 0.36,
      critical_alert_count: 2,
      high_alert_count: 6,
      medium_alert_count: 3,
      coverage: {
        sales: { available_days: 92, total_days: 92 },
        labor_ratio: { available_days: 92, total_days: 92 },
        food_cost_ratio: { available_days: 91, total_days: 92 },
        contribution_ratio: { available_days: 91, total_days: 92 },
      },
    };
    render(<SummarySection summary={summaryWithGap} />);
    expect(screen.getByTestId('coverage-warning')).toBeInTheDocument();
    expect(screen.getByText('일부 누락')).toBeInTheDocument();
  });
});
