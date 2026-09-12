import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { HistoryPage } from '../index';
import { useDocumentStore } from '../../../store/documentStore';
import { documentService } from '../../../services/api';
import {
  __setMockDocuments,
  __resetMockDocuments,
  INITIAL_MOCK_DOCUMENTS,
} from '../../../services/mocks/documents';
import { toast } from '../../../components/ui/Toast';
import '../../../app/i18n';

// Spy on Toast methods
vi.spyOn(toast, 'success');
vi.spyOn(toast, 'error');

describe('HistoryPage (PRD Ch. 22.12, 24, 59 & Section 8.2)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    __resetMockDocuments();
    useDocumentStore.getState().reset();
  });

  const renderHistory = () => {
    return render(
      <MemoryRouter>
        <HistoryPage />
      </MemoryRouter>
    );
  };

  it('renders page header, upload CTA, and full document archive table', async () => {
    renderHistory();

    expect(screen.getByRole('heading', { name: /Document History/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /\+ Upload New Document/i })).toHaveAttribute('href', '/upload');

    // Wait for documents to load
    const firstDoc = INITIAL_MOCK_DOCUMENTS[0];
    await waitFor(() => {
      expect(screen.getAllByText(firstDoc.original_filename).length).toBeGreaterThanOrEqual(1);
    });

    expect(screen.getByRole('table', { name: 'Document History' })).toBeInTheDocument();

    // Check all initial mock documents are rendered untruncated
    INITIAL_MOCK_DOCUMENTS.forEach((doc) => {
      expect(screen.getAllByText(doc.original_filename).length).toBeGreaterThanOrEqual(1);
    });

    // Check table headers
    expect(screen.getByRole('columnheader', { name: /Document Name/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /Status/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /Risk Severity/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /Upload Date/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /Actions/i })).toBeInTheDocument();
  });

  it('strictly adheres to PRD Ch. 59: does NOT contain search, filter, or sort controls', async () => {
    renderHistory();

    const firstDoc = INITIAL_MOCK_DOCUMENTS[0];
    await waitFor(() => {
      expect(screen.getAllByText(firstDoc.original_filename).length).toBeGreaterThanOrEqual(1);
    });

    // Verify absence of search inputs
    expect(screen.queryByPlaceholderText(/search/i)).not.toBeInTheDocument();
    expect(screen.queryByRole('search')).not.toBeInTheDocument();
    expect(screen.queryByRole('searchbox')).not.toBeInTheDocument();

    // Verify absence of filter controls
    expect(screen.queryByLabelText(/filter/i)).not.toBeInTheDocument();
    expect(screen.queryByRole('combobox', { name: /filter/i })).not.toBeInTheDocument();

    // Verify absence of sort headers/buttons
    expect(screen.queryByRole('button', { name: /sort/i })).not.toBeInTheDocument();
  });

  it('renders mobile card view for responsive screens (PRD Ch. 24)', async () => {
    renderHistory();

    const firstDoc = INITIAL_MOCK_DOCUMENTS[0];
    await waitFor(() => {
      expect(screen.getAllByText(firstDoc.original_filename).length).toBeGreaterThanOrEqual(1);
    });

    const mobileCards = screen.getByTestId('mobile-cards-view');
    expect(mobileCards).toHaveClass('md:hidden');
  });

  it('opens confirmation modal when delete button is clicked, and cancels safely', async () => {
    renderHistory();

    const targetDoc = INITIAL_MOCK_DOCUMENTS[0];
    await waitFor(() => {
      expect(screen.getAllByText(targetDoc.original_filename).length).toBeGreaterThanOrEqual(1);
    });

    const deleteBtns = screen.getAllByRole('button', {
      name: `Delete ${targetDoc.original_filename}`,
    });
    expect(deleteBtns.length).toBeGreaterThanOrEqual(1);

    // Click delete
    fireEvent.click(deleteBtns[0]);

    // Modal should be visible
    const modal = screen.getByRole('dialog');
    expect(modal).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Delete Document' })).toBeInTheDocument();
    expect(screen.getByText(/This action cannot be undone/i)).toBeInTheDocument();
    expect(within(modal).getByText(new RegExp(targetDoc.original_filename, 'i'))).toBeInTheDocument();

    // Cancel deletion
    const cancelBtn = screen.getByRole('button', { name: /Cancel/i });
    fireEvent.click(cancelBtn);

    // Modal should close and document remains
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(screen.getAllByText(targetDoc.original_filename).length).toBeGreaterThanOrEqual(1);
  });

  it('deletes document when confirmed, updates store, and triggers success toast', async () => {
    renderHistory();

    const targetDoc = INITIAL_MOCK_DOCUMENTS[0];
    await waitFor(() => {
      expect(screen.getAllByText(targetDoc.original_filename).length).toBeGreaterThanOrEqual(1);
    });

    const deleteBtns = screen.getAllByRole('button', {
      name: `Delete ${targetDoc.original_filename}`,
    });

    fireEvent.click(deleteBtns[0]);

    // Confirm deletion inside modal
    const confirmBtn = screen.getByRole('button', { name: /Delete Document/i });
    fireEvent.click(confirmBtn);

    // Wait for deletion to complete and modal to close
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    // Toast success called
    expect(toast.success).toHaveBeenCalledWith(
      expect.stringContaining(`"${targetDoc.original_filename}" was deleted`)
    );

    // Document is removed from view
    expect(screen.queryByText(targetDoc.original_filename)).not.toBeInTheDocument();
  });

  it('handles delete failure: displays error toast and leaves document list intact', async () => {
    renderHistory();

    const targetDoc = INITIAL_MOCK_DOCUMENTS[0];
    await waitFor(() => {
      expect(screen.getAllByText(targetDoc.original_filename).length).toBeGreaterThanOrEqual(1);
    });

    // Mock delete failure
    vi.spyOn(documentService, 'delete').mockRejectedValueOnce(
      new Error('Server error deleting file')
    );

    const deleteBtns = screen.getAllByRole('button', {
      name: `Delete ${targetDoc.original_filename}`,
    });

    fireEvent.click(deleteBtns[0]);

    const confirmBtn = screen.getByRole('button', { name: /Delete Document/i });
    fireEvent.click(confirmBtn);

    // Wait for error handling
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Failed to delete document. Please try again.');
    });

    // Document should still be present in the document list
    expect(screen.getAllByText(targetDoc.original_filename).length).toBeGreaterThanOrEqual(1);
  });

  it('renders clean empty state with Upload CTA when document list is empty', async () => {
    __setMockDocuments([]);

    renderHistory();

    await waitFor(() => {
      expect(screen.getByText('No documents in history')).toBeInTheDocument();
    });

    expect(
      screen.getByText(/Your document repository is currently empty/i)
    ).toBeInTheDocument();

    const emptyUploadCta = screen.getByRole('link', { name: /Upload Document/i });
    expect(emptyUploadCta).toHaveAttribute('href', '/upload');
  });

  it('renders error alert with retry button on fetch failure', async () => {
    const fetchSpy = vi
      .spyOn(documentService, 'list')
      .mockRejectedValue(new Error('Failed to reach document service'));

    renderHistory();

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    expect(screen.getByText('Unable to load document history')).toBeInTheDocument();
    expect(screen.getByText('Failed to reach document service')).toBeInTheDocument();

    // Now mock resolved value for retry
    fetchSpy.mockResolvedValueOnce({
      count: 0,
      next: null,
      previous: null,
      results: [],
    });

    // Click retry
    const retryBtn = screen.getByRole('button', { name: /Retry/i });
    fireEvent.click(retryBtn);

    expect(fetchSpy).toHaveBeenCalledTimes(2);
  });
});
