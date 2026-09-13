import { create } from 'zustand';
import type { ChatMessage, ChatSession } from '../types/chat';
import { chatService } from '../services/api';
import { registerResetHandler } from './resetRegistry';

export interface ChatState {
  sessionsByDoc: Record<string, ChatSession>;
  messagesByDoc: Record<string, ChatMessage[]>;
  isLoadingByDoc: Record<string, boolean>;
  isSendingByDoc: Record<string, boolean>;
  errorByDoc: Record<string, string | null>;

  initSession: (documentId: string) => Promise<void>;
  sendMessage: (documentId: string, messageText: string) => Promise<void>;
  clearChat: (documentId: string) => void;
  reset: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  sessionsByDoc: {},
  messagesByDoc: {},
  isLoadingByDoc: {},
  isSendingByDoc: {},
  errorByDoc: {},

  initSession: async (documentId: string) => {
    set((state) => ({
      isLoadingByDoc: { ...state.isLoadingByDoc, [documentId]: true },
      errorByDoc: { ...state.errorByDoc, [documentId]: null },
    }));

    try {
      const session = await chatService.getOrCreateSession(documentId);
      const history = await chatService.getHistory(documentId);

      set((state) => ({
        sessionsByDoc: { ...state.sessionsByDoc, [documentId]: session },
        messagesByDoc: { ...state.messagesByDoc, [documentId]: history },
        isLoadingByDoc: { ...state.isLoadingByDoc, [documentId]: false },
        errorByDoc: { ...state.errorByDoc, [documentId]: null },
      }));
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to initialize chat session';
      set((state) => ({
        isLoadingByDoc: { ...state.isLoadingByDoc, [documentId]: false },
        errorByDoc: { ...state.errorByDoc, [documentId]: msg },
      }));
      throw err;
    }
  },

  sendMessage: async (documentId: string, messageText: string) => {
    const trimmed = messageText.trim();
    if (!trimmed) return;

    // Optimistically add user message if not already added by mock service
    const tempUserMsg: ChatMessage = {
      id: `temp-usr-${Date.now()}`,
      role: 'user',
      content: trimmed,
      source_clause_ids: [],
      created_at: new Date().toISOString(),
    };

    const currentMessages = get().messagesByDoc[documentId] || [];

    set((state) => ({
      isSendingByDoc: { ...state.isSendingByDoc, [documentId]: true },
      errorByDoc: { ...state.errorByDoc, [documentId]: null },
      messagesByDoc: {
        ...state.messagesByDoc,
        [documentId]: [...currentMessages, tempUserMsg],
      },
    }));

    try {
      const assistantMessage = await chatService.sendMessage(documentId, trimmed);

      // Refresh or append the assistant response
      set((state) => {
        const msgs = state.messagesByDoc[documentId] || [];
        return {
          messagesByDoc: {
            ...state.messagesByDoc,
            [documentId]: [...msgs, assistantMessage],
          },
          isSendingByDoc: { ...state.isSendingByDoc, [documentId]: false },
          errorByDoc: { ...state.errorByDoc, [documentId]: null },
        };
      });
    } catch (err) {
      const errorMsg =
        err instanceof Error
          ? err.message
          : 'AI chat service currently unavailable. Your message was saved.';

      const errMessageBubble: ChatMessage = {
        id: `err-${Date.now()}`,
        role: 'system',
        content: errorMsg,
        source_clause_ids: [],
        created_at: new Date().toISOString(),
        isError: true,
      };

      set((state) => ({
        messagesByDoc: {
          ...state.messagesByDoc,
          [documentId]: [...(state.messagesByDoc[documentId] || []), errMessageBubble],
        },
        isSendingByDoc: { ...state.isSendingByDoc, [documentId]: false },
        errorByDoc: { ...state.errorByDoc, [documentId]: errorMsg },
      }));
    }
  },

  clearChat: (documentId: string) => {
    set((state) => ({
      messagesByDoc: { ...state.messagesByDoc, [documentId]: [] },
      errorByDoc: { ...state.errorByDoc, [documentId]: null },
    }));
  },

  reset: () => {
    set({
      sessionsByDoc: {},
      messagesByDoc: {},
      isLoadingByDoc: {},
      isSendingByDoc: {},
      errorByDoc: {},
    });
  },
}));

registerResetHandler(() => useChatStore.getState().reset());

export default useChatStore;
