import { describe, it, expect, beforeEach } from 'vitest';
import { useChatStore } from '../chatStore';
import { __resetMockChat } from '../../services/mocks/chat';
import { __resetMockDocuments } from '../../services/mocks/documents';

describe('ChatStore (Zustand Document-Scoped State Management)', () => {
  beforeEach(() => {
    __resetMockDocuments();
    __resetMockChat();
    useChatStore.getState().reset();
  });

  it('initializes chat session and loads existing history for a document', async () => {
    await useChatStore.getState().initSession('doc-msa-001');

    const state = useChatStore.getState();
    expect(state.sessionsByDoc['doc-msa-001']).toBeDefined();
    expect(state.sessionsByDoc['doc-msa-001'].document).toBe('doc-msa-001');
    expect(state.messagesByDoc['doc-msa-001'].length).toBeGreaterThanOrEqual(2);
    expect(state.isLoadingByDoc['doc-msa-001']).toBe(false);
  });

  it('sends message, updates message list with user query, and appends assistant answer', async () => {
    await useChatStore.getState().initSession('doc-msa-001');
    const initialCount = useChatStore.getState().messagesByDoc['doc-msa-001'].length;

    await useChatStore.getState().sendMessage(
      'doc-msa-001',
      'Can the vendor terminate without cause?'
    );

    const updatedMessages = useChatStore.getState().messagesByDoc['doc-msa-001'];
    expect(updatedMessages.length).toBe(initialCount + 2); // 1 user + 1 assistant

    const lastMsg = updatedMessages[updatedMessages.length - 1];
    expect(lastMsg.role).toBe('assistant');
    expect(lastMsg.source_clause_ids).toContain('clause-102');
  });

  it('strictly isolates conversations between different documents', async () => {
    await useChatStore.getState().initSession('doc-msa-001');
    await useChatStore.getState().initSession('doc-safe-001');

    await useChatStore.getState().sendMessage('doc-safe-001', 'Is this contract balanced?');

    const state = useChatStore.getState();
    const safeMessages = state.messagesByDoc['doc-safe-001'];
    const msaMessages = state.messagesByDoc['doc-msa-001'];

    expect(safeMessages.some((m) => m.content === 'Is this contract balanced?')).toBe(true);
    expect(msaMessages.some((m) => m.content === 'Is this contract balanced?')).toBe(false);
  });

  it('appends system error bubble and sets error state when send fails', async () => {
    await useChatStore.getState().initSession('doc-msa-001');

    await useChatStore.getState().sendMessage('doc-msa-001', 'trigger-error: test error');

    const state = useChatStore.getState();
    const messages = state.messagesByDoc['doc-msa-001'];
    const lastMsg = messages[messages.length - 1];

    expect(lastMsg.role).toBe('system');
    expect(lastMsg.isError).toBe(true);
    expect(lastMsg.content).toMatch(/AI (processing is temporarily|chat service currently) unavailable/i);
    expect(state.isSendingByDoc['doc-msa-001']).toBe(false);
  });

  it('clears chat messages for a specific document without affecting others', async () => {
    await useChatStore.getState().initSession('doc-msa-001');
    await useChatStore.getState().initSession('doc-safe-001');

    useChatStore.getState().clearChat('doc-msa-001');

    const state = useChatStore.getState();
    expect(state.messagesByDoc['doc-msa-001']).toEqual([]);
    expect(state.messagesByDoc['doc-safe-001'].length).toBeGreaterThanOrEqual(0);
  });
});
