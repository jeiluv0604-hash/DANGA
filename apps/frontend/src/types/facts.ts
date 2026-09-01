export interface DailyFactItem {
  business_date: string;
  sales: number | null;
  guests: number | null;
  avg_check: number | null;
  labor_cost: number | null;
  labor_ratio: number | null;
  food_cost: number | null;
  food_cost_ratio: number | null;
  incoming_kg: number | null;
  sold_kg: number | null;
  service_kg: number | null;
  waste_kg: number | null;
  waste_ratio: number | null;
  theory_end_kg: number | null;
  actual_end_kg: number | null;
  variance_kg: number | null;
  rating: number | null;
  review_count: number | null;
  complaints: number | null;
  contribution: number | null;
  contribution_ratio: number | null;
  data_status: string;
  dataset_type: string;
  ingestion_id: string;
}
