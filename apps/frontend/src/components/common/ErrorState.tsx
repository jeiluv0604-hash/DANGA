import React from 'react';

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({ message, onRetry }) => {
  return (
    <div
      style={{
        padding: '60px 24px',
        textAlign: 'center',
        backgroundColor: '#131b2e',
        borderRadius: '12px',
        margin: '24px',
        border: '1px solid #334155',
      }}
    >
      <div style={{ fontSize: '36px', marginBottom: '12px' }}>⚡</div>
      <h3 style={{ fontSize: '18px', color: '#f8fafc', marginBottom: '8px' }}>
        데이터를 불러오지 못했습니다
      </h3>
      <p style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '20px' }}>{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            padding: '8px 20px',
            backgroundColor: '#2563eb',
            color: '#ffffff',
            borderRadius: '6px',
            fontWeight: '600',
            fontSize: '14px',
          }}
        >
          다시 시도
        </button>
      )}
    </div>
  );
};
