import React from 'react';

interface KpiHeroCardProps {
  title: string;
  primaryValue: string;
  secondaryText?: string;
  subValue?: string;
  isWarning?: boolean;
  warningLabel?: string;
  isBlocked?: boolean;
}

export const KpiHeroCard: React.FC<KpiHeroCardProps> = ({
  title,
  primaryValue,
  secondaryText,
  subValue,
  isWarning = false,
  warningLabel,
  isBlocked = false,
}) => {
  return (
    <div
      data-testid="kpi-card"
      style={{
        backgroundColor: isBlocked ? '#161d2d' : isWarning ? '#231518' : '#131b2e',
        border: `1px solid ${isWarning ? '#dc2626' : isBlocked ? '#334155' : '#23314e'}`,
        borderRadius: '10px',
        padding: '18px 20px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        position: 'relative',
        boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
      }}
    >
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <span style={{ fontSize: '13px', fontWeight: '600', color: '#94a3b8' }}>{title}</span>
          {isWarning && (
            <span
              style={{
                backgroundColor: '#450a0a',
                border: '1px solid #dc2626',
                color: '#f87171',
                fontSize: '11px',
                fontWeight: 'bold',
                padding: '2px 6px',
                borderRadius: '4px',
              }}
            >
              {warningLabel || '경고'}
            </span>
          )}
          {isBlocked && (
            <span
              style={{
                backgroundColor: '#1e293b',
                color: '#94a3b8',
                fontSize: '11px',
                padding: '2px 6px',
                borderRadius: '4px',
              }}
            >
              선행필드 누락
            </span>
          )}
        </div>

        <div
          data-testid="kpi-primary-value"
          style={{
            fontSize: '24px',
            fontWeight: '800',
            color: isBlocked ? '#94a3b8' : isWarning ? '#fca5a5' : '#f8fafc',
            letterSpacing: '-0.02em',
            marginBottom: '6px',
          }}
        >
          {primaryValue}
        </div>
      </div>

      <div>
        {subValue && (
          <div style={{ fontSize: '13px', fontWeight: '600', color: '#cbd5e1', marginBottom: '2px' }}>
            {subValue}
          </div>
        )}
        {secondaryText && (
          <div style={{ fontSize: '12px', color: '#64748b' }}>
            {secondaryText}
          </div>
        )}
      </div>
    </div>
  );
};
