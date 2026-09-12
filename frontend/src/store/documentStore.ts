import { create } from 'zustand';
import type {
  ClauseItem,
  DocumentItem,
  DocumentListParams,
  DocumentSummary,
} from '../types';
import { documentService } from '../services/api';

export interface DocumentState {
  documents: DocumentItem[];
  totalCount: number;
  isLoading: boolean;
  error: string | null;

  // Active document analysis state (PRD Ch. 16 & Section 8.3)
  activeDocument: DocumentItem | null;
  summary: DocumentSummary | null;
  clauses: ClauseItem[];
  summaryLoading: boolean;
  clausesLoading: boolean;
  summaryError: string | null;
  clausesError: string | null;

  fetchDocuments: (params?: DocumentListParams) => Promise<void>;
  deleteDocument: (id: string) => Promise<void>;
  setActiveDocument: (doc: DocumentItem | null) => void;
  fetchSummary: (id: string, lang?: string) => Promise<void>;
  fetchClauses: (id: string, lang?: string, severity?: string) => Promise<void>;
  resetActiveDocument: () => void;
  reset: () => void;
}

export const useDocumentStore = create<DocumentState>((set) => ({
  documents: [],
  totalCount: 0,
  isLoading: false,
  error: null,

  activeDocument: null,
  summary: null,
  clauses: [],
  summaryLoading: false,
  clausesLoading: false,
  summaryError: null,
  clausesError: null,

  fetchDocuments: async (params?: DocumentListParams) => {
    set({ isLoading: true, error: null });
    try {
      const response = await documentService.list(params);
      set({
        documents: response.results,
        totalCount: response.count,
        isLoading: false,
        error: null,
      });
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to fetch documents. Please try again.';
      set({
        isLoading: false,
        error: errorMessage,
      });
    }
  },

  deleteDocument: async (id: string) => {
    await documentService.delete(id);
    set((state) => ({
      documents: state.documents.filter((doc) => doc.id !== id),
      totalCount: Math.max(0, state.totalCount - 1),
    }));
  },

  setActiveDocument: (doc) => set({ activeDocument: doc }),

  fetchSummary: async (id: string, lang?: string) => {
    set({ summaryLoading: true, summaryError: null });
    try {
      const summary = await documentService.getSummary(id, lang);
      set({ summary, summaryLoading: false, summaryError: null });
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load document summary.';
      set({ summaryLoading: false, summaryError: errorMessage });
    }
  },

  fetchClauses: async (id: string, lang?: string, severity?: string) => {
    set({ clausesLoading: true, clausesError: null });
    try {
      const response = severity
        ? await documentService.getClauses(id, lang, severity)
        : await documentService.getClauses(id, lang);
      set({ clauses: response.results, clausesLoading: false, clausesError: null });
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load document clauses.';
      set({ clausesLoading: false, clausesError: errorMessage });
    }
  },

  resetActiveDocument: () => {
    set({
      activeDocument: null,
      summary: null,
      clauses: [],
      summaryLoading: false,
      clausesLoading: false,
      summaryError: null,
      clausesError: null,
    });
  },

  reset: () => {
    set({
      documents: [],
      totalCount: 0,
      isLoading: false,
      error: null,
      activeDocument: null,
      summary: null,
      clauses: [],
      summaryLoading: false,
      clausesLoading: false,
      summaryError: null,
      clausesError: null,
    });
  },
}));

export default useDocumentStore;
