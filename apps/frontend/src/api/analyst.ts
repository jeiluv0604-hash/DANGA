import { apiFetch } from './client';
import { AnalystBriefResponse, DecisionAuditLogItem } from '../types/analyst';

export async function fetchDailyAnalystBrief(date: string): Promise<AnalystBriefResponse> {
  return apiFetch<AnalystBriefResponse>(`/analyst/daily/${date}`);
}

export async function approveAnalystBrief(
  briefId: string,
  reviewerRole: 'CEO' | 'GENERAL_MANAGER' = 'CEO',
  comment?: string
): Promise<AnalystBriefResponse> {
  return apiFetch<AnalystBriefResponse>(`/analyst/briefs/${briefId}/approve`, {
    method: 'POST',
    body: JSON.stringify({ reviewer_role: reviewerRole, comment }),
  });
}

export async function rejectAnalystBrief(
  briefId: string,
  reviewerRole: 'CEO' | 'GENERAL_MANAGER' = 'CEO',
  comment?: string
): Promise<AnalystBriefResponse> {
  return apiFetch<AnalystBriefResponse>(`/analyst/briefs/${briefId}/reject`, {
    method: 'POST',
    body: JSON.stringify({ reviewer_role: reviewerRole, comment }),
  });
}

export async function fetchBriefAuditTrail(briefId: string): Promise<DecisionAuditLogItem[]> {
  return apiFetch<DecisionAuditLogItem[]>(`/analyst/briefs/${briefId}/audit`);
}
