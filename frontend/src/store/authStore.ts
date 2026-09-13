import { create } from 'zustand';
import type { User } from '../types';
import { resetAllDomainStores } from './resetRegistry';

export { resetAllDomainStores };

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

  clearAuth: () => {
    resetAllDomainStores();
    set({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoggingOut: false,
    });
  },

  logout: () => {
    // In-memory state and all domain stores are cleared immediately with isLoggingOut flag
    resetAllDomainStores();
    set({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoggingOut: true,
    });
  },
}));

export default useAuthStore;
