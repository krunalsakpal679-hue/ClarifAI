/**
 * ClarifAI 4-Value Severity Model Specification (PRD Ch. 16, 22.0 & Section 9.1)
 *
 * Strict Rule: Only 4 severity values exist (High, Moderate, Low, Safe).
 * There is NO boolean isRisky field and NO numerical risk score.
 */

export type SeverityLevel = 'High' | 'Moderate' | 'Low' | 'Safe';

export interface SeverityDefinition {
  id: SeverityLevel;
  label: string;
  description: string;
  badgeBg: string;
  badgeText: string;
  badgeBorder: string;
  barColor: string;
  order: number;
}

export const SEVERITY_LEVELS: SeverityLevel[] = ['High', 'Moderate', 'Low', 'Safe'];

export const SEVERITY_DEFINITIONS: Record<SeverityLevel, SeverityDefinition> = {
  High: {
    id: 'High',
    label: 'High Risk',
    description: 'Critical legal, liability, or financial hazard requiring immediate review or renegotiation',
    badgeBg: 'bg-risk-high-bg',
    badgeText: 'text-risk-high-text',
    badgeBorder: 'border-risk-high-border',
    barColor: 'bg-risk-high',
    order: 0,
  },
  Moderate: {
    id: 'Moderate',
    label: 'Moderate Risk',
    description: 'Notable commercial or operational exposure warranting negotiation or protective safeguards',
    badgeBg: 'bg-risk-moderate-bg',
    badgeText: 'text-risk-moderate-text',
    badgeBorder: 'border-risk-moderate-border',
    barColor: 'bg-risk-moderate',
    order: 1,
  },
  Low: {
    id: 'Low',
    label: 'Low Risk',
    description: 'Minor ambiguity or slight contractual imbalance with limited financial exposure',
    badgeBg: 'bg-risk-low-bg',
    badgeText: 'text-risk-low-text',
    badgeBorder: 'border-risk-low-border',
    barColor: 'bg-risk-low',
    order: 2,
  },
  Safe: {
    id: 'Safe',
    label: 'Safe',
    description: 'Standard, balanced, mutual, or benign boilerplate clause with minimal risk',
    badgeBg: 'bg-risk-safe-bg',
    badgeText: 'text-risk-safe-text',
    badgeBorder: 'border-risk-safe-border',
    barColor: 'bg-risk-safe',
    order: 3,
  },
};

/**
 * Flagged clauses include High, Moderate, and Low severities.
 * Safe clauses are non-flagged.
 */
export const isRiskySeverity = (severity?: SeverityLevel | null): boolean => {
  if (!severity) return false;
  return severity === 'High' || severity === 'Moderate' || severity === 'Low';
};

/**
 * Normalizes case-insensitive API inputs (e.g. 'high', 'HIGH', 'High') to the canonical SeverityLevel.
 */
export const normalizeSeverity = (val?: string | null): SeverityLevel | null => {
  if (!val) return null;
  const lower = val.toLowerCase().trim();
  switch (lower) {
    case 'high':
      return 'High';
    case 'moderate':
      return 'Moderate';
    case 'low':
      return 'Low';
    case 'safe':
      return 'Safe';
    default:
      return null;
  }
};
