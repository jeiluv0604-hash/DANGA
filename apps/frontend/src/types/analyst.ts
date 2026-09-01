export interface FindingItem {
  finding: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
  rule_id?: string;
  evidence_ids: string[];
}

export interface PossibleCauseItem {
  hypothesis: string;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  basis: string;
  evidence_ids: string[];
}

export interface RecommendedActionItem {
  action: string;
  owner_role: 'CEO' | 'GENERAL_MANAGER' | 'FLOOR_MANAGER' | 'KITCHEN_LEAD';
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  approval_required: boolean;
  evidence_ids: string[];
}

export interface DecisionAuditLogItem {
  log_id: string;
  brief_id: string;
  decision_id?: string;
  previous_status: string;
  new_status: string;
  actor_role: string;
  action_type: string;
  timestamp: string;
  comment?: string;
}

export interface AnalystBriefResponse {
  brief_id: string;
  business_date: string;
  dataset_type: string;
  status: 'READY' | 'BLOCKED' | 'REVIEW_REQUIRED' | 'APPROVED' | 'REJECTED';
  provider: string;
  model: string;
  prompt_version: string;
  facts_version: string;
  rule_version: string;
  executive_summary: string;
  findings: FindingItem[];
  possible_causes: PossibleCauseItem[];
  recommended_actions: RecommendedActionItem[];
  unknowns: string[];
  evidence_ids: string[];
  rejection_reasons: string[];
  created_at: string;
  reviewed_at?: string;
  approval_disclaimer: string;
}
