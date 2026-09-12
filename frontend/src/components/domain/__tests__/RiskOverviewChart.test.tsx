import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { RiskOverviewChart } from '../RiskOverviewChart';
import type { ClauseItem } from '../../../types';

const mockClauses: ClauseItem[] = [
  {
    id: 'c-1',
    document_id: 'doc-1',
    position: 1,
    original_text: 'Indemnity...',
    simplified_text: 'You pay...',
    severity: 'High',
    category: 'Liability',
    explanation: 'Uncapped indemnity',
    status: 'analyzed',
    rule_findings: [],
    created_at: '2026-09-12T14:35:00.000Z',
    translation_available: true,
  },
  {
    id: 'c-2',
    document_id: 'doc-1',
    position: 2,
    original_text: 'Termination...',
    simplified_text: 'They can cancel...',
    severity: 'High',
    category: 'Termination',
    explanation: 'Immediate cancel',
    status: 'analyzed',
    rule_findings: [],
    created_at: '2026-09-12T14:35:00.000Z',
    translation_available: true,
  },
  {
    id: 'c-3',
    document_id: 'doc-1',
    position: 3,
    original_text: 'Renewal...',
    simplified_text: 'Rollover...',
    severity: 'Moderate',
    category: 'Renewal',
    explanation: 'Automatic rollover',
    status: 'analyzed',
    rule_findings: [],
    created_at: '2026-09-12T14:35:00.000Z',
    translation_available: true,
  },
  {
    id: 'c-4',
    document_id: 'doc-1',
    position: 4,
    original_text: 'Confidentiality...',
    simplified_text: 'Keep secret...',
    severity: 'Low',
    category: 'Confidentiality',
    explanation: 'Standard secret',
    status: 'analyzed',
    rule_findings: [],
    created_at: '2026-09-12T14:35:00.000Z',
    translation_available: true,
  },
  {
    id: 'c-5',
    document_id: 'doc-1',
    position: 5,
    original_text: 'Privacy...',
    simplified_text: 'Protect data...',
    severity: 'Safe',
    category: 'Privacy',
    explanation: 'Standard GDPR',
    status: 'analyzed',
    rule_findings: [],
    created_at: '2026-09-12T14:35:00.000Z',
    translation_available: true,
  },
];

describe('RiskOverviewChart Component (components/domain/RiskOverviewChart)', () => {
  it('renders risk distribution cards with exact counts and no numerical risk score', () => {
    render(<RiskOverviewChart clauses={mockClauses} />);

    expect(screen.getByText('Risk Severity Breakdown')).toBeInTheDocument();
    expect(screen.getByText('5 Clauses Analyzed')).toBeInTheDocument();

    // High: 2, Moderate: 1, Low: 1, Safe: 1
    expect(screen.getByTestId('risk-card-High')).toHaveTextContent('2');
    expect(screen.getByTestId('risk-card-Moderate')).toHaveTextContent('1');
    expect(screen.getByTestId('risk-card-Low')).toHaveTextContent('1');
    expect(screen.getByTestId('risk-card-Safe')).toHaveTextContent('1');

    // Strict constraint check: NO numerical composite risk score or % confidence
    expect(screen.queryByText(/%/)).not.toBeInTheDocument();
    expect(screen.queryByText(/score/i)).not.toBeInTheDocument();
  });

  it('provides accessible text alternative for screen readers', () => {
    render(<RiskOverviewChart clauses={mockClauses} />);
    expect(
      screen.getByText(/Clause severity distribution: 2 high risk, 1 moderate risk, 1 low risk, 1 safe/i)
    ).toBeInTheDocument();
  });
});
