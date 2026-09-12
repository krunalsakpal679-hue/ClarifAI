import React from 'react';
import { Check, AlertTriangle, RefreshCw, Circle } from 'lucide-react';
import { cn } from '../../utils/cn';
import {
  PROCESSING_STAGES,
  getStageIndex,
  isStagePassed,
  type ProcessingStageId,
} from '../../constants/processingStages';
import type { DocumentStatusType } from '../../types/documents';

export interface ProgressStepperProps {
  currentStatus: DocumentStatusType;
  failedStageId?: ProcessingStageId | null;
  className?: string;
}

export const ProgressStepper: React.FC<ProgressStepperProps> = ({
  currentStatus,
  failedStageId,
  className,
}) => {
  const currentIndex = getStageIndex(currentStatus);

  return (
    <div
      role="list"
      aria-label="Document Processing Pipeline Stages"
      className={cn('space-y-4 sm:space-y-6', className)}
      data-testid="progress-stepper"
    >
      {PROCESSING_STAGES.map((stage, index) => {
        const isCompleted =
          currentStatus === 'complete' ||
          (currentStatus !== 'failed' && isStagePassed(currentStatus, stage.id));

        const isCurrent = currentStatus === stage.id && currentStatus !== 'complete';

        // Stage is considered failed if pipeline failed at this specific stage,
        // or if failed without explicit stage ID and it was the active stage
        const isFailed =
          currentStatus === 'failed' &&
          (failedStageId === stage.id || (!failedStageId && index === currentIndex));

        const isUpcoming = !isCompleted && !isCurrent && !isFailed;
        const isLast = index === PROCESSING_STAGES.length - 1;

        let statusText = 'Upcoming';
        if (isCompleted) statusText = 'Completed';
        else if (isCurrent) statusText = 'In progress';
        else if (isFailed) statusText = 'Failed';

        return (
          <div
            key={stage.id}
            role="listitem"
            className="relative flex items-start gap-4 group"
            data-testid={`stepper-stage-${stage.id}`}
            aria-current={isCurrent ? 'step' : undefined}
          >
            {/* Connecting Vertical Trail Line */}
            {!isLast && (
              <div
                aria-hidden="true"
                className={cn(
                  'absolute left-4 top-8 -bottom-4 w-0.5 -ml-px transition-colors duration-200',
                  isCompleted ? 'bg-emerald-500' : 'bg-secondary-200'
                )}
              />
            )}

            {/* Stage Indicator Node */}
            <div className="relative z-10 shrink-0">
              {isCompleted && (
                <div
                  className="w-8 h-8 rounded-full bg-emerald-600 text-white flex items-center justify-center shadow-sm"
                  title="Completed"
                >
                  <Check className="w-4 h-4 stroke-[2.5]" aria-hidden="true" />
                  <span className="sr-only">({statusText})</span>
                </div>
              )}

              {isCurrent && (
                <div
                  className="w-8 h-8 rounded-full bg-primary-600 text-white flex items-center justify-center ring-4 ring-primary-100 shadow-md animate-pulse"
                  title="In Progress"
                >
                  <RefreshCw className="w-4 h-4 animate-spin" aria-hidden="true" />
                  <span className="sr-only">({statusText})</span>
                </div>
              )}

              {isFailed && (
                <div
                  className="w-8 h-8 rounded-full bg-red-600 text-white flex items-center justify-center ring-4 ring-red-100 shadow-sm"
                  title="Failed"
                >
                  <AlertTriangle className="w-4 h-4" aria-hidden="true" />
                  <span className="sr-only">({statusText})</span>
                </div>
              )}

              {isUpcoming && (
                <div
                  className="w-8 h-8 rounded-full bg-white border-2 border-secondary-300 text-secondary-500 flex items-center justify-center text-xs font-semibold"
                  title="Upcoming"
                >
                  <Circle className="w-2.5 h-2.5 fill-current text-secondary-300" aria-hidden="true" />
                  <span className="sr-only">({statusText})</span>
                </div>
              )}
            </div>

            {/* Stage Text & Details */}
            <div className="flex-1 min-w-0 pt-1 pb-2">
              <div className="flex flex-wrap items-center gap-2">
                <p
                  className={cn(
                    'text-sm font-semibold transition-colors',
                    isCurrent && 'text-primary-950 font-bold',
                    isCompleted && 'text-emerald-900',
                    isFailed && 'text-red-900 font-bold',
                    isUpcoming && 'text-secondary-500'
                  )}
                >
                  {stage.label}
                </p>

                {/* Conditional Indicator for OCR (PRD Ch. 15.1 UI Requirement) */}
                {stage.isConditional && (
                  <span
                    className={cn(
                      'text-[10px] font-medium px-2 py-0.5 rounded-full border',
                      isCurrent
                        ? 'bg-primary-100 border-primary-200 text-primary-800'
                        : isCompleted
                        ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                        : 'bg-secondary-100 border-secondary-200 text-secondary-600'
                    )}
                    data-testid="ocr-conditional-badge"
                  >
                    Conditional
                  </span>
                )}
              </div>

              <p
                className={cn(
                  'text-xs mt-0.5 leading-relaxed',
                  isCurrent ? 'text-primary-800 font-medium' : 'text-secondary-500'
                )}
              >
                {stage.description}
              </p>

              {stage.conditionalNote && (
                <p className="text-[11px] text-secondary-400 italic mt-0.5">
                  &bull; {stage.conditionalNote}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default ProgressStepper;
