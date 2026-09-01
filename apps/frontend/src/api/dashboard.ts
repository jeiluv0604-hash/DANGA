import { apiFetch } from './client';
import { DailyDashboardResponse, DashboardSummaryResponse } from '../types/dashboard';

export async function fetchDailyDashboard(date: string): Promise<DailyDashboardResponse> {
  return apiFetch<DailyDashboardResponse>(`/dashboard/daily/${date}`);
}

export async function fetchDashboardSummary(startDate?: string, endDate?: string): Promise<DashboardSummaryResponse> {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  const qs = params.toString();
  return apiFetch<DashboardSummaryResponse>(`/dashboard/summary` + (qs ? `?${qs}` : ''));
}
