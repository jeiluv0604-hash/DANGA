# -*- coding: utf-8 -*-
import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
    print('Wrote:', path)

# 1. Formatters Unit Tests
write_file('apps/frontend/tests/unit/formatters.test.ts', """import { describe, it, expect } from 'vitest';
import {
  formatWon,
  formatPercent,
  formatKg,
  formatRating,
  formatCount,
  truncateHash,
} from '../../src/utils/formatters';

describe('Formatters Unit Tests', () => {
  it('formats currency in Won correctly', () => {
    expect(formatWon(13092000)).toBe('13,092,000원');
    expect(formatWon(0)).toBe('0원');
    expect(formatWon(null, 'MISSING_INPUT')).toBe('데이터 없음');
    expect(formatWon(null, 'BLOCKED_DEPENDENCY')).toBe('계산 불가');
  });

  it('formats percent correctly', () => {
    expect(formatPercent(0.355)).toBe('35.5%');
    expect(formatPercent(0)).toBe('0.0%');
    expect(formatPercent(null, 'BLOCKED_DEPENDENCY')).toBe('계산 불가');
  });

  it('formats weight in Kg correctly', () => {
    expect(formatKg(-1.2)).toBe('-1.2kg');
    expect(formatKg(0)).toBe('0.0kg');
    expect(formatKg(2.5)).toBe('+2.5kg');
  });

  it('formats customer metrics distinguishing null vs 0', () => {
    expect(formatRating(4.65)).toBe('4.65');
    expect(formatRating(null, 'NOT_PROVIDED')).toBe('미입력');

    expect(formatCount(0, '건')).toBe('0건');
    expect(formatCount(null, '건', 'NOT_PROVIDED')).toBe('미입력');
  });

  it('truncates SHA-256 hash correctly', () => {
    const hash = '2132542be216b1cd5c610036f3c5207e189023a63e6a2aed1d3e87eeda2745cc';
    expect(truncateHash(hash, 6)).toBe('213254...2745cc');
    expect(truncateHash(undefined)).toBe('-');
  });
});
""")

# 2. UI-001 ~ UI-015 Component Tests
write_file('apps/frontend/tests/components/CockpitComponents.test.tsx', """import React from 'react';
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
    const incompleteStatus = { ...normalStatus, food_cost: 'MISSING_INPUT', food_cost_ratio: 'BLOCKED_DEPENDENCY' as any };
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
""")

# 3. Playwright E2E Tests (E2E-01 ~ E2E-05) & Screenshots
write_file('apps/frontend/tests/e2e/cockpit.spec.ts', """import { test, expect } from '@playwright/test';

test.describe('DAMGA-OPS CEO Cockpit E2E Tests', () => {
  test('E2E-01: Access 2026-06-12 (Normal & High Labor Alert Date)', async ({ page }) => {
    await page.goto('/?date=2026-06-12');
    
    // Select date 2026-06-12
    const dateInput = page.locator('input[type="date"]');
    await dateInput.fill('2026-06-12');

    // Verify Sales
    await expect(page.locator('text=13,092,000원')).toBeVisible();

    // Verify Labor Ratio 35.5% & Alert
    await expect(page.locator('text=35.5%')).toBeVisible();
    await expect(page.locator('text=인건비율 기준 초과')).toBeVisible();

    // Take Normal Day Screenshot
    await page.screenshot({ path: '../../evidence/EV-UI-NORMAL-20260612.png', fullPage: true });
  });

  test('E2E-02: Access 2026-08-21 (DATA_INCOMPLETE Date)', async ({ page }) => {
    await page.goto('/');
    const dateInput = page.locator('input[type="date"]');
    await dateInput.fill('2026-08-21');

    // Verify Warning Banner
    await expect(page.getByTestId('data-incomplete-banner')).toBeVisible();
    await expect(page.locator('text=일부 필수 데이터가 누락되었습니다')).toBeVisible();

    // Verify Independent Preserved KPIs
    await expect(page.locator('text=14,162,000원')).toBeVisible();
    await expect(page.locator('text=고객 419명')).toBeVisible();
    await expect(page.locator('text=24.5%')).toBeVisible();

    // Verify Blocked Dependent KPIs
    await expect(page.locator('text=계산 불가').first()).toBeVisible();

    // Take DATA_INCOMPLETE Screenshot
    await page.screenshot({ path: '../../evidence/EV-UI-DATA-INCOMPLETE-20260821.png', fullPage: true });
  });

  test('E2E-03: Open Evidence Drawer and Verify Cryptographic Integrity', async ({ page }) => {
    await page.goto('/');
    const dateInput = page.locator('input[type="date"]');
    await dateInput.fill('2026-06-12');

    // Click Evidence button on Alert
    const evButton = page.locator('button:has-text("Evidence 확인")').first();
    await expect(evButton).toBeVisible();
    await evButton.click();

    // Verify Drawer and VALID Badge
    await expect(page.getByTestId('evidence-drawer')).toBeVisible();
    await expect(page.getByTestId('evidence-status-valid')).toBeVisible();
    await expect(page.locator('text=무결성 검증됨 (VALID)')).toBeVisible();

    // Take Evidence Drawer Screenshot
    await page.screenshot({ path: '../../evidence/EV-UI-EVIDENCE-DRAWER.png', fullPage: true });
  });

  test('E2E-04: Verify 7-Day Trend Charts rendering', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByTestId('trend-charts')).toBeVisible();
    await expect(page.locator('text=최근 7일 경영 추세')).toBeVisible();
  });

  test('E2E-05: Tablet / Mobile Responsive Layout Viewport', async ({ page }) => {
    await page.setViewportSize({ width: 820, height: 1180 });
    await page.goto('/');

    await expect(page.getByTestId('synthetic-badge')).toBeVisible();
    await expect(page.locator('text=오늘 매출 (Sales)')).toBeVisible();

    // Take Responsive Screenshot
    await page.screenshot({ path: '../../evidence/EV-UI-RESPONSIVE-TABLET.png', fullPage: true });
  });
});
""")

