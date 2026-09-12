import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { routes } from '../../../app/router';
import { useAuthStore } from '../../../store/authStore';
import { __resetMockAuthDatabase } from '../../../services/mocks/auth';
import '../../../app/i18n';

describe('Auth Pages (PRD Section 8.1, Ch. 10/11, Ch. 22.2/22.3, Ch. 31)', () => {
  beforeEach(() => {
    useAuthStore.getState().clearAuth();
    __resetMockAuthDatabase();
  });

  const renderRoute = (initialPath: string) => {
    const memoryRouter = createMemoryRouter(routes, {
      initialEntries: [initialPath],
    });
    return render(<RouterProvider router={memoryRouter} />);
  };

  describe('SignupPage', () => {
    it('validates required fields and shows inline errors', async () => {
      renderRoute('/signup');

      const submitBtn = screen.getByRole('button', { name: /create account/i });
      fireEvent.click(submitBtn);

      expect(await screen.findByText(/Email address is required/i)).toBeInTheDocument();
      expect(screen.getByText(/Password is required/i)).toBeInTheDocument();
    });

    it('validates email format', async () => {
      renderRoute('/signup');

      const emailInput = screen.getByLabelText(/Work Email Address/i);
      const submitBtn = screen.getByRole('button', { name: /create account/i });

      fireEvent.change(emailInput, { target: { value: 'invalid-email-format' } });
      fireEvent.click(submitBtn);

      expect(await screen.findByText(/Please enter a valid email address/i)).toBeInTheDocument();
    });

    it('validates password complexity rules with strength meter feedback', async () => {
      renderRoute('/signup');

      const emailInput = screen.getByLabelText(/Work Email Address/i);
      const passwordInput = screen.getByLabelText(/^Password/i);
      const submitBtn = screen.getByRole('button', { name: /create account/i });

      fireEvent.change(emailInput, { target: { value: 'user@clarifai.internal' } });
      // Password lacks uppercase and special char
      fireEvent.change(passwordInput, { target: { value: 'simple123' } });
      fireEvent.click(submitBtn);

      expect(
        await screen.findByText(/Password does not meet the security policy requirements/i)
      ).toBeInTheDocument();
    });

    it('successfully signs up valid user, updates authStore, and navigates to Dashboard', async () => {
      renderRoute('/signup');

      const uniqueEmail = `legal_${Date.now()}@clarifai.internal`;
      const emailInput = screen.getByLabelText(/Work Email Address/i);
      const passwordInput = screen.getByLabelText(/^Password/i);
      const submitBtn = screen.getByRole('button', { name: /create account/i });

      fireEvent.change(emailInput, { target: { value: uniqueEmail } });
      fireEvent.change(passwordInput, { target: { value: 'StrongPass123!' } });
      fireEvent.click(submitBtn);

      // Verify redirection to dashboard
      await waitFor(() => {
        expect(screen.getByText(/Welcome back/i)).toBeInTheDocument();
      });

      // Verify in-memory state updated
      expect(useAuthStore.getState().isAuthenticated).toBe(true);
      expect(useAuthStore.getState().user?.email).toBe(uniqueEmail);
      expect(useAuthStore.getState().accessToken).toBeDefined();
    });

    it('rejects duplicate email signup with clear inline error per PRD Ch. 10', async () => {
      renderRoute('/signup');

      const emailInput = screen.getByLabelText(/Work Email Address/i);
      const passwordInput = screen.getByLabelText(/^Password/i);
      const submitBtn = screen.getByRole('button', { name: /create account/i });

      // existing@clarifai.internal is pre-seeded in mock DB
      fireEvent.change(emailInput, { target: { value: 'existing@clarifai.internal' } });
      fireEvent.change(passwordInput, { target: { value: 'ValidPass123!' } });
      fireEvent.click(submitBtn);

      const duplicateErrors = await screen.findAllByText(
        /A user with this email address already exists/i
      );
      expect(duplicateErrors[0]).toBeInTheDocument();

      // Ensure store remains unauthenticated
      expect(useAuthStore.getState().isAuthenticated).toBe(false);
    });
  });

  describe('LoginPage', () => {
    it('validates required fields', async () => {
      renderRoute('/login');

      const submitBtn = screen.getByRole('button', { name: /^Sign In$/i });
      fireEvent.click(submitBtn);

      expect(await screen.findByText(/Email address is required/i)).toBeInTheDocument();
      expect(screen.getByText(/Password is required/i)).toBeInTheDocument();
    });

    it('shows generic error on invalid credentials per PRD Ch. 31', async () => {
      renderRoute('/login');

      const emailInput = screen.getByLabelText(/Work Email Address/i);
      const passwordInput = screen.getByLabelText(/^Password/i);
      const submitBtn = screen.getByRole('button', { name: /^Sign In$/i });

      fireEvent.change(emailInput, { target: { value: 'counsel@clarifai.internal' } });
      fireEvent.change(passwordInput, { target: { value: 'WrongPass!' } });
      fireEvent.click(submitBtn);

      const loginErrors = await screen.findAllByText('Invalid email or password.');
      expect(loginErrors[0]).toBeInTheDocument();
      expect(useAuthStore.getState().isAuthenticated).toBe(false);
    });

    it('authenticates valid credentials, updates authStore, and navigates to Dashboard', async () => {
      renderRoute('/login');

      const emailInput = screen.getByLabelText(/Work Email Address/i);
      const passwordInput = screen.getByLabelText(/^Password/i);
      const submitBtn = screen.getByRole('button', { name: /^Sign In$/i });

      fireEvent.change(emailInput, { target: { value: 'counsel@clarifai.internal' } });
      fireEvent.change(passwordInput, { target: { value: 'Password123!' } });
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(screen.getByText(/Welcome back/i)).toBeInTheDocument();
      });

      expect(useAuthStore.getState().isAuthenticated).toBe(true);
      expect(useAuthStore.getState().user?.email).toBe('counsel@clarifai.internal');
      expect(useAuthStore.getState().accessToken).toBeDefined();
    });
  });
});
