import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import i18n from '../index';
import { useUiStore } from '../../store/uiStore';
import { useAppStore } from '../../store';
import { useAuthStore } from '../../store/authStore';
import { useComparisonStore } from '../../store/comparisonStore';
import { comparisonService } from '../../services/api';
import { AppShell } from '../../layouts/AppShell';
import { DashboardPage } from '../../pages/Dashboard';
import { HistoryPage } from '../../pages/History';
import { ComparisonResultsPage } from '../../pages/Comparison/Results';

const mockUser = {
  id: 'usr-1',
  email: 'counsel@clarifai.internal',
  fullName: 'Jane Counsel',
  preferredLanguage: 'en' as const,
  createdAt: '2026-09-12T00:00:00.000Z',
};

describe('Dual-Language Architecture & i18n Translation (PRD Section 9.5 & Ch. 21, 22.7)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuthStore.getState().setAuth(mockUser, 'mock_access_token');
    useUiStore.getState().setUiLanguage('en');
    useUiStore.getState().setAnalysisLanguage('en');
    useAppStore.getState().setLanguage('en');
    i18n.changeLanguage('en');
  });

  afterEach(() => {
    useUiStore.getState().setUiLanguage('en');
    useUiStore.getState().setAnalysisLanguage('en');
    i18n.changeLanguage('en');
  });

  it('changes visible UI chrome text across 3 different pages when UI language is toggled to Hindi', async () => {
    // Page 1: AppShell (Navigation Links)
    const { unmount: unmountShell } = render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AppShell />
      </MemoryRouter>
    );

    expect(screen.getByRole('link', { name: /Dashboard/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /History/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Compare/i })).toBeInTheDocument();

    // Switch UI to Hindi via i18n / uiStore
    useUiStore.getState().setUiLanguage('hi');

    await waitFor(() => {
      expect(screen.getByRole('link', { name: /डैशबोर्ड/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /इतिहास/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /तुलना करें/i })).toBeInTheDocument();
    });
    unmountShell();

    // Page 2: DashboardPage (Stat Cards & Section Headers)
    const { unmount: unmountDashboard } = render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/कुल दस्तावेज़/i)).toBeInTheDocument();
      expect(screen.getByText(/हाल के दस्तावेज़/i)).toBeInTheDocument();
    });
    unmountDashboard();

    // Page 3: HistoryPage (Table & Headers)
    render(
      <MemoryRouter>
        <HistoryPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /दस्तावेज़ इतिहास/i })).toBeInTheDocument();
      expect(screen.getByRole('table', { name: /दस्तावेज़ इतिहास/i })).toBeInTheDocument();
    });

    // Toggle back to English restores original chrome
    useUiStore.getState().setUiLanguage('en');
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Document History/i })).toBeInTheDocument();
      expect(screen.getByRole('table', { name: /Document History/i })).toBeInTheDocument();
    });
  });

  it('maintains uiStore.analysisLanguage as single source of truth across Comparison and Analysis', async () => {
    expect(useUiStore.getState().analysisLanguage).toBe('en');

    // Toggle analysis language in uiStore
    useUiStore.getState().setAnalysisLanguage('hi');
    expect(useUiStore.getState().analysisLanguage).toBe('hi');

    // UI language chrome must remain unchanged ('en')
    expect(useUiStore.getState().uiLanguage).toBe('en');
    expect(i18n.language).toBe('en');
  });

  it('re-fetches Comparison Results with selected lang param when analysis language is toggled', async () => {
    const fetchSpy = vi.spyOn(comparisonService, 'getResult');

    render(
      <MemoryRouter initialEntries={['/compare/comp-doc-1-doc-2']}>
        <Routes>
          <Route path="/compare/:comparisonId" element={<ComparisonResultsPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalledWith('comp-doc-1-doc-2', 'en');
    });

    // Toggle analysis language to Hindi via the LanguageToggle button
    const hindiToggleBtn = screen.getByRole('button', { name: /select hindi for ai analysis/i });
    fireEvent.click(hindiToggleBtn);

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalledWith('comp-doc-1-doc-2', 'hi');
      expect(useUiStore.getState().analysisLanguage).toBe('hi');
    });
  });

  it('shows an explicit notice and keeps English visible when translation is unavailable', async () => {
    // Set comparison with translation_available: false
    useComparisonStore.setState({
      comparison: {
        id: 'comp-untrans-1',
        base_document_id: 'doc-1',
        target_document_id: 'doc-2',
        status: 'complete',
        results: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        is_low_confidence: false,
        confidence_warning: null,
        translation_available: false,
      },
      isLoading: false,
      error: null,
    });

    render(
      <MemoryRouter initialEntries={['/compare/comp-untrans-1']}>
        <Routes>
          <Route path="/compare/:comparisonId" element={<ComparisonResultsPage />} />
        </Routes>
      </MemoryRouter>
    );

    // Explicit notice must be rendered without crashing or blocking the page
    expect(screen.getByTestId('translation-unavailable-notice')).toBeInTheDocument();
    expect(
      screen.getByText(/Translation temporarily unavailable\. Showing in English\./i)
    ).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Comparison Results/i })).toBeInTheDocument();
  });
});
