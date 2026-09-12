import React from 'react';
import { Link } from 'react-router-dom';
import { FileText, MessageSquare, ArrowRight } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../ui/Card';
import { Button } from '../ui/Button';
import { DocumentStatusBadge } from './DocumentStatusBadge';
import { RiskLevelIndicator } from './RiskLevelIndicator';
import type { DocumentItem } from '../../types';

export interface DocumentHistoryCardProps {
  document: DocumentItem;
  className?: string;
}

export const DocumentHistoryCard: React.FC<DocumentHistoryCardProps> = ({
  document,
  className,
}) => {
  const isComplete = document.status === 'complete';
  const isFailed = document.status === 'failed';
  const isInProgress = !isComplete && !isFailed;

  // Destination route for main inspection action
  const analysisDestination = isInProgress
    ? `/documents/${document.id}/processing`
    : `/documents/${document.id}`;

  const formattedDate = new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(document.uploaded_at));

  return (
    <Card
      elevation="sm"
      className={`flex flex-col justify-between transition-all duration-micro hover:border-primary-300 hover:shadow-elevation-2 ${className || ''}`}
    >
      <CardHeader className="space-y-3 pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-start gap-2.5 min-w-0">
            <div className="p-2 rounded-lg bg-primary-50 text-primary-900 shrink-0 mt-0.5 border border-primary-100">
              <FileText className="w-5 h-5 text-primary-800" aria-hidden="true" />
            </div>
            <div className="min-w-0">
              <CardTitle
                className="text-sm sm:text-base font-semibold text-primary-950 truncate max-w-xs sm:max-w-sm"
                title={document.original_filename}
              >
                {document.original_filename}
              </CardTitle>
              <CardDescription className="text-xs text-secondary-500 mt-0.5">
                Uploaded {formattedDate}
              </CardDescription>
            </div>
          </div>

          <div className="shrink-0 flex items-center gap-1.5">
            <DocumentStatusBadge status={document.status} />
          </div>
        </div>

        {/* Risk Level Badge (PRD Ch. 20) */}
        <div className="flex items-center justify-between pt-1 border-t border-secondary-100">
          <span className="text-xs font-medium text-secondary-600">Risk Assessment:</span>
          <RiskLevelIndicator risk={document.overall_risk} size="sm" />
        </div>
      </CardHeader>

      <CardContent className="py-2">
        {isFailed && document.failure_reason && (
          <p className="text-xs text-red-600 bg-red-50 p-2 rounded border border-red-200">
            {document.failure_reason}
          </p>
        )}
        {isInProgress && (
          <p className="text-xs text-sky-700 bg-sky-50 p-2 rounded border border-sky-200">
            Legal analysis in progress. Clauses are being extracted and analyzed.
          </p>
        )}
        {isComplete && document.document_type && (
          <p className="text-xs text-secondary-600 line-clamp-1">
            Category: <span className="font-medium text-secondary-800">{document.document_type}</span>
          </p>
        )}
      </CardContent>

      <CardFooter className="pt-3 border-t border-secondary-100 flex items-center justify-between gap-2">
        <Link
          to={analysisDestination}
          className="flex-1"
          aria-label={`View analysis for ${document.original_filename}`}
        >
          <Button
            variant="outline"
            size="sm"
            className="w-full justify-center gap-1.5 text-xs text-primary-900 hover:bg-primary-50"
          >
            <span>View Analysis</span>
            <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
          </Button>
        </Link>

        {isComplete && (
          <Link
            to={`/documents/${document.id}/chat`}
            aria-label={`Chat with ${document.original_filename}`}
          >
            <Button
              variant="ghost"
              size="sm"
              className="gap-1.5 text-xs text-secondary-700 hover:text-primary-900"
            >
              <MessageSquare className="w-3.5 h-3.5" aria-hidden="true" />
              <span>Chat</span>
            </Button>
          </Link>
        )}
      </CardFooter>
    </Card>
  );
};
