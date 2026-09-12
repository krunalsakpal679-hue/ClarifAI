import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ClauseNavControls } from '../ClauseNavControls';
import { useClauseNavStore } from '../../../store/clauseNavStore';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('ClauseNavControls Component (components/domain/ClauseNavControls)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useClauseNavStore.getState().reset();
  });

  const renderComponent = (docId = 'doc-123') => {
    return render(
      <MemoryRouter>
        <ClauseNavControls documentId={docId} />
      </MemoryRouter>
    );
  };

  it('renders previous/next buttons and position status indicator', () => {
    useClauseNavStore.getState().setClauseIds('doc-123', ['c1', 'c2', 'c3'], 'c2');
    renderComponent('doc-123');

    expect(screen.getByRole('button', { name: /previous clause/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /next clause/i })).toBeInTheDocument();

    const statusEl = screen.getByRole('status');
    expect(statusEl).toBeInTheDocument();
    expect(statusEl).toHaveAttribute('aria-live', 'polite');
    expect(statusEl).toHaveTextContent(/Clause 2 of 3/i);
  });

  it('disables previous button on the first clause and enables next button', () => {
    useClauseNavStore.getState().setClauseIds('doc-123', ['c1', 'c2', 'c3'], 'c1');
    renderComponent('doc-123');

    const prevBtn = screen.getByRole('button', { name: /previous clause/i });
    const nextBtn = screen.getByRole('button', { name: /next clause/i });

    expect(prevBtn).toBeDisabled();
    expect(nextBtn).toBeEnabled();
    expect(screen.getByRole('status')).toHaveTextContent(/Clause 1 of 3/i);
  });

  it('disables next button on the last clause and enables previous button', () => {
    useClauseNavStore.getState().setClauseIds('doc-123', ['c1', 'c2', 'c3'], 'c3');
    renderComponent('doc-123');

    const prevBtn = screen.getByRole('button', { name: /previous clause/i });
    const nextBtn = screen.getByRole('button', { name: /next clause/i });

    expect(prevBtn).toBeEnabled();
    expect(nextBtn).toBeDisabled();
    expect(screen.getByRole('status')).toHaveTextContent(/Clause 3 of 3/i);
  });

  it('navigates to next clause on clicking next button', () => {
    useClauseNavStore.getState().setClauseIds('doc-123', ['c1', 'c2', 'c3'], 'c1');
    renderComponent('doc-123');

    const nextBtn = screen.getByRole('button', { name: /next clause/i });
    fireEvent.click(nextBtn);

    expect(mockNavigate).toHaveBeenCalledWith('/documents/doc-123/clauses/c2');
  });

  it('navigates to previous clause on clicking previous button', () => {
    useClauseNavStore.getState().setClauseIds('doc-123', ['c1', 'c2', 'c3'], 'c2');
    renderComponent('doc-123');

    const prevBtn = screen.getByRole('button', { name: /previous clause/i });
    fireEvent.click(prevBtn);

    expect(mockNavigate).toHaveBeenCalledWith('/documents/doc-123/clauses/c1');
  });
});
