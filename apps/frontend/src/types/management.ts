export interface MonthlyPnl {
  period: string;
  sales: number;
  food_cost: number;
  labor_cost: number;
  rent: number;
  utilities: number;
  card_platform_fees: number;
  other_expenses: number;
  operating_profit: number;
  operating_margin: number;
  food_cost_ratio: number;
  labor_ratio: number;
  data_status: string;
}

export interface CashFlowMonth {
  period: string;
  beginning_cash: number;
  cash_inflows: number;
  cash_outflows: number;
  ending_cash: number;
}

export interface MenuEngineeringItem {
  menu_id: string;
  menu_name: string;
  net_price: number;
  sales_quantity: number;
  standard_cost: number;
  unit_contribution: number;
  contribution_margin: number;
  abcd_class: 'A' | 'B' | 'C' | 'D';
  data_status: string;
}

export interface ManagementAction {
  action_id: string;
  title: string;
  source_rule_id: string;
  sop_id: string;
  owner_role: string;
  priority: string;
  status: string;
  due_date: string;
  evidence_id: string;
  dataset_type?: string;
  policy_status?: string;
}

export interface ManagementPrototype {
  brand_name: string;
  prototype_version: string;
  dataset_type: string;
  data_disclosure: string;
  policy_status: string;
  purpose: string;
  daily_kpis: Array<{ order: string; name: string; status: string }>;
  daily_kpi_snapshot: Array<{ order: number; name: string; value: number | Record<string, number>; unit: string; status: string }>;
  finance: {
    monthly_pnl: MonthlyPnl[];
    cash_flow: CashFlowMonth[];
    budget_actual: Array<{
      period: string;
      metrics: Record<string, { actual: number; budget: number; variance: number; variance_ratio: number }>;
    }>;
    allocation_policy_status: string;
    annualized_sales_baseline?: number;
  };
  menu_engineering: {
    menus: MenuEngineeringItem[];
    policy: {
      status: string;
      sales_threshold_method: string;
      contribution_threshold_method: string;
    };
  };
  organization: {
    roles: Array<{ role_id: string; name: string; reports_to: string | null }>;
    manager_scorecard: Array<{ metric: string; weight: number }>;
    scorecard_policy_status: string;
    scorecard_total_weight: number;
    automated_employment_decisions: boolean;
    raci_assignments?: Array<{ process: string; responsible: string; accountable: string; consulted: string[]; informed: string[] }>;
    approval_policies?: Array<{ policy_id: string; action_type: string; rule: string; status: string; automatic_execution: boolean; self_approval_allowed: boolean }>;
  };
  standards: {
    sops: Array<{
      sop_id: string;
      title: string;
      owner_role: string;
      linked_rule_ids: string[];
      checklist: string[];
    }>;
    actions: ManagementAction[];
    action_state_machine?: string[];
    automatic_execution_enabled: boolean;
  };
  monthly_review: {
    period: string;
    status: string;
    sales: number;
    operating_profit: number;
    operating_margin: number;
    food_cost_ratio: number;
    labor_ratio: number;
    menu_abcd_counts: Record<string, number>;
    action_counts: Record<string, number>;
    top_actions: string[];
    human_approval_required: boolean;
    management_brief?: {
      status: string;
      provider: string;
      executive_summary: string;
      findings: string[];
      recommended_actions: string[];
      human_approval_required: boolean;
    };
  };
}
