/**
 * ClarifAI Section 8.4 Chat & Q&A API Contracts (PRD Ch. 17, 22.9, 30.4)
 */

export type MessageRole = 'user' | 'assistant' | 'system';

export interface ChatSession {
  id: string;
  document: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  source_clause_ids: string[];
  created_at: string;
  isError?: boolean;
}

export interface PaginatedChatMessageResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: ChatMessage[];
}

export interface IChatService {
  getOrCreateSession: (documentId: string) => Promise<ChatSession>;
  sendMessage: (documentId: string, message: string) => Promise<ChatMessage>;
  getHistory: (documentId: string) => Promise<ChatMessage[]>;
}
