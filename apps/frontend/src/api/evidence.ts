import { apiFetch } from './client';
import { EvidenceDetail, EvidenceVerifyResult } from '../types/evidence';

export async function fetchEvidenceDetail(evidenceId: string): Promise<EvidenceDetail> {
  return apiFetch<EvidenceDetail>(`/evidence/${evidenceId}`);
}

export async function verifyEvidence(evidenceId: string): Promise<EvidenceVerifyResult> {
  return apiFetch<EvidenceVerifyResult>(`/evidence/${evidenceId}/verify`);
}
