import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { DocumentHistoryCard } from '../DocumentHistoryCard';
import type { DocumentItem } from '../../../types';

const renderCard = (doc: DocumentItem) => {
  return render(
    <MemoryRouter>
      <DocumentHistoryCard document={doc} />
    </MemoryRouter>
  );
};

describe('DocumentHistoryCard & RiskLevelIndicator (PRD Ch. 20)', () => {
  it('renders completed high-risk document with all indicators and action links', () => {
    const highRiskDoc: DocumentItem = {
      id: 'doc-123',
      original_filename: 'Vendor_MSA_Agreement_2026.pdf',
      file_reference: 'uploads/documents/doc-123.pdf',
      document_type: 'Master Services Agreement',
      status: 'complete',
      failure_reason: null,
      overall_risk: 'high',
      uploaded_at: '2026-09-12T10:00:00.000Z',
      updated_at: '2026-09-12T10:05:00.000Z',
    };

    renderCard(highRiskDoc);

    // Filename & Category
    expect(screen.getByText('Vendor_MSA_Agreement_2026.pdf')).toBeInTheDocument();
    expect(screen.getByText(/Master Services Agreement/i)).toBeInTheDocument();

    // Status Badge
    expect(screen.getByRole('status', { name: /Status: Complete/i })).toBeInTheDocument();

    // Risk Indicator (accessible, never relies on color alone)
    const riskIndicator = screen.getByRole('status', { name: /Risk Level: High Risk/i });
    expect(riskIndicator).toBeInTheDocument();
    expect(riskIndicator).toHaveTextContent('High Risk');

    // Actions
    const viewAnalysisLink = screen.getByRole('link', {
      name: /View analysis for Vendor_MSA_Agreement_2026\.pdf/i,
    });
    expect(viewAnalysisLink).toHaveAttribute('href', '/documents/doc-123');

    const chatLink = screen.getByRole('link', {
      name: /Chat with Vendor_MSA_Agreement_2026\.pdf/i,
    });
    expect(chatLink).toHaveAttribute('href', '/documents/doc-123/chat');
  });

  it('renders moderate, low, and safe risk indicators correctly', () => {
    const moderateDoc: DocumentItem = {
      id: 'doc-mod',
      original_filename: 'Moderate_Risk.pdf',
      file_reference: 'ref',
      document_type: null,
      status: 'complete',
      failure_reason: null,
      overall_risk: 'moderate',
      uploaded_at: '2026-09-12T10:00:00.000Z',
      updated_at: '2026-09-12T10:00:00.000Z',
    };

    const { unmount } = renderCard(moderateDoc);
    expect(screen.getByRole('status', { name: /Risk Level: Moderate Risk/i })).toHaveTextContent(
      'Moderate Risk'
    );
    unmount();

    const lowDoc: DocumentItem = { ...moderateDoc, id: 'doc-low', overall_risk: 'low' };
    const { unmount: unmountLow } = renderCard(lowDoc);
    expect(screen.getByRole('status', { name: /Risk Level: Low Risk/i })).toHaveTextContent(
      'Low Risk'
    );
    unmountLow();

    const safeDoc: DocumentItem = { ...moderateDoc, id: 'doc-safe', overall_risk: 'safe' };
    renderCard(safeDoc);
    expect(screen.getByRole('status', { name: /Risk Level: Safe/i })).toHaveTextContent('Safe');
  });

  it('renders in-progress document with pending risk and processing route', () => {
    const inProgressDoc: DocumentItem = {
      id: 'doc-prog',
      original_filename: 'Lease_Draft.pdf',
      file_reference: 'ref',
      document_type: null,
      status: 'extracting',
      failure_reason: null,
      overall_risk: null,
      uploaded_at: '2026-09-12T10:00:00.000Z',
      updated_at: '2026-09-12T10:00:00.000Z',
    };

    renderCard(inProgressDoc);

    expect(screen.getByRole('status', { name: /Status: Processing/i })).toBeInTheDocument();
    expect(screen.getByRole('status', { name: /Risk Level: Pending Analysis/i })).toHaveTextContent(
      'Risk Pending'
    );

    // Links to processing page when incomplete
    const viewAnalysisLink = screen.getByRole('link', {
      name: /View analysis for Lease_Draft\.pdf/i,
    });
    expect(viewAnalysisLink).toHaveAttribute('href', '/documents/doc-prog/processing');

    // Chat link should NOT be present for incomplete documents
    expect(
      screen.queryByRole('link', { name: /Chat with Lease_Draft\.pdf/i })
    ).not.toBeInTheDocument();
  });

  it('renders failed document with failure reason and error badge', () => {
    const failedDoc: DocumentItem = {
      id: 'doc-fail',
      original_filename: 'Corrupted.pdf',
      file_reference: 'ref',
      document_type: null,
      status: 'failed',
      failure_reason: 'PDF file is password protected or corrupted.',
      overall_risk: null,
      uploaded_at: '2026-09-12T10:00:00.000Z',
      updated_at: '2026-09-12T10:00:00.000Z',
    };

    renderCard(failedDoc);

    expect(screen.getByRole('status', { name: /Status: Failed/i })).toBeInTheDocument();
    expect(
      screen.getByText('PDF file is password protected or corrupted.')
    ).toBeInTheDocument();
  });
});
