/**
 * Zustand Store for Two-Document Comparison (PRD Ch. 18 & Section 8.5)
 */
import { create } from 'zustand';
import type { ComparisonDetail } from '../types/comparison';
import { comparisonService } from '../services/api';
import { registerResetHandler } from './resetRegistry';

export interface ComparisonState {
  selectedDocAId: string | null;
  selectedDocBId: string | null;
  comparisonId: string | null;
  comparison: ComparisonDetail | null;
  isLowConfidence: boolean;
  confidenceWarning: string | null;
  isLoading: boolean;
  isCreating: boolean;
  error: string | null;

  setSelectedDocA: (id: string | null) => void;
  setSelectedDocB: (id: string | null) => void;
  createComparison: (docA: string, docB: string) => Promise<string>;
  fetchComparison: (comparisonId: string, lang?: string) => Promise<void>;
  reset: () => void;
}

export const useComparisonStore = create<ComparisonState>((set) => ({
  selectedDocAId: null,
  selectedDocBId: null,
  comparisonId: null,
  comparison: null,
  isLowConfidence: false,
  confidenceWarning: null,
  isLoading: false,
  isCreating: false,
  error: null,

  setSelectedDocA: (id: string | null) => set({ selectedDocAId: id, error: null }),
  setSelectedDocB: (id: string | null) => set({ selectedDocBId: id, error: null }),

  createComparison: async (docA: string, docB: string): Promise<string> => {
    set({ isCreating: true, error: null });
    try {
      const result = await comparisonService.create(docA, docB);
      set({
        comparison: result,
        comparisonId: result.id,
        selectedDocAId: result.base_document_id,
        selectedDocBId: result.target_document_id,
        isLowConfidence: Boolean(result.is_low_confidence),
        confidenceWarning: result.confidence_warning || null,
        isCreating: false,
        error: null,
      });
      return result.id;
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to create comparison.';
      set({ isCreating: false, error: msg });
      throw err;
    }
  },

  fetchComparison: async (comparisonId: string, lang = 'en'): Promise<void> => {
    set({ isLoading: true, error: null });
    try {
      const result = await comparisonService.getResult(comparisonId, lang);
      set({
        comparison: result,
        comparisonId: result.id,
        selectedDocAId: result.base_document_id,
        selectedDocBId: result.target_document_id,
        isLowConfidence: Boolean(result.is_low_confidence),
        confidenceWarning: result.confidence_warning || null,
        isLoading: false,
        error: null,
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to retrieve comparison.';
      set({ isLoading: false, error: msg, comparison: null });
    }
  },

  reset: () =>
    set({
      selectedDocAId: null,
      selectedDocBId: null,
      comparisonId: null,
      comparison: null,
      isLowConfidence: false,
      confidenceWarning: null,
      isLoading: false,
      isCreating: false,
      error: null,
    }),
}));

registerResetHandler(() => useComparisonStore.getState().reset());
