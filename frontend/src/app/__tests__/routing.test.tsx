import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { routes } from '../router';
import { useAuthStore } from '../../store/authStore';
import { useAppStore } from '../../store';
import i18n from '../i18n';

describe('ClarifAI Typed Routing & App Shell (PRD Section 5, Ch. 9.1, 9.6, 22, 24)', () => {
  beforeEach(() => {
    useAuthStore.getState().clearAuth();
    useAppStore.getState().setLanguage('en');
    i18n.changeLanguage('en');
  });

  const renderRoute = (initialPath: string) => {
    const memoryRouter = createMemoryRouter(routes, {
      initialEntries: [initialPath],
    });
    return render(<RouterProvider router={memoryRouter} />);
  };

  it('renders LandingPage at public route "/" with brand identity', () => {
    renderRoute('/');
    expect(screen.getByRole('link', { name: /ClarifAI Home/i })).toBeInTheDocument();
    expect(screen.getByText(/Clear Legal Insights/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Get Started Free/i })).toBeInTheDocument();
  });

  it('redirects unauthenticated user from protected route "/dashboard" to "/login"', () => {
    renderRoute('/dashboard');
    expect(screen.getByRole('heading', { name: /Sign In/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/Email Address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
  });

  it('redirects unauthenticated user from protected route "/history" to "/login"', () => {
    renderRoute('/history');
    expect(screen.getByRole('heading', { name: /Sign In/i })).toBeInTheDocument();
  });

  const mockUser = {
    id: 'usr_counsel',
    email: 'counsel@clarifai.internal',
    fullName: 'Jane Counsel',
    preferredLanguage: 'en' as const,
    createdAt: '2026-09-12T00:00:00.000Z',
  };

  it('renders DashboardPage and persistent legal disclaimer when user is authenticated', () => {
    useAuthStore.getState().setAuth(mockUser, 'valid_token');

    renderRoute('/dashboard');
    expect(screen.getByText(/Welcome back, Jane Counsel/i)).toBeInTheDocument();
    // Verify persistent legal disclaimer per PRD Ch. 26.1
    expect(
      screen.getByRole('region', { name: /legal disclaimer/i })
    ).toBeInTheDocument();
  });

  it('renders HistoryPage when authenticated at "/history"', () => {
    useAuthStore.getState().setAuth(mockUser, 'valid_token');

    renderRoute('/history');
    expect(screen.getByRole('heading', { name: /Document History/i })).toBeInTheDocument();
    expect(screen.getByRole('table', { name: /Document History/i })).toBeInTheDocument();
  });

  it('renders UploadPage when authenticated at "/upload"', () => {
    useAuthStore.getState().setAuth(mockUser, 'valid_token');

    renderRoute('/upload');
    expect(screen.getByRole('heading', { name: /Upload Legal Document/i })).toBeInTheDocument();
  });

  it('renders ProcessingPage when authenticated at "/documents/:id/processing"', () => {
    useAuthStore.getState().setAuth(mockUser, 'valid_token');

    renderRoute('/documents/doc-sample-123/processing');
    expect(screen.getByText(/Analyzing Document/i)).toBeInTheDocument();
    expect(screen.getByText(/doc-sample-123/i)).toBeInTheDocument();
  });

  it('renders AnalysisResultsPage when authenticated at "/documents/:id"', () => {
    useAuthStore.getState().setAuth(mockUser, 'valid_token');

    renderRoute('/documents/doc-sample-123');
    expect(screen.getByText(/Master Services Agreement Analysis/i)).toBeInTheDocument();
    expect(screen.getByText(/Executive Plain-Language Summary/i)).toBeInTheDocument();
  });

  it('renders ClauseDetailPage when authenticated at "/documents/:id/clauses/:clauseId"', () => {
    useAuthStore.getState().setAuth(mockUser, 'valid_token');

    renderRoute('/documents/doc-sample-123/clauses/clause-101');
    expect(screen.getByText(/Original Contract Text/i)).toBeInTheDocument();
    expect(screen.getByText(/Plain-English Breakdown & Risk Driver/i)).toBeInTheDocument();
  });

  it('renders ChatbotPage when authenticated at "/documents/:id/chat"', () => {
    useAuthStore.getState().setAuth(mockUser, 'valid_token');

    renderRoute('/documents/doc-sample-123/chat');
    expect(screen.getByRole('heading', { name: /Document Assistant/i })).toBeInTheDocument();
    expect(screen.getByText(/Contract-Grounded Conversation/i)).toBeInTheDocument();
  });

  it('renders ComparisonSetupPage when authenticated at "/compare"', () => {
    useAuthStore.getState().setAuth(mockUser, 'valid_token');

    renderRoute('/compare');
    expect(screen.getByRole('heading', { name: /Compare Legal Documents/i })).toBeInTheDocument();
  });

  it('renders ComparisonResultsPage when authenticated at "/compare/:idA/:idB"', () => {
    useAuthStore.getState().setAuth(mockUser, 'valid_token');

    renderRoute('/compare/doc-1/doc-2');
    expect(screen.getByRole('heading', { name: /Comparison Results/i })).toBeInTheDocument();
    expect(screen.getByText(/doc-1 vs doc-2/i)).toBeInTheDocument();
  });

  it('renders SettingsPage when authenticated at "/settings"', () => {
    useAuthStore.getState().setAuth(mockUser, 'valid_token');

    renderRoute('/settings');
    expect(screen.getByRole('heading', { name: /User Settings/i })).toBeInTheDocument();
    expect(screen.getByText(/Security & Token Architecture/i)).toBeInTheDocument();
  });

  it('strictly enforces zero admin route per PRD 9.1: "/admin" renders 404 NotFoundPage', () => {
    useAuthStore.getState().setAuth(mockUser, 'valid_token');

    renderRoute('/admin');
    expect(screen.getByText('404')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Page Not Found/i })).toBeInTheDocument();
    expect(screen.queryByText(/Admin Dashboard/i)).not.toBeInTheDocument();
  });

  it('toggles language between English and Hindi using UILanguageSwitch', () => {
    renderRoute('/');
    const langBtn = screen.getByRole('button', { name: /switch ui to hindi/i });
    expect(langBtn).toBeInTheDocument();

    fireEvent.click(langBtn);
    expect(screen.getByRole('button', { name: /switch ui to english/i })).toBeInTheDocument();
  });
});
