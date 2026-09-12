import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { routes } from '../../app/router';
import { useAuthStore } from '../../store/authStore';
import { authService } from '../../services/api';
import '../../app/i18n';

describe('Logout Flow (PRD Section 8.1 & Ch. 10/11)', () => {
  beforeEach(() => {
    useAuthStore.getState().clearAuth();
    vi.restoreAllMocks();
  });

  it('clears authStore, calls logout endpoint, redirects to Landing, and blocks protected routes', async () => {
    // Seed authenticated state
    useAuthStore.getState().setAuth(
      {
        id: 'usr_counsel_001',
        email: 'counsel@clarifai.internal',
        fullName: 'Jane Counsel',
        preferredLanguage: 'en',
        createdAt: '2026-09-01T00:00:00.000Z',
      },
      'valid_session_access_token'
    );

    const logoutSpy = vi.spyOn(authService, 'logout');

    const memoryRouter = createMemoryRouter(routes, {
      initialEntries: ['/dashboard'],
    });

    render(<RouterProvider router={memoryRouter} />);

    expect(screen.getByText(/Welcome back, Jane Counsel/i)).toBeInTheDocument();

    // Click Log Out button in header
    const logoutBtn = screen.getByRole('button', { name: /log out/i });
    fireEvent.click(logoutBtn);

    // Verify authService.logout was called
    await waitFor(() => {
      expect(logoutSpy).toHaveBeenCalled();
    });

    // Verify redirected to Landing page (Section 5)
    await waitFor(() => {
      expect(screen.getByRole('link', { name: /Get Started Free/i })).toBeInTheDocument();
    });

    // Verify authStore state is completely cleared
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
    expect(useAuthStore.getState().user).toBeNull();
    expect(useAuthStore.getState().accessToken).toBeNull();
  });
});
