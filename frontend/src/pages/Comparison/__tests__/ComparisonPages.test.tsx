import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { routes } from '../../../app/router';
import { useAuthStore } from '../../../store/authStore';
import { useComparisonStore } from '../../../store/comparisonStore';
import { useDocumentStore } from '../../../store/documentStore';
import { __resetMockComparisons } from '../../../services/mocks/comparison';
import { __resetMockDocuments, __setMockDocumentStatus } from '../../../services/mocks/documents';

const mockUser = {
  id: 'usr_counsel',
  email: 'counsel@clarifai.internal',
  fullName: 'Jane Counsel',
  preferredLanguage: 'en' as const,
  createdAt: '2026-09-12T00:00:00.000Z',
};

describe('Comparison Pages (PRD Ch. 18, 22.10 & Section 8.5)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    __resetMockDocuments();
    __resetMockComparisons();
    useAuthStore.getState().setAuth(mockUser, 'valid_token');
    useDocumentStore.getState().reset();
    useComparisonStore.getState().reset();
  });

  const renderRoute = (initialPath: string) => {
    const memoryRouter = createMemoryRouter(routes, {
      initialEntries: [initialPath],
    });
    return render(<RouterProvider router={memoryRouter} />);
  };

  describe('ComparisonSetupPage (/compare)', () => {
    it('renders page header and populates document selectors with user contracts', async () => {
      renderRoute('/compare');

      expect(
        screen.getByRole('heading', { name: /Compare Legal Documents/i })
      ).toBeInTheDocument();

      await waitFor(() => {
        const select = screen.getByLabelText(/Select Base Contract/i) as HTMLSelectElement;
        expect(select.options.length).toBeGreaterThan(1);
      });

      const selectA = screen.getByLabelText(/Select Base Contract/i) as HTMLSelectElement;
      const selectB = screen.getByLabelText(/Select Comparison Target/i) as HTMLSelectElement;

      expect(selectA.options.length).toBeGreaterThan(1);
      expect(selectB.options.length).toBeGreaterThan(1);
    });

    it('disallows selecting the same document twice client-side and disables initiate button', async () => {
      renderRoute('/compare');

      await waitFor(() => {
        const select = screen.getByLabelText(/Select Base Contract/i) as HTMLSelectElement;
        expect(select.options.length).toBeGreaterThan(1);
      });

      const selectA = screen.getByLabelText(/Select Base Contract/i);
      const selectB = screen.getByLabelText(/Select Comparison Target/i);
      const submitBtn = screen.getByRole('button', { name: /Run Version Comparison/i });

      // Select same document on both sides
      fireEvent.change(selectA, { target: { value: 'doc-msa-001' } });
      fireEvent.change(selectB, { target: { value: 'doc-msa-001' } });

      await waitFor(() => {
        expect(screen.getByTestId('same-document-warning')).toBeInTheDocument();
      });

      expect(
        screen.getByText(/Cannot compare a document against itself/i)
      ).toBeInTheDocument();
      expect(submitBtn).toBeDisabled();
    });

    it('blocks comparison and shows explanation if selected document is not complete', async () => {
      __setMockDocumentStatus('doc-lease-005', 'extracting');

      renderRoute('/compare');

      await waitFor(() => {
        const select = screen.getByLabelText(/Select Base Contract/i) as HTMLSelectElement;
        expect(select.options.length).toBeGreaterThan(1);
      });

      const selectA = screen.getByLabelText(/Select Base Contract/i);
      const selectB = screen.getByLabelText(/Select Comparison Target/i);
      const submitBtn = screen.getByRole('button', { name: /Run Version Comparison/i });

      fireEvent.change(selectA, { target: { value: 'doc-msa-001' } });
      fireEvent.change(selectB, { target: { value: 'doc-lease-005' } });

      await waitFor(() => {
        expect(screen.getByTestId('incomplete-document-warning')).toBeInTheDocument();
      });

      expect(
        screen.getByText(/Both documents must be fully analyzed before pairwise comparison/i)
      ).toBeInTheDocument();
      expect(submitBtn).toBeDisabled();
    });

    it('initiates comparison on valid distinct documents and navigates to results', async () => {
      renderRoute('/compare');

      await waitFor(() => {
        const select = screen.getByLabelText(/Select Base Contract/i) as HTMLSelectElement;
        expect(select.options.length).toBeGreaterThan(1);
      });

      const selectA = screen.getByLabelText(/Select Base Contract/i);
      const selectB = screen.getByLabelText(/Select Comparison Target/i);
      const submitBtn = screen.getByRole('button', { name: /Run Version Comparison/i });

      fireEvent.change(selectA, { target: { value: 'doc-msa-001' } });
      fireEvent.change(selectB, { target: { value: 'doc-sla-002' } });

      expect(submitBtn).toBeEnabled();
      fireEvent.click(submitBtn);

      await waitFor(
        () => {
          expect(
            screen.getByRole('heading', { name: /Comparison Results/i })
          ).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });
  });

  describe('ComparisonResultsPage (/compare/:id or /compare/:idA/:idB)', () => {
    it('renders comparison results with all three groups (Changed, Matched, Missing)', async () => {
      renderRoute('/compare/comp-msa-sla');

      await waitFor(
        () => {
          expect(
            screen.getByRole('heading', { name: /^Changed Clauses/i })
          ).toBeInTheDocument();
        },
        { timeout: 10000 }
      );

      // Verify the three groups are rendered
      expect(screen.getByRole('heading', { name: /^Changed Clauses/i })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: /Matched \/ Unchanged Clauses/i })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: /Missing & Added Clauses/i })).toBeInTheDocument();

      // Check change summary presence
      expect(screen.getAllByText(/Change Summary:/i).length).toBeGreaterThan(0);
    });

    it('renders low-confidence indicator prominently when is_low_confidence is true (PRD Ch. 18.3)', async () => {
      renderRoute('/compare/comp-low-confidence');

      await waitFor(
        () => {
          expect(screen.getByTestId('comparison-confidence-indicator')).toBeInTheDocument();
        },
        { timeout: 10000 }
      );

      expect(
        screen.getByText(/Low Alignment Confidence Notice \(PRD Ch\. 18\.3\)/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/significantly different structure, clause count, and length/i)
      ).toBeInTheDocument();
    });

    it('toggles language to Hindi and displays translated explanations', async () => {
      renderRoute('/compare/comp-msa-sla');

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /^Changed Clauses/i })).toBeInTheDocument();
      });

      const langBtn = screen.getByRole('button', {
        name: /Switch analysis language to Hindi/i,
      });
      expect(langBtn).toBeInTheDocument();

      fireEvent.click(langBtn);

      await waitFor(
        () => {
          expect(screen.getAllByText(/\[हिंदी अनुवाद\]/i).length).toBeGreaterThan(0);
        },
        { timeout: 10000 }
      );
    });

    it('renders error view with retry button when comparison fails to load', async () => {
      renderRoute('/compare/comp-invalid-404-id');

      await waitFor(
        () => {
          expect(screen.getByTestId('comparison-error-view')).toBeInTheDocument();
        },
        { timeout: 10000 }
      );

      expect(screen.getByText(/Comparison Failed to Load/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Retry Comparison/i })).toBeInTheDocument();
    });
  });
});
