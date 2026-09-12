import { create } from 'zustand';
import type { SupportedLanguage } from '../i18n';

export interface UiState {
  analysisLanguage: SupportedLanguage;
  setAnalysisLanguage: (lang: SupportedLanguage) => void;
}

export const useUiStore = create<UiState>((set) => ({
  analysisLanguage: 'en',
  setAnalysisLanguage: (analysisLanguage) => set({ analysisLanguage }),
}));

export const useUIStore = useUiStore;
export default useUiStore;
