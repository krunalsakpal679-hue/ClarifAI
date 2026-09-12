import { describe, it, expect, beforeEach } from 'vitest';
import { chatService } from '../api';
import { __resetMockChat } from '../mocks/chat';
import { __resetMockDocuments, __setMockDocumentStatus } from '../mocks/documents';

describe('ChatService (Section 8.4 & PRD Ch. 17, 30.4)', () => {
  beforeEach(() => {
    __resetMockDocuments();
    __resetMockChat();
  });

  describe('getOrCreateSession', () => {
    it('creates or retrieves a chat session for a completed document', async () => {
      const session = await chatService.getOrCreateSession('doc-msa-001');

      expect(session).toBeDefined();
      expect(session.document).toBe('doc-msa-001');
      expect(session.id).toBeTruthy();
      expect(session.title).toContain('Master_Services_Agreement');
    });

    it('rejects with 422 DOCUMENT_NOT_READY when document is not complete', async () => {
      __setMockDocumentStatus('doc-lease-005', 'segmenting');

      await expect(chatService.getOrCreateSession('doc-lease-005')).rejects.toThrow(
        /DOCUMENT_NOT_READY/i
      );
    });

    it('rejects with 404 when document is not found', async () => {
      await expect(chatService.getOrCreateSession('non-existent-doc')).rejects.toThrow(
        /404/
      );
    });
  });

  describe('sendMessage', () => {
    it('returns grounded response with source_clause_ids for contractual questions', async () => {
      const response = await chatService.sendMessage(
        'doc-msa-001',
        'What are the indemnification liabilities?'
      );

      expect(response).toBeDefined();
      expect(response.role).toBe('assistant');
      expect(response.content).toContain('uncapped unilateral indemnification');
      expect(response.source_clause_ids).toContain('clause-101');
    });

    it('returns exact PRD Ch. 17.7 controlled no-answer copy when document lacks context', async () => {
      const response = await chatService.sendMessage(
        'doc-msa-001',
        'What is the employee severance payout formula?'
      );

      expect(response).toBeDefined();
      expect(response.role).toBe('assistant');
      expect(response.content).toBe(
        "I couldn't find enough information in the uploaded document to answer this question reliably."
      );
      expect(response.source_clause_ids).toEqual([]);
    });

    it('throws 503 error on simulated AI service failure but retains user message', async () => {
      await expect(
        chatService.sendMessage('doc-msa-001', 'trigger-error: test AI failure')
      ).rejects.toThrow(/AI chat service currently unavailable/i);

      // Verify user message was retained in history
      const history = await chatService.getHistory('doc-msa-001');
      expect(history.some((m) => m.content.includes('trigger-error'))).toBe(true);
    });

    it('rejects empty messages before sending', async () => {
      await expect(chatService.sendMessage('doc-msa-001', '   ')).rejects.toThrow(
        /cannot be empty/i
      );
    });
  });

  describe('getHistory', () => {
    it('returns message history in chronological order', async () => {
      const history = await chatService.getHistory('doc-msa-001');

      expect(history).toBeDefined();
      expect(history.length).toBeGreaterThanOrEqual(2);
      expect(history[0].role).toBe('user');
      expect(history[1].role).toBe('assistant');
    });
  });
});
