import { describe, it, expect, beforeEach } from 'vitest';
import { useDocumentStore } from '../documentStore';
import {
  __setMockDocuments,
  __resetMockDocuments,
  INITIAL_MOCK_DOCUMENTS,
} from '../../services/mocks/documents';

describe('DocumentStore (Zustand State Management)', () => {
  beforeEach(() => {
    useDocumentStore.getState().reset();
    __resetMockDocuments();
  });

  it('initializes with default empty state', () => {
    const state = useDocumentStore.getState();
    expect(state.documents).toEqual([]);
    expect(state.totalCount).toBe(0);
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('fetches documents and updates store state', async () => {
    await useDocumentStore.getState().fetchDocuments({ page: 1, page_size: 10 });

    const state = useDocumentStore.getState();
    expect(state.isLoading).toBe(false);
    expect(state.documents.length).toBe(INITIAL_MOCK_DOCUMENTS.length);
    expect(state.totalCount).toBe(INITIAL_MOCK_DOCUMENTS.length);
    expect(state.error).toBeNull();
  });

  it('handles empty document state correctly', async () => {
    __setMockDocuments([]);

    await useDocumentStore.getState().fetchDocuments();

    const state = useDocumentStore.getState();
    expect(state.isLoading).toBe(false);
    expect(state.documents).toEqual([]);
    expect(state.totalCount).toBe(0);
  });
});
