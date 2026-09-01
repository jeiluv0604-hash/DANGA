import React from 'react';

export interface DatasetBadgeProps {
  datasetType?: 'SYNTHETIC' | 'ADVERSARIAL' | 'SHADOW_REAL' | 'REAL';
}

export const SyntheticBadge: React.FC<DatasetBadgeProps> = ({ datasetType = 'SYNTHETIC' }) => {
  if (datasetType === 'SHADOW_REAL') {
    return (
      <div
        data-testid="shadow-real-badge"
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          backgroundColor: '#311042',
          border: '1px solid #c084fc',
          color: '#f3e8ff',
          padding: '4px 10px',
          borderRadius: '6px',
          fontSize: '12px',
          fontWeight: 'bold',
          letterSpacing: '0.02em',
          boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
        }}
      >
        <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#c084fc' }} />
        <span>SHADOW REAL - 실제 데이터 검증 중 · 운영 판단용 아님</span>
      </div>
    );
  }

  if (datasetType === 'REAL') {
    return (
      <div
        data-testid="real-badge"
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          backgroundColor: '#064e3b',
          border: '1px solid #10b981',
          color: '#d1fae5',
          padding: '4px 10px',
          borderRadius: '6px',
          fontSize: '12px',
          fontWeight: 'bold',
          letterSpacing: '0.02em',
        }}
      >
        <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#10b981' }} />
        <span>REAL OPERATIONAL · 운영 데이터</span>
      </div>
    );
  }

  return (
    <div
      data-testid="synthetic-badge"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        backgroundColor: '#422006',
        border: '1px solid #d97706',
        color: '#fef3c7',
        padding: '4px 10px',
        borderRadius: '6px',
        fontSize: '12px',
        fontWeight: 'bold',
        letterSpacing: '0.02em',
        boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
      }}
    >
      <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#f59e0b' }} />
      <span>SYNTHETIC · 실제 매장 데이터 아님</span>
    </div>
  );
};

