import React from 'react';

interface EmptyStateProps {
  message: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ message }) => {
  return (
    <div
      style={{
        padding: '40px 20px',
        textAlign: 'center',
        color: '#64748b',
        fontSize: '14px',
        backgroundColor: '#0f172a',
        borderRadius: '8px',
        border: '1px dashed #1e293b',
      }}
    >
      {message}
    </div>
  );
};
