import { create } from 'zustand';
import { registerResetHandler } from './resetRegistry';

export interface ClauseNavState {
  documentId: string | null;
  clauseIds: string[];
  currentIndex: number;

  setClauseIds: (documentId: string, clauseIds: string[], initialClauseId?: string) => void;
  setCurrentClauseId: (clauseId: string) => void;
  getPrevClauseId: () => string | null;
  getNextClauseId: () => string | null;
  reset: () => void;
}

export const useClauseNavStore = create<ClauseNavState>((set, get) => ({
  documentId: null,
  clauseIds: [],
  currentIndex: -1,

  setClauseIds: (documentId: string, clauseIds: string[], initialClauseId?: string) => {
    let index = -1;
    if (initialClauseId) {
      index = clauseIds.indexOf(initialClauseId);
    }
    set({
      documentId,
      clauseIds,
      currentIndex: index,
    });
  },

  setCurrentClauseId: (clauseId: string) => {
    const { clauseIds } = get();
    const index = clauseIds.indexOf(clauseId);
    if (index !== -1) {
      set({ currentIndex: index });
    }
  },

  getPrevClauseId: () => {
    const { clauseIds, currentIndex } = get();
    if (currentIndex > 0 && currentIndex < clauseIds.length) {
      return clauseIds[currentIndex - 1];
    }
    return null;
  },

  getNextClauseId: () => {
    const { clauseIds, currentIndex } = get();
    if (currentIndex >= 0 && currentIndex < clauseIds.length - 1) {
      return clauseIds[currentIndex + 1];
    }
    return null;
  },

  reset: () => {
    set({
      documentId: null,
      clauseIds: [],
      currentIndex: -1,
    });
  },
}));

registerResetHandler(() => useClauseNavStore.getState().reset());
