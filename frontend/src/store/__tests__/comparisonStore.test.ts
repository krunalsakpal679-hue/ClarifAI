import { describe, it, expect, beforeEach } from 'vitest';
import { useComparisonStore } from '../comparisonStore';
import { __resetMockComparisons } from '../../services/mocks/comparison';
import { __resetMockDocuments, __setMockDocumentStatus } from '../../services/mocks/documents';

describe('ComparisonStore (Zustand Document Comparison State)', () => {
  beforeEach(() => {
    __resetMockDocuments();
    __resetMockComparisons();
    useComparisonStore.getState().reset();
  });

  it('sets selected Document A and Document B IDs', () => {
    const store = useComparisonStore.getState();
    expect(store.selectedDocAId).toBeNull();
    expect(store.selectedDocBId).toBeNull();

    store.setSelectedDocA('doc-msa-001');
    store.setSelectedDocB('doc-sla-002');

    const updated = useComparisonStore.getState();
    expect(updated.selectedDocAId).toBe('doc-msa-001');
    expect(updated.selectedDocBId).toBe('doc-sla-002');
  });

  it('creates comparison and populates comparison detail and low-confidence flags', async () => {
    const compId = await useComparisonStore
      .getState()
      .createComparison('doc-msa-001', 'doc-sla-002');

    expect(compId).toBe('comp-doc-msa-001-doc-sla-002');

    const state = useComparisonStore.getState();
    expect(state.comparisonId).toBe(compId);
    expect(state.comparison).toBeDefined();
    expect(state.comparison?.results.length).toBeGreaterThan(0);
    expect(state.isLowConfidence).toBe(false);
    expect(state.isCreating).toBe(false);
    expect(state.error).toBeNull();
  });

  it('captures low-confidence flag when creating comparison between divergent documents', async () => {
    __setMockDocumentStatus('doc-lease-005', 'complete');
    await useComparisonStore
      .getState()
      .createComparison('doc-msa-001', 'doc-lease-005');

    const state = useComparisonStore.getState();
    expect(state.isLowConfidence).toBe(true);
    expect(state.confidenceWarning).toBeTruthy();
  });

  it('records error message when createComparison fails', async () => {
    await expect(
      useComparisonStore.getState().createComparison('doc-msa-001', 'doc-msa-001')
    ).rejects.toThrow();

    const state = useComparisonStore.getState();
    expect(state.error).toMatch(/Cannot compare a document against itself/i);
    expect(state.isCreating).toBe(false);
  });

  it('fetches existing comparison by ID into state', async () => {
    await useComparisonStore.getState().fetchComparison('comp-msa-sla');

    const state = useComparisonStore.getState();
    expect(state.comparisonId).toBe('comp-msa-sla');
    expect(state.comparison?.status).toBe('complete');
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('resets comparison state when leaving the comparison flow', () => {
    useComparisonStore.getState().setSelectedDocA('doc-1');
    useComparisonStore.getState().setSelectedDocB('doc-2');

    expect(useComparisonStore.getState().selectedDocAId).toBe('doc-1');

    useComparisonStore.getState().reset();

    const resetState = useComparisonStore.getState();
    expect(resetState.selectedDocAId).toBeNull();
    expect(resetState.selectedDocBId).toBeNull();
    expect(resetState.comparison).toBeNull();
    expect(resetState.comparisonId).toBeNull();
    expect(resetState.isLowConfidence).toBe(false);
  });
});
