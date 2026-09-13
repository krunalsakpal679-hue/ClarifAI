/**
 * Real API Service for Section 8.4 Chat Endpoints (PRD Ch. 17, 30.4)
 */
import { apiClient } from './client';
import type {
  ChatMessage,
  ChatSession,
  IChatService,
  PaginatedChatMessageResponse,
} from '../../types/chat';

export const realChatService: IChatService = {
  getOrCreateSession: async (documentId: string): Promise<ChatSession> => {
    // GET /api/documents/{id}/chat/sessions/
    const response = await apiClient.get<ChatSession>(
      `/api/documents/${documentId}/chat/sessions/`
    );
    return response.data;
  },

  sendMessage: async (documentId: string, message: string): Promise<ChatMessage> => {
    // POST /api/documents/{id}/chat/messages/
    const response = await apiClient.post<ChatMessage>(
      `/api/documents/${documentId}/chat/messages/`,
      { message }
    );
    return response.data;
  },

  getHistory: async (documentId: string): Promise<ChatMessage[]> => {
    // GET /api/documents/{id}/chat/messages/
    const response = await apiClient.get<PaginatedChatMessageResponse | ChatMessage[]>(
      `/api/documents/${documentId}/chat/messages/`
    );

    if (Array.isArray(response.data)) {
      return response.data;
    }
    return response.data.results || [];
  },
};
