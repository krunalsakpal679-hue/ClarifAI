import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { SourceClauseLink } from '../SourceClauseLink';
import { SuggestedQuestionChips } from '../SuggestedQuestionChips';
import { ChatMessageBubble } from '../ChatMessageBubble';
import { ChatInput } from '../ChatInput';
import type { ChatMessage } from '../../../types/chat';

describe('Chat Domain Components (components/domain/)', () => {
  describe('SourceClauseLink', () => {
    it('renders clickable link to the clause detail page with accessible label', () => {
      render(
        <MemoryRouter>
          <SourceClauseLink documentId="doc-123" clauseId="clause-101" />
        </MemoryRouter>
      );

      const link = screen.getByRole('link', { name: /view referenced clause #101/i });
      expect(link).toBeInTheDocument();
      expect(link).toHaveAttribute('href', '/documents/doc-123/clauses/clause-101');
      expect(screen.getByText(/Clause #101/i)).toBeInTheDocument();
    });
  });

  describe('SuggestedQuestionChips', () => {
    it('renders suggested question chips and triggers onSelectQuestion on click', () => {
      const handleSelect = vi.fn();
      render(<SuggestedQuestionChips onSelectQuestion={handleSelect} />);

      expect(screen.getByText(/Suggested Questions/i)).toBeInTheDocument();
      const chip = screen.getByRole('button', {
        name: /What are the indemnification obligations in this contract/i,
      });
      expect(chip).toBeInTheDocument();

      fireEvent.click(chip);
      expect(handleSelect).toHaveBeenCalledWith(
        'What are the indemnification obligations in this contract?'
      );
    });
  });

  describe('ChatMessageBubble', () => {
    it('renders user message right-aligned with primary color styling', () => {
      const userMsg: ChatMessage = {
        id: 'msg-u1',
        role: 'user',
        content: 'Is this contract auto-renewing?',
        source_clause_ids: [],
        created_at: '2026-09-12T14:40:00.000Z',
      };

      render(
        <MemoryRouter>
          <ChatMessageBubble message={userMsg} documentId="doc-123" />
        </MemoryRouter>
      );

      expect(screen.getByTestId('chat-message-user')).toBeInTheDocument();
      expect(screen.getByText('Is this contract auto-renewing?')).toBeInTheDocument();
    });

    it('renders grounded assistant message with source clause reference links', () => {
      const assistantMsg: ChatMessage = {
        id: 'msg-a1',
        role: 'assistant',
        content: 'Yes, it auto-renews every 12 months.',
        source_clause_ids: ['clause-103'],
        created_at: '2026-09-12T14:40:05.000Z',
      };

      render(
        <MemoryRouter>
          <ChatMessageBubble message={assistantMsg} documentId="doc-123" />
        </MemoryRouter>
      );

      expect(screen.getByTestId('chat-message-grounded')).toBeInTheDocument();
      expect(screen.getByText('Yes, it auto-renews every 12 months.')).toBeInTheDocument();
      expect(screen.getByText(/Grounded Contract Answer/i)).toBeInTheDocument();
      expect(screen.getByTestId('source-clause-link-clause-103')).toBeInTheDocument();
    });

    it('renders distinct PRD Ch. 17.7 controlled no-answer state with warning badge', () => {
      const noAnswerMsg: ChatMessage = {
        id: 'msg-na1',
        role: 'assistant',
        content:
          "I couldn't find enough information in the uploaded document to answer this question reliably.",
        source_clause_ids: [],
        created_at: '2026-09-12T14:40:10.000Z',
      };

      render(
        <MemoryRouter>
          <ChatMessageBubble message={noAnswerMsg} documentId="doc-123" />
        </MemoryRouter>
      );

      expect(screen.getByTestId('chat-message-no-answer')).toBeInTheDocument();
      expect(screen.getByText(/Insufficient Document Grounding/i)).toBeInTheDocument();
      expect(
        screen.getByText(
          "I couldn't find enough information in the uploaded document to answer this question reliably."
        )
      ).toBeInTheDocument();
    });

    it('renders error bubble with Service Notice styling', () => {
      const errorMsg: ChatMessage = {
        id: 'msg-err',
        role: 'system',
        content: 'AI service timed out.',
        source_clause_ids: [],
        created_at: '2026-09-12T14:40:15.000Z',
        isError: true,
      };

      render(
        <MemoryRouter>
          <ChatMessageBubble message={errorMsg} documentId="doc-123" />
        </MemoryRouter>
      );

      expect(screen.getByTestId('chat-message-error')).toBeInTheDocument();
      expect(screen.getByText(/Service Notice/i)).toBeInTheDocument();
      expect(screen.getByText('AI service timed out.')).toBeInTheDocument();
    });
  });

  describe('ChatInput', () => {
    it('handles query typing and submits on form submission', () => {
      const handleSend = vi.fn();
      render(<ChatInput onSend={handleSend} />);

      const input = screen.getByRole('textbox', {
        name: /ask a question about this contract/i,
      });
      const submitBtn = screen.getByRole('button', { name: /send message/i });

      expect(submitBtn).toBeDisabled();

      fireEvent.change(input, { target: { value: 'What is the liability cap?' } });
      expect(submitBtn).toBeEnabled();

      fireEvent.click(submitBtn);
      expect(handleSend).toHaveBeenCalledWith('What is the liability cap?');
      expect(input).toHaveValue('');
    });

    it('submits on Enter key press without Shift', () => {
      const handleSend = vi.fn();
      render(<ChatInput onSend={handleSend} />);

      const input = screen.getByRole('textbox');
      fireEvent.change(input, { target: { value: 'Payment terms?' } });
      fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });

      expect(handleSend).toHaveBeenCalledWith('Payment terms?');
    });

    it('disables input and submit button when disabled prop is true', () => {
      const handleSend = vi.fn();
      render(<ChatInput onSend={handleSend} disabled={true} />);

      expect(screen.getByRole('textbox')).toBeDisabled();
      expect(screen.getByRole('button', { name: /send message/i })).toBeDisabled();
    });
  });
});
