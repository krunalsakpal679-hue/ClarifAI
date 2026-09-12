/**
 * Mock Service for Section 8.4 Chat Endpoints (PRD Ch. 17, 30.4)
 */
import type { ChatMessage, ChatSession, IChatService } from '../../types/chat';
import { mockDocumentService } from './documents';

const delay = (ms: number) =>
  new Promise((resolve) => setTimeout(resolve, process.env.NODE_ENV === 'test' ? 10 : ms));

const PRD_NO_ANSWER_TEXT =
  "I couldn't find enough information in the uploaded document to answer this question reliably.";

let mockSessionsByDoc: Record<string, ChatSession> = {
  'doc-msa-001': {
    id: 'session-msa-001',
    document: 'doc-msa-001',
    title: 'Chat on Master_Services_Agreement_Enterprise_2026.pdf',
    created_at: '2026-09-12T14:40:00.000Z',
    updated_at: '2026-09-12T14:40:00.000Z',
  },
};

let mockMessagesByDoc: Record<string, ChatMessage[]> = {
  'doc-msa-001': [
    {
      id: 'msg-init-1',
      role: 'user',
      content: 'What are the payment terms in this agreement?',
      source_clause_ids: [],
      created_at: '2026-09-12T14:40:05.000Z',
    },
    {
      id: 'msg-init-2',
      role: 'assistant',
      content:
        'Invoices are due within fifteen (15) days of receipt. Unpaid balances incur 1.5% compounding monthly interest plus legal collection expenses.',
      source_clause_ids: ['clause-104'],
      created_at: '2026-09-12T14:40:08.000Z',
    },
  ],
};

export const mockChatService: IChatService = {
  getOrCreateSession: async (documentId: string): Promise<ChatSession> => {
    await delay(60);

    // Verify document status
    try {
      const doc = await mockDocumentService.getById(documentId);
      if (doc && doc.status !== 'complete') {
        throw new Error('DOCUMENT_NOT_READY: Document analysis is still in progress (422)');
      }
    } catch (err) {
      if (err instanceof Error && err.message.includes('DOCUMENT_NOT_READY')) {
        throw err;
      }
      if (!documentId.startsWith('doc-')) {
        throw new Error(`Document not found with ID ${documentId} (404)`);
      }
    }

    if (!mockSessionsByDoc[documentId]) {
      mockSessionsByDoc[documentId] = {
        id: `session-${documentId}-${Date.now().toString(36)}`,
        document: documentId,
        title: `Chat on Document ${documentId}`,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
    }

    return { ...mockSessionsByDoc[documentId] };
  },

  sendMessage: async (documentId: string, message: string): Promise<ChatMessage> => {
    await delay(120);

    if (!message || !message.trim()) {
      throw new Error('Message query content cannot be empty.');
    }

    // Verify document status
    try {
      const doc = await mockDocumentService.getById(documentId);
      if (doc && doc.status !== 'complete') {
        throw new Error('DOCUMENT_NOT_READY: Document analysis is still in progress (422)');
      }
    } catch (err) {
      if (err instanceof Error && err.message.includes('DOCUMENT_NOT_READY')) {
        throw err;
      }
      if (!documentId.startsWith('doc-')) {
        throw new Error(`Document not found with ID ${documentId} (404)`);
      }
    }

    // Initialize message array if absent
    if (!mockMessagesByDoc[documentId]) {
      mockMessagesByDoc[documentId] = [];
    }

    const trimmedQuery = message.trim();

    // 1. Persist User Message FIRST (matching PRD Ch. 30.4 user message retention guarantee)
    const userMsg: ChatMessage = {
      id: `msg-usr-${Date.now().toString(36)}-${Math.random().toString(36).substring(2, 6)}`,
      role: 'user',
      content: trimmedQuery,
      source_clause_ids: [],
      created_at: new Date().toISOString(),
    };
    mockMessagesByDoc[documentId].push(userMsg);

    // 2. Error simulation check
    const lowerQuery = trimmedQuery.toLowerCase();
    if (lowerQuery.includes('trigger-error') || lowerQuery.includes('simulate-error')) {
      throw new Error('AI chat service currently unavailable. Your message was saved.');
    }

    // 3. Grounded answer vs. PRD Ch. 17.7 controlled no-answer simulation
    let answerContent = '';
    let sourceClauseIds: string[] = [];

    if (lowerQuery.includes('indemn') || lowerQuery.includes('liability')) {
      answerContent =
        'Section 14.2 imposes uncapped unilateral indemnification on the customer for third-party claims, with zero monetary ceiling or reciprocal vendor coverage.';
      sourceClauseIds = ['clause-101'];
    } else if (lowerQuery.includes('terminat') || lowerQuery.includes('cancel')) {
      answerContent =
        'Section 18.1 grants the vendor the right to terminate immediately for any reason without refunding prepaid fees or providing migration transition assistance.';
      sourceClauseIds = ['clause-102'];
    } else if (lowerQuery.includes('renew') || lowerQuery.includes('annual')) {
      answerContent =
        'The contract automatically renews every 12 months unless cancelled 60 days in advance in writing. Prices may increase by up to 15% on each renewal.';
      sourceClauseIds = ['clause-103'];
    } else if (lowerQuery.includes('payment') || lowerQuery.includes('fee') || lowerQuery.includes('invoice')) {
      answerContent =
        'Invoices must be paid within 15 days of receipt. Late balances incur a 1.5% monthly compounding finance charge.';
      sourceClauseIds = ['clause-104'];
    } else {
      // PRD Ch. 17.7: Specific controlled no-answer wording when document lacks sufficient grounds
      answerContent = PRD_NO_ANSWER_TEXT;
      sourceClauseIds = [];
    }

    const assistantMsg: ChatMessage = {
      id: `msg-ast-${Date.now().toString(36)}-${Math.random().toString(36).substring(2, 6)}`,
      role: 'assistant',
      content: answerContent,
      source_clause_ids: sourceClauseIds,
      created_at: new Date().toISOString(),
    };

    mockMessagesByDoc[documentId].push(assistantMsg);
    return { ...assistantMsg };
  },

  getHistory: async (documentId: string): Promise<ChatMessage[]> => {
    await delay(70);

    const history = mockMessagesByDoc[documentId] || [];
    return history.map((msg) => ({ ...msg }));
  },
};

/**
 * Testing helpers
 */
export const __resetMockChat = (): void => {
  mockSessionsByDoc = {
    'doc-msa-001': {
      id: 'session-msa-001',
      document: 'doc-msa-001',
      title: 'Chat on Master_Services_Agreement_Enterprise_2026.pdf',
      created_at: '2026-09-12T14:40:00.000Z',
      updated_at: '2026-09-12T14:40:00.000Z',
    },
  };
  mockMessagesByDoc = {
    'doc-msa-001': [
      {
        id: 'msg-init-1',
        role: 'user',
        content: 'What are the payment terms in this agreement?',
        source_clause_ids: [],
        created_at: '2026-09-12T14:40:05.000Z',
      },
      {
        id: 'msg-init-2',
        role: 'assistant',
        content:
          'Invoices are due within fifteen (15) days of receipt. Unpaid balances incur 1.5% compounding monthly interest plus legal collection expenses.',
        source_clause_ids: ['clause-104'],
        created_at: '2026-09-12T14:40:08.000Z',
      },
    ],
  };
};

export const __setMockChatHistory = (documentId: string, messages: ChatMessage[]): void => {
  mockMessagesByDoc[documentId] = [...messages];
};
