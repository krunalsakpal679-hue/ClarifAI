import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AppShell } from '../layouts/AppShell';
import { AuthLayout } from '../layouts/AuthLayout';
import '../i18n';

describe('Responsive Behavior across 5 Breakpoints (PRD Ch. 24)', () => {
  describe('AppShell Navigation & Breakpoints', () => {
    it('renders desktop navigation links on larger screens and mobile hamburger button for <640px', () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <AppShell />
        </MemoryRouter>
      );

      // Skip to main content link for keyboard/screen reader
      const skipLink = screen.getByText(/skip to main content/i);
      expect(skipLink).toBeInTheDocument();
      expect(skipLink).toHaveAttribute('href', '#main-content');

      // Mobile menu hamburger button exists with proper accessibility attributes
      const mobileButton = screen.getByLabelText(/open main menu/i);
      expect(mobileButton).toBeInTheDocument();
      expect(mobileButton).toHaveAttribute('aria-expanded', 'false');
      expect(mobileButton).toHaveAttribute('aria-controls', 'mobile-navigation');

      // Click mobile hamburger menu to toggle open
      fireEvent.click(mobileButton);
      expect(mobileButton).toHaveAttribute('aria-expanded', 'true');
      expect(mobileButton).toHaveAttribute('aria-label', 'Close main menu');

      // Drawer is opened
      const mobileNav = screen.getByLabelText('Mobile Navigation');
      expect(mobileNav).toBeInTheDocument();

      // Click again to close
      fireEvent.click(mobileButton);
      expect(mobileButton).toHaveAttribute('aria-expanded', 'false');
      expect(screen.queryByLabelText('Mobile Navigation')).not.toBeInTheDocument();
    });

    it('enforces max-w-constrained (1440px) large-screen centered container constraint', () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <AppShell />
        </MemoryRouter>
      );

      const main = screen.getByRole('main');
      expect(main).toHaveClass('max-w-constrained');
      expect(main).toHaveClass('mx-auto');
    });
  });

  describe('AuthLayout Large Desktop (>1920px) Constraint', () => {
    it('enforces max-w-[1920px] centered container to prevent ultra-wide screen drift', () => {
      const { container } = render(
        <MemoryRouter initialEntries={['/login']}>
          <Routes>
            <Route element={<AuthLayout />}>
              <Route path="/login" element={<div>Login Form</div>} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      const innerWrapper = container.querySelector('.max-w-\\[1920px\\]');
      expect(innerWrapper).toBeInTheDocument();
      expect(innerWrapper).toHaveClass('mx-auto');
      expect(innerWrapper).toHaveClass('min-h-screen');
    });
  });
});
