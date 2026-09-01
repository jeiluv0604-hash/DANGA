import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { ManagementSystemSection } from '../../src/components/management/ManagementSystemSection';
import * as managementApi from '../../src/api/management';
import { ManagementPrototype } from '../../src/types/management';


const prototype: ManagementPrototype = {
  brand_name: '담가화로구이',
  prototype_version: '6.0.0-prototype',
  dataset_type: 'SYNTHETIC',
  data_disclosure: 'SYNTHETIC · 실제 담가화로구이 매장 데이터 아님',
  policy_status: 'UNVERIFIED POLICY',
  purpose: '실제 사용 전 경영체계 검증용 프로토타입',
  daily_kpis: [],
  daily_kpi_snapshot: [{order: 1, name: '일매출', value: 344000000, unit: 'KRW', status: 'AVAILABLE'}],
  finance: {
    monthly_pnl: [{
      period: '2026-08', sales: 344000000, food_cost: 115584000, labor_cost: 96320000,
      rent: 38000000, utilities: 21000000, card_platform_fees: 17200000,
      other_expenses: 15480000, operating_profit: 40416000, operating_margin: 0.117488,
      food_cost_ratio: 0.336, labor_ratio: 0.28, data_status: 'OK',
    }],
    cash_flow: [{period: '2026-08', beginning_cash: 200000000, cash_inflows: 330000000, cash_outflows: 290000000, ending_cash: 240000000}],
    budget_actual: [{period: '2026-08', metrics: {sales: {actual: 344000000, budget: 360000000, variance: -16000000, variance_ratio: -0.0444}}}],
    allocation_policy_status: 'UNVERIFIED POLICY',
  },
  menu_engineering: {
    menus: [{menu_id: 'M-001', menu_name: '담가 갈비', net_price: 30000, sales_quantity: 2650, standard_cost: 12390, unit_contribution: 17610, contribution_margin: 0.587, abcd_class: 'A', data_status: 'OK'}],
    policy: {status: 'UNVERIFIED POLICY', sales_threshold_method: 'SYNTHETIC_MEDIAN', contribution_threshold_method: 'SYNTHETIC_MEDIAN'},
  },
  organization: {
    roles: [{role_id: 'OWNER', name: '오너(대표)', reports_to: null}, {role_id: 'GENERAL_MANAGER', name: '총괄점장', reports_to: 'OWNER'}],
    manager_scorecard: [{metric: '매출', weight: 20}, {metric: '영업이익', weight: 80}],
    scorecard_policy_status: 'UNVERIFIED POLICY', scorecard_total_weight: 100, automated_employment_decisions: false,
    raci_assignments: [], approval_policies: [],
  },
  standards: {
    sops: [{sop_id: 'SOP-INV-003', title: '재고 차이 확인 절차', owner_role: 'PURCHASING_MANAGER', linked_rule_ids: ['R-INV-01'], checklist: ['재고 재계량']}],
    actions: [{action_id: 'ACT-SYN-001', title: '재고 차이 재계량 및 기록 대사', source_rule_id: 'R-INV-01', sop_id: 'SOP-INV-003', owner_role: 'PURCHASING_MANAGER', priority: 'CRITICAL', status: 'IN_PROGRESS', due_date: '2026-09-02', evidence_id: 'EV-ACT-SYN-001'}],
    automatic_execution_enabled: false,
  },
  monthly_review: {
    period: '2026-08', status: 'REVIEW_REQUIRED', sales: 344000000, operating_profit: 40416000,
    operating_margin: 0.117488, food_cost_ratio: 0.336, labor_ratio: 0.28,
    menu_abcd_counts: {A: 1}, action_counts: {IN_PROGRESS: 1}, top_actions: ['재고 차이 재계량 및 기록 대사'], human_approval_required: true,
    management_brief: {status: 'REVIEW_REQUIRED', provider: 'deterministic-prototype', executive_summary: 'Synthetic 경영검토입니다.', findings: [], recommended_actions: [], human_approval_required: true},
  },
};


describe('Management Sales Tabs', () => {
  it('renders monthly sales and operating profit without SOP or monthly meeting', async () => {
    vi.spyOn(managementApi, 'getManagementPrototype').mockResolvedValue(prototype);
    render(<ManagementSystemSection view="monthly" />);
    expect(await screen.findByText('월 단위 매출 정보')).toBeInTheDocument();
    expect(screen.getAllByText('영업이익').length).toBeGreaterThan(0);
    expect(screen.getAllByText(/UNVERIFIED POLICY/).length).toBeGreaterThan(0);
    expect(screen.queryByText(/SOP/)).not.toBeInTheDocument();
    expect(screen.queryByText(/월간 경영회의/)).not.toBeInTheDocument();
  });

  it('renders yearly sales aggregation', async () => {
    vi.spyOn(managementApi, 'getManagementPrototype').mockResolvedValue(prototype);
    render(<ManagementSystemSection view="yearly" />);
    expect(await screen.findByText('2026년 매출 정보')).toBeInTheDocument();
    expect(screen.getByText('누적 매출')).toBeInTheDocument();
    expect(screen.getByText('연환산 예상 매출')).toBeInTheDocument();
  });
});
