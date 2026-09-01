import { apiFetch } from './client';
import { DailyFactItem } from '../types/facts';

export async function fetchDailyFacts(startDate?: string, endDate?: string): Promise<DailyFactItem[]> {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  const qs = params.toString();
  return apiFetch<DailyFactItem[]>(`/facts` + (qs ? `?${qs}` : ''));
}
