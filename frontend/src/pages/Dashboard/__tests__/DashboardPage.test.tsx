import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { DashboardPage } from '../index';
import { useAuthStore } from '../../../store/authStore';
import { useDocumentStore } from '../../../store/documentStore';
import { dashboardService } from '../../../services/api';
import {
  __setMockDashboardSummary,
  __resetMockDashboardSummary,
} from '../../../services/mocks/dashboard';
import {
  __setMockDocuments,
  __resetMockDocuments,
  INITIAL_MOCK_DOCUMENTS,
} from '../../../services/mocks/documents';
import '../../../app/i18n';

describe('DashboardPage (PRD Ch. 20, 22.4 & Section 8.7)', () => {
  beforeEach(() => {
    __resetMockDashboardSummary();
    __resetMockDocuments();
    useDocumentStore.getState().reset();

    // Set authenticated user context
    useAuthStore.getState().setAuth(
      {
        id: 'usr-counsel-01',
        email: 'counsel@clarifai.internal',
        fullName: 'Jane Counsel',
        preferredLanguage: 'en',
        createdAt: '2026-09-01T00:00:00.000Z',
      },
      'mock_access_token'
    );
  });

  const renderDashboard = () => {
    return render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );
  };

  it('renders personalized welcome header and quick action CTAs', async () => {
    renderDashboard();

    expect(screen.getByText(/Welcome back, Jane Counsel/i)).toBeInTheDocument();
    expect(
      screen.getByRole('link', { name: /Upload Document/i })
    ).toHaveAttribute('href', '/upload');
    expect(
      screen.getByRole('link', { name: /Compare Documents/i })
    ).toHaveAttribute('href', '/compare');
  });

  it('fetches and renders aggregate statistics from Section 8.7 summary endpoint', async () => {
    __setMockDashboardSummary({
      total_documents: 12,
      flagged_risk_count: 5,
      in_progress_count: 2,
      completed_count: 9,
      failed_count: 1,
    });

    renderDashboard();

    // Verify stats appear after loading
    await waitFor(() => {
      expect(screen.getByText('12')).toBeInTheDocument();
    });

    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('9')).toBeInTheDocument();

    // Verify section labels
    expect(screen.getByText(/Total Documents/i)).toBeInTheDocument();
    expect(screen.getByText(/Risk Flagged/i)).toBeInTheDocument();
    expect(screen.getByText(/^In Progress$/i)).toBeInTheDocument();
    expect(screen.getByText(/Completed/i)).toBeInTheDocument();
  });

  it('renders recent documents with risk-level indicators in a responsive grid', async () => {
    renderDashboard();

    // Wait for documents to load
    await waitFor(() => {
      expect(screen.getByText(INITIAL_MOCK_DOCUMENTS[0].original_filename)).toBeInTheDocument();
    });

    // Verify presence of recent documents
    expect(screen.getByText(INITIAL_MOCK_DOCUMENTS[1].original_filename)).toBeInTheDocument();

    // Verify risk-level indicators are shown per document (PRD Ch. 20)
    expect(screen.getAllByText(/Risk Assessment:/i).length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByRole('status', { name: /Risk Level:/i }).length).toBeGreaterThanOrEqual(2);

    // Verify link to full History page (PRD Ch. 20 distinct from History)
    const historyLink = screen.getByRole('link', { name: /View all history/i });
    expect(historyLink).toHaveAttribute('href', '/history');
  });

  it('renders clean empty state when user has zero documents', async () => {
    __setMockDocuments([]);
    __setMockDashboardSummary({
      total_documents: 0,
      in_progress_count: 0,
      flagged_risk_count: 0,
      completed_count: 0,
      failed_count: 0,
    });

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText(/No documents analyzed yet/i)).toBeInTheDocument();
    });

    expect(
      screen.getByText(/Upload your first contract, NDA, or service agreement/i)
    ).toBeInTheDocument();

    // Prominent Upload CTA inside empty state
    const emptyStateCta = screen.getByRole('link', {
      name: /Upload your first document/i,
    });
    expect(emptyStateCta).toHaveAttribute('href', '/upload');
  });

  it('renders error state with retry button when summary fetch fails', async () => {
    const errorSpy = vi.spyOn(dashboardService, 'getSummary').mockRejectedValueOnce(
      new Error('Network error loading summary')
    );

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    expect(screen.getByText(/Unable to load dashboard data/i)).toBeInTheDocument();
    expect(screen.getByText(/Network error loading summary/i)).toBeInTheDocument();

    // Click retry
    const retryBtn = screen.getByRole('button', { name: /Retry/i });
    fireEvent.click(retryBtn);

    expect(errorSpy).toHaveBeenCalledTimes(2);
  });
});
