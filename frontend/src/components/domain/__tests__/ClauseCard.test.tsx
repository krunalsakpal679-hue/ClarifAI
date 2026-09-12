import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ClauseCard } from '../ClauseCard';
import type { ClauseItem } from '../../../types';

const standardClause: ClauseItem = {
  id: 'clause-101',
  document_id: 'doc-msa-001',
  position: 1,
  original_text: 'Customer shall defend and indemnify Vendor without limitation.',
  simplified_text: 'You must pay all legal costs without limit if the vendor is sued.',
  severity: 'High',
  category: 'Liability',
  explanation: 'Uncapped unilateral indemnity creates severe exposure.',
  status: 'analyzed',
  rule_findings: [
    {
      rule_id: 'R-101',
      rule_name: 'Uncapped Customer Indemnity',
      severity: 'High',
      matched_text: 'without limitation',
    },
  ],
  created_at: '2026-09-12T14:35:00.000Z',
  translation_available: true,
};

const failedClause: ClauseItem = {
  id: 'clause-fail-999',
  document_id: 'doc-msa-001',
  position: 9,
  original_text: 'Complex tariff clause intersecting statutory cross-references.',
  simplified_text: '',
  severity: null,
  category: null,
  explanation: 'Automated engine could not classify risk due to overlapping cross-references.',
  status: 'failed',
  rule_findings: [],
  created_at: '2026-09-12T14:35:00.000Z',
  translation_available: false,
};

describe('ClauseCard Component (components/domain/ClauseCard)', () => {
  it('renders standard clause with original, simplified, explanation, and risk badge', () => {
    render(
      <MemoryRouter>
        <ClauseCard clause={standardClause} documentId="doc-msa-001" />
      </MemoryRouter>
    );

    expect(screen.getByText('Clause #1')).toBeInTheDocument();
    expect(screen.getByText('High Risk')).toBeInTheDocument();
    expect(screen.getByText('Liability')).toBeInTheDocument();

    expect(screen.getByText('Plain-English Summary')).toBeInTheDocument();
    expect(screen.getByText('You must pay all legal costs without limit if the vendor is sued.')).toBeInTheDocument();

    expect(screen.getByText('Risk Driver & Legal Context')).toBeInTheDocument();
    expect(screen.getByText('Uncapped unilateral indemnity creates severe exposure.')).toBeInTheDocument();

    expect(screen.getByText('Original Contract Text')).toBeInTheDocument();
    expect(screen.getByText(/Customer shall defend and indemnify Vendor without limitation/)).toBeInTheDocument();

    // Link to Clause Detail page (Phase 09)
    const detailLink = screen.getByRole('link', { name: /Inspect Clause Details/i });
    expect(detailLink).toHaveAttribute('href', '/documents/doc-msa-001/clauses/clause-101');
  });

  it('renders explicit classification-failed state without defaulting to Safe per PRD Ch. 16.5', () => {
    render(
      <MemoryRouter>
        <ClauseCard clause={failedClause} documentId="doc-msa-001" />
      </MemoryRouter>
    );

    expect(screen.getByText('Clause #9')).toBeInTheDocument();
    expect(screen.getByText('Classification Incomplete')).toBeInTheDocument();
    expect(screen.getByText(/Preserved verbatim without defaulting to Safe/i)).toBeInTheDocument();

    // Crucial PRD constraint: Never default to Safe
    expect(screen.queryByText('Safe')).not.toBeInTheDocument();

    // Verbatim original text is preserved
    expect(screen.getByText(/Complex tariff clause intersecting statutory cross-references/)).toBeInTheDocument();

    // Explanation is surfaced
    expect(screen.getByText(/Automated engine could not classify risk/i)).toBeInTheDocument();
  });
});
