export function formatWon(value: number | null | undefined, kpiStatus?: string): string {
  if (kpiStatus === 'MISSING_INPUT') return '데이터 없음';
  if (kpiStatus === 'BLOCKED_DEPENDENCY') return '계산 불가';
  if (kpiStatus === 'NOT_PROVIDED') return '미입력';
  if (value === null || value === undefined) return '데이터 없음';
  return `${new Intl.NumberFormat('ko-KR').format(Math.round(value))}원`;
}

export function formatWonSummary(value: number | null | undefined): string {
  if (value === null || value === undefined) return '-';
  if (value >= 100_000_000) {
    const eok = (value / 100_000_000).toFixed(2);
    return `${eok}억원 (${new Intl.NumberFormat('ko-KR').format(Math.round(value))}원)`;
  }
  return formatWon(value);
}

export function formatPercent(value: number | null | undefined, kpiStatus?: string): string {
  if (kpiStatus === 'MISSING_INPUT') return '데이터 없음';
  if (kpiStatus === 'BLOCKED_DEPENDENCY') return '계산 불가';
  if (kpiStatus === 'NOT_PROVIDED') return '미입력';
  if (value === null || value === undefined) return '데이터 없음';
  return `${(value * 100).toFixed(1)}%`;
}

export function formatKg(value: number | null | undefined, kpiStatus?: string): string {
  if (kpiStatus === 'MISSING_INPUT') return '데이터 없음';
  if (kpiStatus === 'BLOCKED_DEPENDENCY') return '계산 불가';
  if (kpiStatus === 'NOT_PROVIDED') return '미입력';
  if (value === null || value === undefined) return '데이터 없음';
  const prefix = value > 0 ? '+' : '';
  return `${prefix}${value.toFixed(1)}kg`;
}

export function formatRating(value: number | null | undefined, kpiStatus?: string): string {
  if (kpiStatus === 'NOT_PROVIDED' || value === null || value === undefined) return '미입력';
  return value.toFixed(2);
}

export function formatCount(value: number | null | undefined, unit: string = '건', kpiStatus?: string): string {
  if (kpiStatus === 'NOT_PROVIDED' || value === null || value === undefined) return '미입력';
  return `${value}${unit}`;
}

export function truncateHash(hash: string | undefined, length: number = 8): string {
  if (!hash) return '-';
  if (hash.length <= length * 2) return hash;
  return `${hash.slice(0, length)}...${hash.slice(-length)}`;
}

