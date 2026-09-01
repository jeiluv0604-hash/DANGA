import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { AnalystBriefingSection } from '../../src/components/analyst/AnalystBriefingSection';
import * as useAnalystBriefModule from '../../src/hooks/useAnalystBrief';
import { AnalystBriefResponse } from '../../src/types/analyst';

describe('Analyst Briefing Section Tests (UI-AI-001 ~ UI-AI-006)', () => {
  const mockBrief: AnalystBriefResponse = {
    brief_id: 'BRF-2026-06-12-001',
    business_date: '2026-06-12',
    dataset_type: 'SYNTHETIC',
    status: 'REVIEW_REQUIRED',
    provider: 'mock',
    model: 'mock-analyst-gpt4o-mini-simulator',
    prompt_version: 'v1.0',
    facts_version: 'v1.0',
    rule_version: 'v1.0',
    executive_summary: '인건비율이 35.5%로 관리 기준(33.0%)을 초과했습니다.',
    findings: [
      {
        finding: '인건비율이 35.5%로 관리 기준(33.0%)을 초과했습니다.',
        severity: 'HIGH',
        rule_id: 'R-LAB-01',
        evidence_ids: ['EV-ALT-2026-06-12-R-LAB-01'],
      },
    ],
    possible_causes: [
      {
        hypothesis: '매출 변동 대비 피크타임 인력 배치 과다 가능성',
        confidence: 'MEDIUM',
        basis: '인건비율 35.5% 관측',
        evidence_ids: ['EV-ALT-2026-06-12-R-LAB-01'],
      },
    ],
    recommended_actions: [
      {
        action: '파트타임 근무 스케줄 배치를 점검하십시오.',
        owner_role: 'FLOOR_MANAGER',
        priority: 'HIGH',
        approval_required: true,
        evidence_ids: ['EV-ALT-2026-06-12-R-LAB-01'],
      },
    ],
    unknowns: ['현장 상세 정성적 원인'],
    evidence_ids: ['EV-ALT-2026-06-12-R-LAB-01'],
    rejection_reasons: [],
    created_at: '2026-06-12T23:59:00Z',
    approval_disclaimer: 'DEVELOPMENT HUMAN APPROVAL SIMULATION',
  };

  it('UI-AI-001: Renders AI Briefing executive summary & model badge', () => {
    vi.spyOn(useAnalystBriefModule, 'useAnalystBrief').mockReturnValue({
      brief: mockBrief,
      auditLogs: [],
      loading: false,
      actionLoading: false,
      error: null,
      refresh: vi.fn(),
      handleApprove: vi.fn(),
      handleReject: vi.fn(),
    });

    render(<AnalystBriefingSection date="2026-06-12" onOpenEvidence={() => {}} />);
    expect(screen.getByText('AI 경영분석 및 의사결정 지원')).toBeInTheDocument();
    expect(screen.getByText('오늘의 결론')).toBeInTheDocument();
    expect(screen.getAllByText(/인건비율이 35.5%로 관리 기준/)[0]).toBeInTheDocument();
  });

  it('UI-AI-002: Renders REVIEW REQUIRED badge and Approve/Reject buttons', () => {
    const handleApprove = vi.fn();
    const handleReject = vi.fn();

    vi.spyOn(useAnalystBriefModule, 'useAnalystBrief').mockReturnValue({
      brief: mockBrief,
      auditLogs: [],
      loading: false,
      actionLoading: false,
      error: null,
      refresh: vi.fn(),
      handleApprove,
      handleReject,
    });

    render(<AnalystBriefingSection date="2026-06-12" onOpenEvidence={() => {}} />);
    expect(screen.getByText(/검토 대기/)).toBeInTheDocument();
    expect(screen.getByText('승인')).toBeInTheDocument();
    expect(screen.getByText('반려')).toBeInTheDocument();

    fireEvent.click(screen.getByText('승인'));
    expect(handleApprove).toHaveBeenCalled();
  });

  it('UI-AI-003: Renders BLOCKED status badge when DATA_INCOMPLETE', () => {
    const blockedBrief: AnalystBriefResponse = {
      ...mockBrief,
      status: 'BLOCKED',
      executive_summary: '필수 입력 데이터(Food_Cost)가 누락되어 자동 경영 분석이 차단되었습니다.',
    };

    vi.spyOn(useAnalystBriefModule, 'useAnalystBrief').mockReturnValue({
      brief: blockedBrief,
      auditLogs: [],
      loading: false,
      actionLoading: false,
      error: null,
      refresh: vi.fn(),
      handleApprove: vi.fn(),
      handleReject: vi.fn(),
    });

    render(<AnalystBriefingSection date="2026-08-21" onOpenEvidence={() => {}} />);
    expect(screen.getByText(/분석 차단/)).toBeInTheDocument();
    expect(screen.queryByText('승인')).not.toBeInTheDocument();
  });

  it('UI-AI-004: Displays synthetic dataset disclosure warning', () => {
    vi.spyOn(useAnalystBriefModule, 'useAnalystBrief').mockReturnValue({
      brief: mockBrief,
      auditLogs: [],
      loading: false,
      actionLoading: false,
      error: null,
      refresh: vi.fn(),
      handleApprove: vi.fn(),
      handleReject: vi.fn(),
    });

    render(<AnalystBriefingSection date="2026-06-12" onOpenEvidence={() => {}} />);
    expect(screen.getByText(/SYNTHETIC · 실제 매장 데이터가 아닌 가상 데이터 분석/)).toBeInTheDocument();
  });

  it('UI-AI-005: Clicking Evidence link calls onOpenEvidence', () => {
    const onOpenEvidence = vi.fn();
    vi.spyOn(useAnalystBriefModule, 'useAnalystBrief').mockReturnValue({
      brief: mockBrief,
      auditLogs: [],
      loading: false,
      actionLoading: false,
      error: null,
      refresh: vi.fn(),
      handleApprove: vi.fn(),
      handleReject: vi.fn(),
    });

    render(<AnalystBriefingSection date="2026-06-12" onOpenEvidence={onOpenEvidence} />);
    const evBtn = screen.getAllByText(/인건비율이 35.5%로 관리 기준/)[1];
    fireEvent.click(evBtn);
    expect(onOpenEvidence).toHaveBeenCalledWith('EV-ALT-2026-06-12-R-LAB-01');
  });
});

