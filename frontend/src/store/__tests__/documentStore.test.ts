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

  it('deletes document and decrements count', async () => {
    await useDocumentStore.getState().fetchDocuments();
    const beforeState = useDocumentStore.getState();
    const docToDelete = beforeState.documents[0];
    const initialCount = beforeState.totalCount;

    await useDocumentStore.getState().deleteDocument(docToDelete.id);

    const afterState = useDocumentStore.getState();
    expect(afterState.totalCount).toBe(initialCount - 1);
    expect(afterState.documents.find((d) => d.id === docToDelete.id)).toBeUndefined();
  });

  it('propagates error and leaves state unchanged when delete fails', async () => {
    await useDocumentStore.getState().fetchDocuments();
    const beforeState = useDocumentStore.getState();
    const initialDocs = [...beforeState.documents];
    const initialCount = beforeState.totalCount;

    await expect(
      useDocumentStore.getState().deleteDocument('invalid-doc-id')
    ).rejects.toThrow();

    const afterState = useDocumentStore.getState();
    expect(afterState.totalCount).toBe(initialCount);
    expect(afterState.documents.length).toBe(initialDocs.length);
  });
});

