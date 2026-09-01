export interface EvidenceDetail {
  evidence_id: string;
  evidence_type: string;
  business_date?: string;
  rule_id?: string;
  file_path: string;
  file_sha256: string;
  dataset_sha256: string;
  created_at: string;
}

export interface EvidenceVerifyResult {
  evidence_id: string;
  exists: boolean;
  stored_sha256?: string;
  actual_sha256?: string;
  dataset_sha256?: string;
  integrity: 'VALID' | 'INVALID' | 'MISSING_FILE';
}
