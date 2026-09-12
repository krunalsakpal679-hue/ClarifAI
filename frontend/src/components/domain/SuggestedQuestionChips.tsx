import React from 'react';
import { HelpCircle, Sparkles } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface SuggestedQuestionChipsProps {
  onSelectQuestion: (question: string) => void;
  className?: string;
}

const DEFAULT_SUGGESTED_QUESTIONS = [
  'What are the indemnification obligations in this contract?',
  'Can the vendor terminate this agreement without cause?',
  'What are the automatic renewal terms and notice deadlines?',
  'What are the invoice payment deadlines and late fees?',
];

export const SuggestedQuestionChips: React.FC<SuggestedQuestionChipsProps> = ({
  onSelectQuestion,
  className,
}) => {
  return (
    <div className={cn('space-y-3', className)} data-testid="suggested-question-chips">
      <div className="flex items-center gap-1.5 text-xs font-semibold text-secondary-600 uppercase tracking-wider">
        <Sparkles className="w-3.5 h-3.5 text-accent-600" aria-hidden="true" />
        <span>Suggested Questions</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {DEFAULT_SUGGESTED_QUESTIONS.map((question, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => onSelectQuestion(question)}
            className="flex items-start gap-2.5 p-3 rounded-lg border border-secondary-200 bg-white text-left text-xs sm:text-sm text-secondary-800 hover:border-primary-400 hover:bg-primary-50/40 hover:text-primary-950 transition-all shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-1 group"
          >
            <HelpCircle
              className="w-4 h-4 text-secondary-400 group-hover:text-primary-600 shrink-0 mt-0.5 transition-colors"
              aria-hidden="true"
            />
            <span className="leading-snug">{question}</span>
          </button>
        ))}
      </div>
    </div>
  );
};
