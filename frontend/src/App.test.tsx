import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import App from './App';
import './app/i18n';

describe('ClarifAI Phase 01 Foundation App', () => {
  it('renders the ClarifAI header and Phase 01 design system title', () => {
    render(<App />);
    expect(screen.getByText('ClarifAI')).toBeInTheDocument();
    expect(screen.getByText(/Design System Foundation/i)).toBeInTheDocument();
  });

  it('renders the PRD 9.1 admin decision enforcement banner', () => {
    render(<App />);
    expect(
      screen.getByText(/PRD Chapter 9.1 Role Decision Enforcement/i)
    ).toBeInTheDocument();
  });

  it('renders design system primitives showcase', () => {
    render(<App />);
    expect(screen.getByText('Button Primitives')).toBeInTheDocument();
    expect(screen.getByText('Input Primitives')).toBeInTheDocument();
    expect(screen.getByText('Badges & Risk Indicators')).toBeInTheDocument();
  });

  it('toggles language between English and Hindi when language button is clicked', () => {
    render(<App />);
    const langButton = screen.getByRole('button', {
      name: /toggle ui language/i,
    });
    expect(langButton).toBeInTheDocument();

    // Click to switch to Hindi
    fireEvent.click(langButton);
    expect(screen.getByText(/डिज़ाइन सिस्टम फाउंडेशन/i)).toBeInTheDocument();

    // Click to switch back to English
    fireEvent.click(langButton);
    expect(screen.getByText(/Design System Foundation/i)).toBeInTheDocument();
  });
});
