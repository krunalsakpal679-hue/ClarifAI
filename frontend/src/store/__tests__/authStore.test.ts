import { describe, it, expect, beforeEach } from 'vitest';
import { useAuthStore } from '../authStore';

describe('useAuthStore (PRD Section 9.6 & Ch. 26.1)', () => {
  beforeEach(() => {
    // Reset store state before each test
    useAuthStore.getState().clearAuth();
    localStorage.clear();
    sessionStorage.clear();
  });

  it('initializes with unauthenticated state and null in-memory accessToken', () => {
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(state.accessToken).toBeNull();
  });

  it('strictly enforces no refreshToken in frontend state store per PRD 9.6 & 26.1', () => {
    const state = useAuthStore.getState() as unknown as Record<string, unknown>;
    expect(state['refreshToken']).toBeUndefined();
    expect(state['refresh_token']).toBeUndefined();
  });

  it('updates in-memory accessToken and user profile upon setAuth', () => {
    const mockUser = {
      id: 'usr_abc',
      email: 'counsel@clarifai.internal',
      fullName: 'Legal Counsel',
      preferredLanguage: 'en' as const,
      createdAt: '2026-09-12T00:00:00.000Z',
    };
    const mockToken = 'jwt_sample_access_token_123';

    useAuthStore.getState().setAuth(mockUser, mockToken);

    const updated = useAuthStore.getState();
    expect(updated.isAuthenticated).toBe(true);
    expect(updated.user).toEqual(mockUser);
    expect(updated.accessToken).toBe(mockToken);

    // Verify token was NOT written to localStorage or sessionStorage
    expect(localStorage.getItem('accessToken')).toBeNull();
    expect(localStorage.getItem('token')).toBeNull();
    expect(sessionStorage.getItem('accessToken')).toBeNull();
  });

  it('clears credentials on clearAuth and logout', () => {
    useAuthStore.getState().setAuth(
      {
        id: 'usr_xyz',
        email: 'test@clarifai.internal',
        fullName: 'Test User',
        preferredLanguage: 'en',
        createdAt: '2026-09-12T00:00:00.000Z',
      },
      'token_to_clear'
    );

    expect(useAuthStore.getState().isAuthenticated).toBe(true);

    useAuthStore.getState().logout();

    const loggedOut = useAuthStore.getState();
    expect(loggedOut.isAuthenticated).toBe(false);
    expect(loggedOut.user).toBeNull();
    expect(loggedOut.accessToken).toBeNull();
  });
});
