import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AnalysisResultsPage } from '../index';
import { documentService } from '../../../services/api';
import { toast } from '../../../components/ui/Toast';
import '../../../app/i18n';

vi.spyOn(toast, 'info');
vi.spyOn(toast, 'success');
vi.spyOn(toast, 'error');

const mockedNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockedNavigate,
  };
});

describe('AnalysisResultsPage (PRD Ch. 16, 22.7 & Section 8.3)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderAnalysisPage = (docId = 'doc-msa-001') => {
    return render(
      <MemoryRouter initialEntries={[`/documents/${docId}`]}>
        <Routes>
          <Route path="/documents/:id" element={<AnalysisResultsPage />} />
        </Routes>
      </MemoryRouter>
    );
  };

  it('renders summary and clause list from mock services with metrics and no numerical score', async () => {
    renderAnalysisPage('doc-msa-001');

    // Header checks
    expect(screen.getByText(/Master Services Agreement Analysis/i)).toBeInTheDocument();
    expect(screen.getByText(/Executive Plain-Language Summary/i)).toBeInTheDocument();

    // Skeletons are visible while data is fetching
    expect(screen.getByTestId('summary-panel-skeleton')).toBeInTheDocument();
    expect(screen.getByTestId('clauses-loading-skeletons')).toBeInTheDocument();

    // Await independent data loading
    await waitFor(() => {
      expect(screen.getByTestId('summary-panel')).toBeInTheDocument();
      expect(screen.getByTestId('clause-list')).toBeInTheDocument();
    });

    // Check Metrics Bar: Total: 9, Flagged: 6 (High 2, Mod 2, Low 2), High: 2
    expect(screen.getByText('Total Clauses')).toBeInTheDocument();
    expect(screen.getByText('Flagged Clauses')).toBeInTheDocument();
    expect(screen.getByText('High Severity Count')).toBeInTheDocument();

    // Check PRD Constraint: NO numerical score anywhere in rendered output
    expect(screen.queryByText(/confidence score/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/composite score/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/risk score/i)).not.toBeInTheDocument();
  });

  it('filter toolbar correctly narrows to All, Risky, and Safe', async () => {
    renderAnalysisPage('doc-msa-001');

    await waitFor(() => {
      expect(screen.getByTestId('clause-list')).toBeInTheDocument();
    });

    // Toolbar buttons
    const allBtn = screen.getByRole('button', { name: /All \(/i });
    const riskyBtn = screen.getByRole('button', { name: /Risky \(/i });
    const safeBtn = screen.getByRole('button', { name: /Safe \(/i });

    expect(allBtn).toBeInTheDocument();
    expect(riskyBtn).toBeInTheDocument();
    expect(safeBtn).toBeInTheDocument();

    // Click "Risky"
    fireEvent.click(riskyBtn);
    expect(screen.getByText('Clause #1')).toBeInTheDocument(); // High
    expect(screen.getByText('Clause #3')).toBeInTheDocument(); // Moderate
    expect(screen.queryByText('Clause #7')).not.toBeInTheDocument(); // Safe clause should be filtered out

    // Click "Safe"
    fireEvent.click(safeBtn);
    expect(screen.getByText('Clause #7')).toBeInTheDocument(); // Safe
    expect(screen.getByText('Clause #8')).toBeInTheDocument(); // Safe
    expect(screen.queryByText('Clause #1')).not.toBeInTheDocument(); // High clause should be filtered out

    // Click "All"
    fireEvent.click(allBtn);
    expect(screen.getByText('Clause #1')).toBeInTheDocument();
    expect(screen.getByText('Clause #7')).toBeInTheDocument();
    expect(screen.getByText('Clause #9')).toBeInTheDocument(); // Unclassified clause visible in All
  });

  it('renders positive empty state when document contains only Safe clauses', async () => {
    renderAnalysisPage('doc-safe-001');

    await waitFor(() => {
      expect(screen.getByTestId('positive-empty-state')).toBeInTheDocument();
    });

    expect(screen.getByText('All Analyzed Clauses Classified as Safe')).toBeInTheDocument();
    expect(screen.getByText(/No unilateral indemnity clauses, uncapped damages/i)).toBeInTheDocument();
  });

  it('renders PRD Ch. 16.5 failed classification clause distinctly', async () => {
    renderAnalysisPage('doc-msa-001');

    await waitFor(() => {
      expect(screen.getByTestId('clause-card-clause-109')).toBeInTheDocument();
    });

    const failedCard = screen.getByTestId('clause-card-clause-109');
    expect(failedCard).toHaveTextContent('Classification Incomplete');
    expect(failedCard).toHaveTextContent(/Preserved verbatim without defaulting to Safe/i);
    expect(failedCard).toHaveTextContent(/conflicting international cross-references/i);
  });

  it('switches analysis language to Hindi and re-fetches endpoints with lang=hi', async () => {
    const getSummarySpy = vi.spyOn(documentService, 'getSummary');
    const getClausesSpy = vi.spyOn(documentService, 'getClauses');

    renderAnalysisPage('doc-msa-001');

    await waitFor(() => {
      expect(screen.getByTestId('summary-panel')).toBeInTheDocument();
    });

    const hindiBtn = screen.getByRole('button', { name: /हिंदी \(Hindi\)/i });
    fireEvent.click(hindiBtn);

    await waitFor(() => {
      expect(getSummarySpy).toHaveBeenCalledWith('doc-msa-001', 'hi');
      expect(getClausesSpy).toHaveBeenCalledWith('doc-msa-001', 'hi');
    });
  });

  it('redirects to /documents/:id/processing when document status is not complete', async () => {
    renderAnalysisPage('doc-lease-005'); // status: 'extracting'

    await waitFor(() => {
      expect(mockedNavigate).toHaveBeenCalledWith('/documents/doc-lease-005/processing', { replace: true });
    });
  });

  it('renders not-found state when document does not exist (404)', async () => {
    vi.spyOn(documentService, 'getById').mockRejectedValueOnce(new Error('Document not found with ID doc-unknown (404)'));

    renderAnalysisPage('doc-unknown');

    await waitFor(() => {
      expect(screen.getByTestId('analysis-not-found')).toBeInTheDocument();
    });

    expect(screen.getByText('Document Not Found')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Return to Dashboard/i })).toBeInTheDocument();
  });
});
