import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App';
import './app/i18n';

describe('ClarifAI Root App (Phase 02)', () => {
  it('renders root App with RouterProvider and Landing page', () => {
    render(<App />);
    expect(screen.getByRole('link', { name: /ClarifAI Home/i })).toBeInTheDocument();
    expect(screen.getByText(/Clear Legal Insights/i)).toBeInTheDocument();
  });
});
