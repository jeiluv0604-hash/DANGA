export function getSeverityStyle(severity: 'CRITICAL' | 'HIGH' | 'MEDIUM') {
  switch (severity) {
    case 'CRITICAL':
      return {
        badgeBg: '#450a0a',
        badgeText: '#f87171',
        border: '#991b1b',
        indicator: '#ef4444',
        label: 'CRITICAL',
      };
    case 'HIGH':
      return {
        badgeBg: '#431407',
        badgeText: '#fb923c',
        border: '#9a3412',
        indicator: '#f97316',
        label: 'HIGH',
      };
    case 'MEDIUM':
      return {
        badgeBg: '#422006',
        badgeText: '#fde047',
        border: '#854d0e',
        indicator: '#eab308',
        label: 'MEDIUM',
      };
  }
}
