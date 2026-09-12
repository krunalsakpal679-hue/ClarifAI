import { create } from 'zustand';
import type { User } from '../types';

/**
 * ClarifAI Authentication Store (PRD v2.3 Section 9.6 & Chapter 26.1)
 *
 * ARCHITECTURAL RULE:
 * - Access token is held strictly IN-MEMORY in this Zustand state.
 * - The refresh token is an httpOnly cookie managed entirely by the browser/server.
 * - The frontend NEVER reads, writes, stores, or handles the refresh token.
 * - Long-lived tokens are never written to localStorage or sessionStorage.
 */

export interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoggingOut: boolean;
  setAuth: (user: User, accessToken: string) => void;
  setAccessToken: (accessToken: string) => void;
  setIsLoggingOut: (isLoggingOut: boolean) => void;
  clearAuth: () => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  accessToken: null,
  isAuthenticated: false,
  isLoggingOut: false,

  setAuth: (user: User, accessToken: string) =>
    set({
      user,
      accessToken,
      isAuthenticated: true,
      isLoggingOut: false,
    }),

  setAccessToken: (accessToken: string) =>
    set({
      accessToken,
      isAuthenticated: true,
    }),

  setIsLoggingOut: (isLoggingOut: boolean) =>
    set({ isLoggingOut }),

  clearAuth: () =>
    set({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoggingOut: false,
    }),

  logout: () => {
    // In-memory state is cleared immediately with isLoggingOut flag to allow clean redirection to Landing
    set({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoggingOut: true,
    });
  },
}));

export default useAuthStore;
