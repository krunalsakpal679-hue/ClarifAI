import React, { useState, useRef, useEffect } from 'react';
import { SendHorizontal } from 'lucide-react';
import { Button } from '../ui/Button';
import { cn } from '../../utils/cn';

export interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
  initialValue?: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  disabled = false,
  placeholder = 'Ask any question about clauses in this contract...',
  className,
  initialValue = '',
}) => {
  const [text, setText] = useState(initialValue);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (initialValue) {
      setText(initialValue);
      inputRef.current?.focus();
    }
  }, [initialValue]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const query = (inputRef.current?.value || text).trim();
    if (!query || disabled) return;

    onSend(query);
    setText('');
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className={cn(
        'p-3 sm:p-4 bg-white border-t border-secondary-200 flex items-center gap-2.5 sm:gap-3',
        className
      )}
      data-testid="chat-input-form"
    >
      <div className="flex-1 relative">
        <label htmlFor="chat-query-input" className="sr-only">
          Ask a question about this contract
        </label>
        <input
          ref={inputRef}
          id="chat-query-input"
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder={placeholder}
          aria-label="Ask a question about this contract"
          className="w-full px-4 py-2.5 text-xs sm:text-sm text-secondary-900 placeholder:text-secondary-400 bg-secondary-50/70 border border-secondary-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:bg-white transition-all disabled:opacity-60 disabled:cursor-not-allowed"
        />
      </div>

      <Button
        type="submit"
        variant="primary"
        size="md"
        disabled={disabled || !text.trim()}
        aria-label="Send message"
        className="shrink-0 gap-1.5 px-4"
      >
        <span className="hidden sm:inline text-xs font-semibold">Send</span>
        <SendHorizontal className="w-4 h-4" aria-hidden="true" />
      </Button>
    </form>
  );
};
