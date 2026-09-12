import React from 'react';
import { CheckCircle2, Clock, Loader2, XCircle } from 'lucide-react';
import { cn } from '../../utils/cn';
import type { DocumentStatusType } from '../../types';

export interface DocumentStatusBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  status: DocumentStatusType;
  className?: string;
}

export const DocumentStatusBadge: React.FC<DocumentStatusBadgeProps> = ({
  status,
  className,
  ...props
}) => {
  switch (status) {
    case 'complete':
      return (
        <span
          role="status"
          aria-label="Status: Complete"
          className={cn(
            'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border bg-emerald-50 text-emerald-800 border-emerald-200',
            className
          )}
          {...props}
        >
          <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-emerald-600" aria-hidden="true" />
          <span>Complete</span>
        </span>
      );

    case 'failed':
      return (
        <span
          role="status"
          aria-label="Status: Failed"
          className={cn(
            'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border bg-red-50 text-red-800 border-red-200',
            className
          )}
          {...props}
        >
          <XCircle className="w-3.5 h-3.5 shrink-0 text-red-600" aria-hidden="true" />
          <span>Failed</span>
        </span>
      );

    case 'queued':
      return (
        <span
          role="status"
          aria-label="Status: Queued"
          className={cn(
            'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border bg-secondary-100 text-secondary-800 border-secondary-300',
            className
          )}
          {...props}
        >
          <Clock className="w-3.5 h-3.5 shrink-0 text-secondary-600" aria-hidden="true" />
          <span>Queued</span>
        </span>
      );

    default:
      // In-progress statuses: extracting, ocr, segmenting, classifying, simplifying, summarizing, indexing
      return (
        <span
          role="status"
          aria-label="Status: Processing"
          className={cn(
            'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border bg-sky-50 text-sky-800 border-sky-200',
            className
          )}
          {...props}
        >
          <Loader2 className="w-3.5 h-3.5 shrink-0 text-sky-600 animate-spin" aria-hidden="true" />
          <span className="capitalize">{status || 'Processing'}</span>
        </span>
      );
  }
};
