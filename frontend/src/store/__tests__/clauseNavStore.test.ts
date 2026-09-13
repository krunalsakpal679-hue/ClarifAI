import { describe, it, expect, beforeEach } from 'vitest';
import { useClauseNavStore } from '../clauseNavStore';

describe('ClauseNavStore (Zustand State Management)', () => {
  beforeEach(() => {
    useClauseNavStore.getState().reset();
  });

  it('initializes with default empty state and currentIndex -1', () => {
    const state = useClauseNavStore.getState();
    expect(state.documentId).toBeNull();
    expect(state.clauseIds).toEqual([]);
    expect(state.currentIndex).toBe(-1);
    expect(state.getPrevClauseId()).toBeNull();
    expect(state.getNextClauseId()).toBeNull();
  });

  it('sets clause IDs and sets initial active index if provided', () => {
    const sampleIds = ['clause-1', 'clause-2', 'clause-3'];
    useClauseNavStore.getState().setClauseIds('doc-100', sampleIds, 'clause-2');

    const state = useClauseNavStore.getState();
    expect(state.documentId).toBe('doc-100');
    expect(state.clauseIds).toEqual(sampleIds);
    expect(state.currentIndex).toBe(1);
    expect(state.getPrevClauseId()).toBe('clause-1');
    expect(state.getNextClauseId()).toBe('clause-3');
  });

  it('updates currentIndex when setCurrentClauseId is called', () => {
    const sampleIds = ['clause-1', 'clause-2', 'clause-3'];
    useClauseNavStore.getState().setClauseIds('doc-100', sampleIds, 'clause-1');

    useClauseNavStore.getState().setCurrentClauseId('clause-3');
    expect(useClauseNavStore.getState().currentIndex).toBe(2);
    expect(useClauseNavStore.getState().getNextClauseId()).toBeNull();
    expect(useClauseNavStore.getState().getPrevClauseId()).toBe('clause-2');
  });

  it('correctly bounds prev and next navigation at list limits', () => {
    const sampleIds = ['clause-1', 'clause-2'];
    useClauseNavStore.getState().setClauseIds('doc-100', sampleIds, 'clause-1');

    // At first clause: previous is null, next is clause-2
    expect(useClauseNavStore.getState().currentIndex).toBe(0);
    expect(useClauseNavStore.getState().getPrevClauseId()).toBeNull();
    expect(useClauseNavStore.getState().getNextClauseId()).toBe('clause-2');

    // Move to last clause: previous is clause-1, next is null
    useClauseNavStore.getState().setCurrentClauseId('clause-2');
    expect(useClauseNavStore.getState().currentIndex).toBe(1);
    expect(useClauseNavStore.getState().getPrevClauseId()).toBe('clause-1');
    expect(useClauseNavStore.getState().getNextClauseId()).toBeNull();
  });

  it('resets state cleanly', () => {
    useClauseNavStore.getState().setClauseIds('doc-100', ['c1', 'c2'], 'c1');
    useClauseNavStore.getState().reset();

    const state = useClauseNavStore.getState();
    expect(state.documentId).toBeNull();
    expect(state.clauseIds).toEqual([]);
    expect(state.currentIndex).toBe(-1);
  });
});
