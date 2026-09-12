import React from 'react';
import { AlertTriangle, Info } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface ComparisonConfidenceIndicatorProps {
  warning?: string | null;
  className?: string;
}

export const ComparisonConfidenceIndicator: React.FC<ComparisonConfidenceIndicatorProps> = ({
  warning,
  className,
}) => {
  const defaultWarning =
    'The two selected contracts have significantly different structural patterns, clause lengths, or legal types. Semantic alignment confidence is reduced (PRD Ch. 18.3). Differences should be reviewed with extra discretion.';

  return (
    <div
      role="alert"
      aria-live="polite"
      className={cn(
        'p-4 rounded-xl border border-amber-300 bg-amber-50/90 text-amber-950 shadow-sm space-y-2',
        className
      )}
      data-testid="comparison-confidence-indicator"
    >
      <div className="flex items-center gap-2 text-amber-900 font-semibold text-sm">
        <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" aria-hidden="true" />
        <span>Low Alignment Confidence Notice (PRD Ch. 18.3)</span>
      </div>

      <p className="text-xs sm:text-sm text-amber-900 leading-relaxed">
        {warning || defaultWarning}
      </p>

      <div className="flex items-center gap-1.5 pt-1 border-t border-amber-200/80 text-[11px] text-amber-800">
        <Info className="w-3.5 h-3.5 text-amber-700 shrink-0" aria-hidden="true" />
        <span>
          ClarifAI algorithms detected a clause ratio exceeding 2.0:1 between baseline and comparison target.
        </span>
      </div>
    </div>
  );
};
