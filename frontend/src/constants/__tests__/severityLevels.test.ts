import { describe, it, expect } from 'vitest';
import {
  isRiskySeverity,
  isSafeSeverity,
  normalizeSeverity,
} from '../severityLevels';

describe('severityLevels utilities', () => {
  it('correctly normalizes all case variations to canonical SeverityLevel', () => {
    expect(normalizeSeverity('high')).toBe('High');
    expect(normalizeSeverity('HIGH')).toBe('High');
    expect(normalizeSeverity('High')).toBe('High');

    expect(normalizeSeverity('moderate')).toBe('Moderate');
    expect(normalizeSeverity('MODERATE')).toBe('Moderate');
    expect(normalizeSeverity('Moderate')).toBe('Moderate');

    expect(normalizeSeverity('low')).toBe('Low');
    expect(normalizeSeverity('LOW')).toBe('Low');
    expect(normalizeSeverity('Low')).toBe('Low');

    expect(normalizeSeverity('safe')).toBe('Safe');
    expect(normalizeSeverity('SAFE')).toBe('Safe');
    expect(normalizeSeverity('Safe')).toBe('Safe');

    expect(normalizeSeverity('unknown')).toBeNull();
    expect(normalizeSeverity(null)).toBeNull();
    expect(normalizeSeverity(undefined)).toBeNull();
  });

  it('isRiskySeverity identifies High, Moderate, and Low regardless of casing', () => {
    // Canonical
    expect(isRiskySeverity('High')).toBe(true);
    expect(isRiskySeverity('Moderate')).toBe(true);
    expect(isRiskySeverity('Low')).toBe(true);
    expect(isRiskySeverity('Safe')).toBe(false);

    // Backend API lowercase
    expect(isRiskySeverity('high')).toBe(true);
    expect(isRiskySeverity('moderate')).toBe(true);
    expect(isRiskySeverity('low')).toBe(true);
    expect(isRiskySeverity('safe')).toBe(false);

    // Edge cases
    expect(isRiskySeverity(null)).toBe(false);
    expect(isRiskySeverity(undefined)).toBe(false);
    expect(isRiskySeverity('invalid')).toBe(false);
  });

  it('isSafeSeverity identifies Safe regardless of casing', () => {
    expect(isSafeSeverity('Safe')).toBe(true);
    expect(isSafeSeverity('safe')).toBe(true);
    expect(isSafeSeverity('SAFE')).toBe(true);

    expect(isSafeSeverity('High')).toBe(false);
    expect(isSafeSeverity('high')).toBe(false);
    expect(isSafeSeverity('moderate')).toBe(false);
    expect(isSafeSeverity('low')).toBe(false);
    expect(isSafeSeverity(null)).toBe(false);
  });
});
