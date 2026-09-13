import { create } from 'zustand';
import { changeLanguage, type SupportedLanguage } from '../i18n';
import { useUiStore } from './uiStore';

interface AppState {
  language: SupportedLanguage;
  setLanguage: (lang: SupportedLanguage) => void;
  isSidebarOpen: boolean;
  toggleSidebar: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  language: 'en',
  setLanguage: (language) => {
    changeLanguage(language);
    set({ language });
    useUiStore.setState({ uiLanguage: language });
  },
  isSidebarOpen: false,
  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
}));

export * from './authStore';
export * from './documentStore';
export * from './uiStore';
export * from './clauseNavStore';
export * from './chatStore';
export * from './comparisonStore';
