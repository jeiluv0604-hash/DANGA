import React from 'react';
import { DailyAlert } from '../../types/dashboard';
import { getRuleMeta } from '../../utils/ruleDisplay';
import { getSeverityStyle } from '../../utils/status';

interface AlertCardProps {
  alert: DailyAlert;
  onOpenEvidence: (evidenceId: string) => void;
}

export const AlertCard: React.FC<AlertCardProps> = ({ alert, onOpenEvidence }) => {
  const meta = getRuleMeta(alert.rule_id);
  const style = getSeverityStyle(alert.severity);

  return (
    <div
      data-testid="alert-card"
      style={{
        backgroundColor: style.badgeBg,
        border: `1px solid ${style.border}`,
        borderRadius: '8px',
        padding: '14px 16px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '12px',
        marginBottom: '10px',
      }}
    >
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
          <span
            style={{
              backgroundColor: style.indicator,
              color: '#000',
              fontSize: '10px',
              fontWeight: '900',
              padding: '2px 6px',
              borderRadius: '4px',
            }}
          >
            {style.label}
          </span>
          <span style={{ fontSize: '14px', fontWeight: 'bold', color: '#f8fafc' }}>
            {meta.name}
          </span>
          <span style={{ fontSize: '11px', color: '#64748b', fontFamily: 'monospace' }}>
            {alert.rule_id}
          </span>
        </div>

        <p style={{ fontSize: '12px', color: '#cbd5e1', margin: '0 0 4px 0' }}>
          {meta.description}
        </p>

        <div style={{ fontSize: '12px', color: style.badgeText, display: 'flex', gap: '12px' }}>
          <span><strong>관측치:</strong> {alert.actual_value}</span>
          <span><strong>관리기준:</strong> {alert.threshold_value}</span>
        </div>
      </div>

      {alert.evidence_id && (
        <button
          onClick={() => onOpenEvidence(alert.evidence_id!)}
          aria-label="Evidence 확인"
          style={{
            padding: '6px 12px',
            backgroundColor: '#1e293b',
            border: '1px solid #3b82f6',
            color: '#38bdf8',
            borderRadius: '6px',
            fontSize: '12px',
            fontWeight: '600',
            whiteSpace: 'nowrap',
          }}
        >
          Evidence 확인
        </button>
      )}
    </div>
  );
};
