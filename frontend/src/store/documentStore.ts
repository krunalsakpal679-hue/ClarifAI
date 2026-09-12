import { create } from 'zustand';
import type { DocumentItem, DocumentListParams } from '../types';
import { documentService } from '../services/api';

export interface DocumentState {
  documents: DocumentItem[];
  totalCount: number;
  isLoading: boolean;
  error: string | null;

  fetchDocuments: (params?: DocumentListParams) => Promise<void>;
  deleteDocument: (id: string) => Promise<void>;
  reset: () => void;
}

export const useDocumentStore = create<DocumentState>((set) => ({
  documents: [],
  totalCount: 0,
  isLoading: false,
  error: null,

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

  reset: () => {
    set({
      documents: [],
      totalCount: 0,
      isLoading: false,
      error: null,
    });
  },
}));

export default useDocumentStore;
