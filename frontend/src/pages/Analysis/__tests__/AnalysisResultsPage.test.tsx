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

  it('correctly handles lowercase severities from backend API (e.g. high, moderate, low, safe)', async () => {
    const mockClauses = [
      { id: 'c1', document_id: 'doc-mixed', position: 1, original_text: 'Text 1', simplified_text: 'Simp 1', severity: 'high' as any, category: 'Liability' as any, explanation: 'Exp 1', status: 'analyzed' as any, rule_findings: [], created_at: '', translation_available: false },
      { id: 'c2', document_id: 'doc-mixed', position: 2, original_text: 'Text 2', simplified_text: 'Simp 2', severity: 'high' as any, category: 'Liability' as any, explanation: 'Exp 2', status: 'analyzed' as any, rule_findings: [], created_at: '', translation_available: false },
      { id: 'c3', document_id: 'doc-mixed', position: 3, original_text: 'Text 3', simplified_text: 'Simp 3', severity: 'high' as any, category: 'Liability' as any, explanation: 'Exp 3', status: 'analyzed' as any, rule_findings: [], created_at: '', translation_available: false },
      { id: 'c4', document_id: 'doc-mixed', position: 4, original_text: 'Text 4', simplified_text: 'Simp 4', severity: 'moderate' as any, category: 'Payment' as any, explanation: 'Exp 4', status: 'analyzed' as any, rule_findings: [], created_at: '', translation_available: false },
      { id: 'c5', document_id: 'doc-mixed', position: 5, original_text: 'Text 5', simplified_text: 'Simp 5', severity: 'low' as any, category: 'Renewal' as any, explanation: 'Exp 5', status: 'analyzed' as any, rule_findings: [], created_at: '', translation_available: false },
      { id: 'c6', document_id: 'doc-mixed', position: 6, original_text: 'Text 6', simplified_text: 'Simp 6', severity: 'safe' as any, category: 'Confidentiality' as any, explanation: 'Exp 6', status: 'analyzed' as any, rule_findings: [], created_at: '', translation_available: false },
    ];
    vi.spyOn(documentService, 'getById').mockResolvedValueOnce({
      id: 'doc-mixed',
      original_filename: 'test.pdf',
      file_reference: 'test.pdf',
      document_type: 'Master Services Agreement',
      status: 'complete',
      failure_reason: null,
      overall_risk: 'high',
      uploaded_at: '',
      updated_at: '',
    });
    vi.spyOn(documentService, 'getClauses').mockResolvedValueOnce({
      count: 6,
      next: null,
      previous: null,
      results: mockClauses,
    });

    renderAnalysisPage('doc-mixed');

    await waitFor(() => {
      expect(screen.getByTestId('clause-list')).toBeInTheDocument();
    });

    // Check counts: Total 6, Flagged 5 (3 high + 1 mod + 1 low), High 3
    expect(screen.getByText('Total Clauses').parentElement).toHaveTextContent('6');
    expect(screen.getByText('Flagged Clauses').parentElement).toHaveTextContent('5');
    expect(screen.getByText('High Severity Count').parentElement).toHaveTextContent('3');

    // Check filter buttons
    const riskyBtn = screen.getByRole('button', { name: /Risky \(5\)/i });
    const safeBtn = screen.getByRole('button', { name: /Safe \(1\)/i });
    expect(riskyBtn).toBeInTheDocument();
    expect(safeBtn).toBeInTheDocument();

    // Positive empty state must NOT be rendered
    expect(screen.queryByTestId('positive-empty-state')).not.toBeInTheDocument();
    expect(screen.queryByText('All Analyzed Clauses Classified as Safe')).not.toBeInTheDocument();

    // Clicking Safe shows only safe clause
    fireEvent.click(safeBtn);
    expect(screen.getByText('Clause #6')).toBeInTheDocument();
    expect(screen.queryByText('Clause #1')).not.toBeInTheDocument();
  });
});
