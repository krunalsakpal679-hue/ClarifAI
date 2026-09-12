import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '../ui/Button';
import { useClauseNavStore } from '../../store/clauseNavStore';
import { cn } from '../../utils/cn';

export interface ClauseNavControlsProps {
  documentId: string;
  className?: string;
  variant?: 'compact' | 'expanded';
  onNavigate?: (clauseId: string) => void;
}

export const ClauseNavControls: React.FC<ClauseNavControlsProps> = ({
  documentId,
  className,
  variant = 'compact',
  onNavigate,
}) => {
  const navigate = useNavigate();
  const { clauseIds, currentIndex, getPrevClauseId, getNextClauseId } = useClauseNavStore();

  const totalCount = clauseIds.length;
  const prevClauseId = getPrevClauseId();
  const nextClauseId = getNextClauseId();

  const isPrevDisabled = currentIndex <= 0 || !prevClauseId;
  const isNextDisabled = currentIndex < 0 || currentIndex >= totalCount - 1 || !nextClauseId;

  const handlePrev = () => {
    if (prevClauseId) {
      onNavigate?.(prevClauseId);
      navigate(`/documents/${documentId}/clauses/${prevClauseId}`);
    }
  };

  const handleNext = () => {
    if (nextClauseId) {
      onNavigate?.(nextClauseId);
      navigate(`/documents/${documentId}/clauses/${nextClauseId}`);
    }
  };

  const currentDisplayNumber = currentIndex >= 0 ? currentIndex + 1 : '--';
  const totalDisplayNumber = totalCount > 0 ? totalCount : '--';

  return (
    <nav
      aria-label="Clause navigation"
      className={cn(
        'flex items-center justify-between gap-3 bg-white p-2.5 sm:p-3 rounded-lg border border-secondary-200 shadow-sm',
        className
      )}
    >
      {/* Previous Button */}
      <Button
        variant="outline"
        size={variant === 'compact' ? 'sm' : 'md'}
        onClick={handlePrev}
        disabled={isPrevDisabled}
        aria-label="Previous clause"
        className="gap-1 text-xs sm:text-sm font-medium"
      >
        <ChevronLeft className="w-4 h-4 shrink-0" aria-hidden="true" />
        <span className="hidden xs:inline">Previous</span>
      </Button>

      {/* Position Indicator with ARIA live region */}
      <div
        role="status"
        aria-live="polite"
        className="text-xs sm:text-sm font-medium text-secondary-700 select-none text-center px-2"
        data-testid="clause-nav-position"
      >
        <span className="font-semibold text-primary-950 font-mono">
          Clause {currentDisplayNumber}
        </span>{' '}
        <span className="text-secondary-400">of</span>{' '}
        <span className="font-mono text-secondary-600">{totalDisplayNumber}</span>
      </div>

      {/* Next Button */}
      <Button
        variant="outline"
        size={variant === 'compact' ? 'sm' : 'md'}
        onClick={handleNext}
        disabled={isNextDisabled}
        aria-label="Next clause"
        className="gap-1 text-xs sm:text-sm font-medium"
      >
        <span className="hidden xs:inline">Next</span>
        <ChevronRight className="w-4 h-4 shrink-0" aria-hidden="true" />
      </Button>
    </nav>
  );
};
