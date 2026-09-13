import React from 'react';
import { Bot, User, AlertCircle, AlertTriangle, ShieldCheck } from 'lucide-react';
import { SourceClauseLink } from './SourceClauseLink';
import { cn } from '../../utils/cn';
import type { ChatMessage } from '../../types/chat';

export interface ChatMessageBubbleProps {
  message: ChatMessage;
  documentId: string;
  className?: string;
}

export const ChatMessageBubble: React.FC<ChatMessageBubbleProps> = ({
  message,
  documentId,
  className,
}) => {
  const isUser = message.role === 'user';
  const isSystemError = message.isError || message.role === 'system';
  const hasCitations = message.source_clause_ids && message.source_clause_ids.length > 0;

  // PRD Ch. 17.7 No-answer detection
  const isNoAnswer =
    !isUser &&
    !isSystemError &&
    (message.content.includes("couldn't find enough information") ||
      message.content.toLowerCase().includes('does not contain information'));

  // Formatted timestamp
  const timeFormatted = new Date(message.created_at).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });

  // 1. Error / System Bubble
  if (isSystemError) {
    return (
      <div
        className={cn('flex items-start gap-3 max-w-[90%] sm:max-w-[80%]', className)}
        data-testid="chat-message-error"
      >
        <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center shrink-0 text-red-600">
          <AlertCircle className="w-4 h-4" aria-hidden="true" />
        </div>
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-900 text-xs sm:text-sm space-y-1 shadow-sm">
          <p className="font-semibold text-xs uppercase tracking-wider text-red-700">Service Notice</p>
          <p className="leading-relaxed">{message.content}</p>
          <span className="text-[10px] text-red-400 block pt-1">{timeFormatted}</span>
        </div>
      </div>
    );
  }

  // 2. User Bubble
  if (isUser) {
    return (
      <div
        className={cn('flex items-start gap-2.5 max-w-[85%] sm:max-w-[75%] self-end flex-row-reverse', className)}
        data-testid="chat-message-user"
      >
        <div className="w-8 h-8 rounded-full bg-primary-900 text-white flex items-center justify-center shrink-0 shadow-sm">
          <User className="w-4 h-4" aria-hidden="true" />
        </div>
        <div className="flex flex-col items-end">
          <div className="p-3.5 sm:p-4 rounded-2xl rounded-tr-none bg-primary-900 text-white text-xs sm:text-sm shadow-sm">
            <p className="leading-relaxed whitespace-pre-wrap select-text">{message.content}</p>
          </div>
          <span className="text-[10px] text-secondary-400 mt-1 mr-1">{timeFormatted}</span>
        </div>
      </div>
    );
  }

  // 3. Assistant Controlled No-Answer State (PRD Ch. 17.7)
  if (isNoAnswer) {
    return (
      <div
        className={cn('flex items-start gap-3 max-w-[90%] sm:max-w-[80%] self-start', className)}
        data-testid="chat-message-no-answer"
      >
        <div className="w-8 h-8 rounded-full bg-amber-100 text-amber-800 flex items-center justify-center shrink-0 shadow-sm">
          <AlertTriangle className="w-4 h-4" aria-hidden="true" />
        </div>
        <div className="flex flex-col">
          <div className="p-4 rounded-2xl rounded-tl-none bg-amber-50/70 border border-amber-200 text-secondary-900 text-xs sm:text-sm shadow-sm space-y-2">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-800">
              <span className="inline-block w-2 h-2 rounded-full bg-amber-500" />
              <span>Insufficient Document Grounding</span>
            </div>
            <p className="leading-relaxed text-secondary-800 select-text">{message.content}</p>
            <p className="text-[11px] text-secondary-500 italic pt-1 border-t border-amber-100">
              ClarifAI only answers questions supported by clauses in this document to prevent hallucinated advice.
            </p>
          </div>
          <span className="text-[10px] text-secondary-400 mt-1 ml-1">{timeFormatted}</span>
        </div>
      </div>
    );
  }

  // 4. Standard Assistant Grounded Answer
  return (
    <div
      className={cn('flex items-start gap-3 max-w-[90%] sm:max-w-[85%] self-start', className)}
      data-testid="chat-message-grounded"
    >
      <div className="w-8 h-8 rounded-full bg-accent-100 text-accent-800 flex items-center justify-center shrink-0 shadow-sm border border-accent-200">
        <Bot className="w-4 h-4 text-accent-700" aria-hidden="true" />
      </div>
      <div className="flex flex-col flex-1">
        <div className="p-4 rounded-2xl rounded-tl-none bg-white border border-secondary-200 text-secondary-900 text-xs sm:text-sm shadow-sm space-y-3">
          {hasCitations && (
            <div className="flex items-center gap-1.5 text-[11px] font-semibold text-primary-800 pb-1 border-b border-secondary-100">
              <ShieldCheck className="w-3.5 h-3.5 text-accent-600" aria-hidden="true" />
              <span>Grounded Contract Answer</span>
            </div>
          )}

          <p className="leading-relaxed whitespace-pre-wrap select-text text-secondary-900">
            {message.content}
          </p>

          {/* Clickable Source Clause References */}
          {hasCitations && (
            <div className="pt-2 border-t border-secondary-100 space-y-1.5">
              <span className="text-[10px] uppercase tracking-wider font-semibold text-secondary-500 block">
                Referenced Source Clauses
              </span>
              <div className="flex flex-wrap gap-1.5">
                {message.source_clause_ids.map((clauseId) => (
                  <SourceClauseLink
                    key={clauseId}
                    documentId={documentId}
                    clauseId={clauseId}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
        <span className="text-[10px] text-secondary-400 mt-1 ml-1">{timeFormatted}</span>
      </div>
    </div>
  );
};
