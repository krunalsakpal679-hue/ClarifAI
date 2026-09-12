import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { routes } from '../../../app/router';
import { useAuthStore } from '../../../store/authStore';
import { useDocumentStore } from '../../../store/documentStore';
import { useClauseNavStore } from '../../../store/clauseNavStore';
import { useUIStore } from '../../../store/uiStore';
import { __resetMockDocuments, __setMockDocumentStatus } from '../../../services/mocks/documents';

const mockUser = {
  id: 'usr_counsel',
  email: 'counsel@clarifai.internal',
  fullName: 'Jane Counsel',
  preferredLanguage: 'en' as const,
  createdAt: '2026-09-12T00:00:00.000Z',
};

describe('ClauseDetailPage (PRD Ch. 12, 22.8 & Section 8.3)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    __resetMockDocuments();
    useAuthStore.getState().setAuth(mockUser, 'valid_token');
    useDocumentStore.getState().reset();
    useClauseNavStore.getState().reset();
    useUIStore.getState().setAnalysisLanguage('en');
  });

  const renderRoute = (initialPath: string) => {
    const memoryRouter = createMemoryRouter(routes, {
      initialEntries: [initialPath],
    });
    return render(<RouterProvider router={memoryRouter} />);
  };

  it('renders single clause detail with original text, plain-English breakdown, risk badge, and category tag', async () => {
    renderRoute('/documents/doc-msa-001/clauses/clause-101');

    // Wait for clause to load
    await waitFor(() => {
      expect(screen.getByText(/Clause #1 Inspection View/i)).toBeInTheDocument();
    });

    // Original verbatim text
    expect(screen.getByText(/Original Contract Text/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Customer shall defend, indemnify, and hold harmless Vendor/i)
    ).toBeInTheDocument();

    // Plain-English Breakdown & Risk Driver
    expect(
      screen.getByText(/Plain-English Breakdown & Risk Driver/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/You must pay all legal costs, damages, and attorney fees/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Uncapped unilateral indemnification disproportionately transfers/i)
    ).toBeInTheDocument();

    // 4-value RiskBadge and RiskCategoryTag
    expect(screen.getByText(/High Risk/i)).toBeInTheDocument();
    expect(screen.getByText(/^Liability$/i)).toBeInTheDocument();

    // Heuristic rule findings
    expect(screen.getByText(/R-101/i)).toBeInTheDocument();
    expect(screen.getByText(/Uncapped Customer Indemnity/i)).toBeInTheDocument();

    // Suggested negotiation counter-language
    expect(screen.getByText(/Recommended Negotiation Counter-Language/i)).toBeInTheDocument();

    // Breadcrumb navigation
    expect(screen.getByRole('link', { name: /Document Analysis/i })).toBeInTheDocument();
  });

  it('handles cold-start deep-linking directly to a clause without prior Analysis Results visit', async () => {
    // Both documentStore and clauseNavStore are empty
    expect(useDocumentStore.getState().clauses).toEqual([]);
    expect(useClauseNavStore.getState().clauseIds).toEqual([]);

    renderRoute('/documents/doc-msa-001/clauses/clause-102');

    await waitFor(() => {
      expect(screen.getByText(/Clause #2 Inspection View/i)).toBeInTheDocument();
    });

    // clauseNavStore should be hydrated with the document's clauses
    const navState = useClauseNavStore.getState();
    expect(navState.documentId).toBe('doc-msa-001');
    expect(navState.clauseIds.length).toBeGreaterThanOrEqual(4);
    expect(navState.currentIndex).toBe(1); // clause-102 is at index 1

    // Status position indicator should show Clause 2 of X
    const statusEl = screen.getAllByTestId('clause-nav-position')[0];
    expect(statusEl).toHaveTextContent(/Clause 2 of/i);
  });

  it('bounds prev/next navigation correctly on list limits', async () => {
    renderRoute('/documents/doc-msa-001/clauses/clause-101');

    await waitFor(() => {
      expect(screen.getByText(/Clause #1 Inspection View/i)).toBeInTheDocument();
    });

    // Previous buttons (top and bottom) should be disabled on the first clause
    const prevButtons = screen.getAllByRole('button', { name: /previous clause/i });
    expect(prevButtons[0]).toBeDisabled();

    // Next button should be enabled
    const nextButtons = screen.getAllByRole('button', { name: /next clause/i });
    expect(nextButtons[0]).toBeEnabled();

    // Click next button to navigate to clause 2
    fireEvent.click(nextButtons[0]);

    await waitFor(() => {
      expect(screen.getByText(/Clause #2 Inspection View/i)).toBeInTheDocument();
    });
  });

  it('displays 404 Not Found state for nonexistent clause ID', async () => {
    renderRoute('/documents/doc-msa-001/clauses/clause-non-existent-999');

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Clause Not Found/i })).toBeInTheDocument();
    });

    expect(screen.getByText(/clause-non-existent-999/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Return to Analysis Results/i })).toBeInTheDocument();
  });

  it('redirects to processing page when document is incomplete', async () => {
    __setMockDocumentStatus('doc-lease-005', 'segmenting');

    renderRoute('/documents/doc-lease-005/clauses/clause-101');

    await waitFor(() => {
      expect(screen.getByText(/Analyzing Document/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/doc-lease-005/i)).toBeInTheDocument();
  });

  it('translates clause analysis to Hindi when language toggle is clicked', async () => {
    renderRoute('/documents/doc-msa-001/clauses/clause-101');

    await waitFor(() => {
      expect(screen.getByText(/Clause #1 Inspection View/i)).toBeInTheDocument();
    });

    const translateBtn = screen.getByRole('button', { name: /Translate to हिंदी/i });
    fireEvent.click(translateBtn);

    await waitFor(() => {
      expect(
        screen.getByText(/यदि आपके डेटा या सेवा के उपयोग के कारण विक्रेता पर मुकदमा होता है/i)
      ).toBeInTheDocument();
    });
  });
});
