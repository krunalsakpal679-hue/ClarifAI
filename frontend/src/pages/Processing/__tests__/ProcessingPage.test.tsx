import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ProcessingPage } from '../index';
import { documentService } from '../../../services/api';
import { toast } from '../../../components/ui/Toast';
import '../../../app/i18n';

// Spy on Toast methods
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

describe('ProcessingPage (PRD Ch. 15.1 & Section 8.2)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderProcessingPage = (docId = 'doc-test-456') => {
    return render(
      <MemoryRouter initialEntries={[`/documents/${docId}/processing`]}>
        <Routes>
          <Route path="/documents/:id/processing" element={<ProcessingPage />} />
        </Routes>
      </MemoryRouter>
    );
  };

  it('renders page header with Analyzing Document, document ID, and all nine stages', async () => {
    vi.spyOn(documentService, 'getById').mockResolvedValueOnce({
      id: 'doc-test-456',
      original_filename: 'Master_Services_Agreement.pdf',
      file_reference: 'uploads/documents/doc-test-456.pdf',
      document_type: 'Master Services Agreement',
      status: 'extracting',
      failure_reason: null,
      overall_risk: null,
      uploaded_at: '2026-09-12T14:30:00.000Z',
      updated_at: '2026-09-12T14:35:00.000Z',
    });

    renderProcessingPage('doc-test-456');

    expect(screen.getByRole('heading', { name: /Analyzing Document/i })).toBeInTheDocument();
    expect(screen.getByText(/doc-test-456/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Master_Services_Agreement.pdf')).toBeInTheDocument();
    });

    // Check all 9 stages are visible simultaneously
    expect(screen.getByText('Validating document')).toBeInTheDocument();
    expect(screen.getByText('Extracting text')).toBeInTheDocument();
    expect(screen.getByText('Running OCR (conditional)')).toBeInTheDocument();
    expect(screen.getByText('Segmenting clauses')).toBeInTheDocument();
    expect(screen.getByText('Analyzing risks')).toBeInTheDocument();
    expect(screen.getByText('Simplifying clauses')).toBeInTheDocument();
    expect(screen.getByText('Generating summary')).toBeInTheDocument();
    expect(screen.getByText('Preparing chatbot')).toBeInTheDocument();
    expect(screen.getByText('Complete')).toBeInTheDocument();

    // Check live announcement region
    const liveRegion = screen.getByTestId('processing-live-region');
    expect(liveRegion).toHaveAttribute('aria-live', 'polite');
  });

  it('navigates to /documents/:id on status complete (PRD Ch. 15.1 hand-off)', async () => {
    vi.spyOn(documentService, 'getById').mockResolvedValueOnce({
      id: 'doc-test-456',
      original_filename: 'Completed_NDA.pdf',
      file_reference: 'uploads/documents/doc-test-456.pdf',
      document_type: 'NDA',
      status: 'complete',
      failure_reason: null,
      overall_risk: 'low',
      uploaded_at: '2026-09-12T14:30:00.000Z',
      updated_at: '2026-09-12T14:35:00.000Z',
    });

    renderProcessingPage('doc-test-456');

    await waitFor(() => {
      expect(mockedNavigate).toHaveBeenCalledWith('/documents/doc-test-456');
    });

    expect(toast.success).toHaveBeenCalledWith('Document analysis complete!');
  });

  it('displays failure card with stage, reason, and retry action on status failed', async () => {
    const getByIdSpy = vi.spyOn(documentService, 'getById').mockResolvedValueOnce({
      id: 'doc-test-456',
      original_filename: 'Broken_PDF.pdf',
      file_reference: 'uploads/documents/doc-test-456.pdf',
      document_type: null,
      status: 'failed',
      failure_reason: 'PDF OCR processing failed due to unreadable scanned resolution.',
      overall_risk: null,
      uploaded_at: '2026-09-12T14:30:00.000Z',
      updated_at: '2026-09-12T14:35:00.000Z',
    });

    renderProcessingPage('doc-test-456');

    await waitFor(() => {
      expect(screen.getByTestId('processing-failed-banner')).toBeInTheDocument();
    });

    expect(screen.getByText('Document Processing Failed')).toBeInTheDocument();
    expect(
      screen.getByText('PDF OCR processing failed due to unreadable scanned resolution.')
    ).toBeInTheDocument();

    // Click retry
    const retryBtn = screen.getByRole('button', { name: /Retry Analysis/i });
    expect(retryBtn).toBeInTheDocument();

    fireEvent.click(retryBtn);
    expect(getByIdSpy).toHaveBeenCalledTimes(2);
  });
});
