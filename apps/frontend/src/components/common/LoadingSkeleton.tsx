import React from 'react';

export const LoadingSkeleton: React.FC = () => {
  return (
    <div style={{ padding: '32px 24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ height: '48px', backgroundColor: '#1e293b', borderRadius: '8px' }} className="animate-pulse-subtle" />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
        {[1, 2, 3, 4].map((i) => (
          <div key={i} style={{ height: '140px', backgroundColor: '#131b2e', borderRadius: '10px', border: '1px solid #1e293b' }} className="animate-pulse-subtle" />
        ))}
      </div>
      <div style={{ height: '240px', backgroundColor: '#131b2e', borderRadius: '10px', border: '1px solid #1e293b' }} className="animate-pulse-subtle" />
    </div>
  );
};
