export type DataStatus = 'OK' | 'DATA_INCOMPLETE' | 'SYNTHETIC';
export type KpiStatus = 'AVAILABLE' | 'MISSING_INPUT' | 'BLOCKED_DEPENDENCY' | 'NOT_PROVIDED' | 'INVALID_FORMAT';

export interface DailyKpis {
  sales: number | null;
  guests: number | null;
  avg_check: number | null;
  labor_cost: number | null;
  labor_ratio: number | null;
  food_cost: number | null;
  food_cost_ratio: number | null;
  contribution: number | null;
  contribution_ratio: number | null;
  inventory_variance_kg: number | null;
  waste_ratio: number | null;
  rating: number | null;
  complaints: number | null;
  service_kg?: number | null;
  review_count?: number | null;
}

export interface KpiStatusMap {
  [key: string]: KpiStatus;
}

export interface DailyAlert {
  alert_id: string;
  business_date: string;
  rule_id: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM';
  status: string;
  actual_value: string;
  threshold_value: string;
  comparison: string;
  dataset_type: string;
  ingestion_id: string;
  evidence_id?: string;
}

export interface DailyDashboardResponse {
  date: string;
  dataset_type: string;
  data_status: DataStatus;
  blocked: boolean;
  ai_eligible: boolean;
  kpis: DailyKpis;
  kpi_status: KpiStatusMap;
  alerts: DailyAlert[];
  evidence_ids: string[];
}

export interface CoverageMetric {
  available_days: number;
  total_days: number;
}

export interface DashboardSummaryResponse {
  start_date: string;
  end_date: string;
  dataset_type: string;
  total_days: number;
  data_complete_days: number;
  data_incomplete_days: number;
  total_sales: number;
  average_daily_sales: number;
  average_labor_ratio: number;
  average_food_cost_ratio: number;
  total_contribution: number;
  average_contribution_ratio: number;
  critical_alert_count: number;
  high_alert_count: number;
  medium_alert_count: number;
  coverage: {
    sales: CoverageMetric;
    labor_ratio: CoverageMetric;
    food_cost_ratio: CoverageMetric;
    contribution_ratio: CoverageMetric;
  };
}
