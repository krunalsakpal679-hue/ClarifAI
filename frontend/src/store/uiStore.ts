import { create } from 'zustand';
import { changeLanguage, type SupportedLanguage } from '../i18n';

export interface UiState {
  uiLanguage: SupportedLanguage;
  setUiLanguage: (lang: SupportedLanguage) => void;
  analysisLanguage: SupportedLanguage;
  setAnalysisLanguage: (lang: SupportedLanguage) => void;
}

export const useUiStore = create<UiState>((set) => ({
  uiLanguage: 'en',
  setUiLanguage: (uiLanguage: SupportedLanguage) => {
    changeLanguage(uiLanguage);
    set({ uiLanguage });
  },
  analysisLanguage: 'en',
  setAnalysisLanguage: (analysisLanguage: SupportedLanguage) => set({ analysisLanguage }),
}));

export const useUIStore = useUiStore;
export default useUiStore;
