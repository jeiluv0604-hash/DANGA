import { describe, it, expect } from 'vitest';
import {
  formatWon,
  formatPercent,
  formatKg,
  formatRating,
  formatCount,
  truncateHash,
} from '../../src/utils/formatters';

describe('Formatters Unit Tests', () => {
  it('formats currency in Won correctly', () => {
    expect(formatWon(13092000)).toBe('13,092,000원');
    expect(formatWon(0)).toBe('0원');
    expect(formatWon(null, 'MISSING_INPUT')).toBe('데이터 없음');
    expect(formatWon(null, 'BLOCKED_DEPENDENCY')).toBe('계산 불가');
  });

  it('formats percent correctly', () => {
    expect(formatPercent(0.355)).toBe('35.5%');
    expect(formatPercent(0)).toBe('0.0%');
    expect(formatPercent(null, 'BLOCKED_DEPENDENCY')).toBe('계산 불가');
  });

  it('formats weight in Kg correctly', () => {
    expect(formatKg(-1.2)).toBe('-1.2kg');
    expect(formatKg(0)).toBe('0.0kg');
    expect(formatKg(2.5)).toBe('+2.5kg');
  });

  it('formats customer metrics distinguishing null vs 0', () => {
    expect(formatRating(4.65)).toBe('4.65');
    expect(formatRating(null, 'NOT_PROVIDED')).toBe('미입력');

    expect(formatCount(0, '건')).toBe('0건');
    expect(formatCount(null, '건', 'NOT_PROVIDED')).toBe('미입력');
  });

  it('truncates SHA-256 hash correctly', () => {
    const hash = '2132542be216b1cd5c610036f3c5207e189023a63e6a2aed1d3e87eeda2745cc';
    expect(truncateHash(hash, 6)).toBe('213254...2745cc');
    expect(truncateHash(undefined)).toBe('-');
  });
});
