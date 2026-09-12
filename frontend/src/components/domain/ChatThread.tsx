import React, { useEffect, useRef } from 'react';
import { Bot, Shield } from 'lucide-react';
import { ChatMessageBubble } from './ChatMessageBubble';
import { SuggestedQuestionChips } from './SuggestedQuestionChips';
import { cn } from '../../utils/cn';
import type { ChatMessage } from '../../types/chat';

export interface ChatThreadProps {
  documentId: string;
  messages: ChatMessage[];
  isSending: boolean;
  onSelectQuestion: (question: string) => void;
  className?: string;
}

export const ChatThread: React.FC<ChatThreadProps> = ({
  documentId,
  messages,
  isSending,
  onSelectQuestion,
  className,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on message list updates or sending indicator
  useEffect(() => {
    if (typeof bottomRef.current?.scrollIntoView === 'function') {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isSending]);

  const isEmpty = messages.length === 0;

  return (
    <div
      aria-label="Conversation Thread"
      aria-live="polite"
      className={cn('flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 sm:space-y-5', className)}
      data-testid="chat-thread"
    >
      {/* Empty Conversation State */}
      {isEmpty && (
        <div className="py-8 px-2 max-w-xl mx-auto text-center space-y-6" data-testid="chat-empty-state">
          <div className="w-12 h-12 mx-auto rounded-full bg-primary-100 flex items-center justify-center text-primary-800 shadow-sm">
            <Bot className="w-6 h-6" aria-hidden="true" />
          </div>

          <div className="space-y-1.5">
            <h2 className="text-lg sm:text-xl font-serif font-bold text-primary-950">
              Contract-Grounded Q&amp;A
            </h2>
            <p className="text-xs sm:text-sm text-secondary-600 leading-relaxed">
              Ask specific legal questions about terms, liabilities, payments, or termination. All responses cite exact source clauses from this contract.
            </p>
          </div>

          <div className="p-3 bg-secondary-50 rounded-lg border border-secondary-200 text-xs text-secondary-600 flex items-center justify-center gap-2">
            <Shield className="w-4 h-4 text-secondary-500 shrink-0" aria-hidden="true" />
            <span>Strict Hallucination Defense: AI does not extrapolate beyond uploaded clauses.</span>
          </div>

          <div className="text-left pt-2">
            <SuggestedQuestionChips onSelectQuestion={onSelectQuestion} />
          </div>
        </div>
      )}

      {/* Message List */}
      {!isEmpty && (
        <div className="space-y-4 sm:space-y-5 flex flex-col">
          {messages.map((message) => (
            <ChatMessageBubble
              key={message.id}
              message={message}
              documentId={documentId}
            />
          ))}
        </div>
      )}

      {/* Typing Indicator while awaiting response */}
      {isSending && (
        <div
          className="flex items-start gap-3 max-w-[80%] self-start"
          data-testid="chat-typing-indicator"
          role="status"
          aria-label="Assistant is analyzing clauses and generating response"
        >
          <div className="w-8 h-8 rounded-full bg-accent-100 text-accent-800 flex items-center justify-center shrink-0 shadow-sm border border-accent-200">
            <Bot className="w-4 h-4 text-accent-700" aria-hidden="true" />
          </div>
          <div className="p-3.5 rounded-2xl rounded-tl-none bg-secondary-100 border border-secondary-200 flex items-center gap-1.5 shadow-sm">
            <span className="w-2 h-2 rounded-full bg-secondary-500 animate-bounce [animation-delay:-0.3s]" />
            <span className="w-2 h-2 rounded-full bg-secondary-500 animate-bounce [animation-delay:-0.15s]" />
            <span className="w-2 h-2 rounded-full bg-secondary-500 animate-bounce" />
            <span className="sr-only">Analyzing contract clauses...</span>
          </div>
        </div>
      )}

      <div ref={bottomRef} aria-hidden="true" />
    </div>
  );
};
