import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { SummaryPanel } from '../SummaryPanel';
import type { DocumentSummary } from '../../../types';

const mockSummary: DocumentSummary = {
  id: 'sum-1',
  document_id: 'doc-1',
  purpose_text: 'Purpose of the enterprise cloud services agreement.',
  key_risks_text: 'Uncapped customer indemnification and short termination notice.',
  key_terms_text: '36-month term, auto-renewal, Net 30 payment.',
  obligations_text: 'Maintain SOC2 compliance and confidentiality.',
  created_at: '2026-09-12T14:35:00.000Z',
  updated_at: '2026-09-12T14:35:00.000Z',
  translation_available: true,
};

describe('SummaryPanel Component (components/domain/SummaryPanel)', () => {
  it('renders all four executive summary sections when data is loaded', () => {
    render(<SummaryPanel summary={mockSummary} isLoading={false} />);

    expect(screen.getByText('Executive Plain-Language Summary')).toBeInTheDocument();
    expect(screen.getByText('Contract Purpose & Scope')).toBeInTheDocument();
    expect(screen.getByText('Purpose of the enterprise cloud services agreement.')).toBeInTheDocument();

    expect(screen.getByText('Key Liabilities & Risks')).toBeInTheDocument();
    expect(screen.getByText('Uncapped customer indemnification and short termination notice.')).toBeInTheDocument();

    expect(screen.getByText('Essential Commercial Terms')).toBeInTheDocument();
    expect(screen.getByText('36-month term, auto-renewal, Net 30 payment.')).toBeInTheDocument();

    expect(screen.getByText('Operational Obligations')).toBeInTheDocument();
    expect(screen.getByText('Maintain SOC2 compliance and confidentiality.')).toBeInTheDocument();
  });

  it('renders independent loading skeleton state while keeping title visible', () => {
    render(<SummaryPanel summary={null} isLoading={true} />);

    expect(screen.getByTestId('summary-panel-skeleton')).toBeInTheDocument();
    expect(screen.getByText('Executive Plain-Language Summary')).toBeInTheDocument();
  });

  it('renders error state with retry button when error occurs', () => {
    const retryFn = vi.fn();
    render(<SummaryPanel summary={null} isLoading={false} error="Summary service failure" onRetry={retryFn} />);

    expect(screen.getByText('Executive Summary Unavailable')).toBeInTheDocument();
    expect(screen.getByText('Summary service failure')).toBeInTheDocument();

    const retryBtn = screen.getByRole('button', { name: /Retry Loading Summary/i });
    expect(retryBtn).toBeInTheDocument();
    fireEvent.click(retryBtn);
    expect(retryFn).toHaveBeenCalledTimes(1);
  });

  it('renders translation unavailable warning when Hindi requested but translation is unavailable', () => {
    const untranslatedSummary: DocumentSummary = {
      ...mockSummary,
      translation_available: false,
    };

    render(<SummaryPanel summary={untranslatedSummary} isLoading={false} lang="hi" />);
    expect(screen.getByText(/Hindi translation unavailable \(English fallback\)/i)).toBeInTheDocument();
  });
});
