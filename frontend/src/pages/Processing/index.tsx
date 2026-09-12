import React, { useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { AlertTriangle, RefreshCw, ArrowLeft, Plus } from 'lucide-react';
import { usePolling } from '../../hooks/usePolling';
import { documentService } from '../../services/api';
import { Button } from '../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../components/ui/Card';
import { ProgressStepper } from '../../components/ui/ProgressStepper';
import { toast } from '../../components/ui/Toast';
import { PROCESSING_STAGES, type ProcessingStageId } from '../../constants/processingStages';
import type { DocumentItem, DocumentStatusType } from '../../types/documents';

export const ProcessingPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const {
    data: document,
    error: pollingError,
    isLoading,
    restartPolling,
  } = usePolling<DocumentItem>({
    fn: () => {
      if (!id) throw new Error('Document ID is required');
      return documentService.getById(id);
    },
    intervalMs: 3000,
    enabled: Boolean(id),
    isTerminal: (doc) => doc.status === 'complete' || doc.status === 'failed',
  });

  const currentStatus: DocumentStatusType = document?.status || 'queued';
  const isComplete = currentStatus === 'complete';
  const isFailed = currentStatus === 'failed';

  // PRD Ch. 15.1 Hand-off: On 'complete', navigate to /documents/:id (never false complete)
  useEffect(() => {
    if (isComplete && id) {
      toast.success('Document analysis complete!');
      navigate(`/documents/${id}`);
    }
  }, [isComplete, id, navigate]);

  // Active stage definition for screen readers & UI announcements
  const activeStage = PROCESSING_STAGES.find((s) => s.id === currentStatus);

  return (
    <div className="max-w-2xl mx-auto space-y-6 py-6" data-testid="processing-page">
      {/* Accessible Live Region for Stage Change Announcements */}
      <div
        className="sr-only"
        role="status"
        aria-live="polite"
        aria-atomic="true"
        data-testid="processing-live-region"
      >
        {isFailed
          ? `Analysis failed: ${document?.failure_reason || 'Unknown error'}`
          : isComplete
          ? 'Analysis complete! Redirecting to results...'
          : `Processing pipeline stage: ${activeStage?.label || currentStatus}`}
      </div>

      {/* Page Header */}
      <div className="text-center space-y-2">
        <h1 className="text-2xl sm:text-3xl font-serif font-bold text-primary-950">
          Analyzing Document
        </h1>
        <p className="text-xs text-secondary-500 font-mono">
          Document ID: {id || 'doc-preview'}
        </p>
        {document?.original_filename && (
          <p className="text-sm font-medium text-primary-900 truncate max-w-md mx-auto">
            {document.original_filename}
          </p>
        )}
      </div>

      {/* Failure State Notice Card */}
      {isFailed && (
        <div
          role="alert"
          className="p-5 rounded-2xl bg-red-50 border border-red-200 text-red-900 space-y-3 shadow-sm animate-in fade-in duration-200"
          data-testid="processing-failed-banner"
        >
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" aria-hidden="true" />
            <div className="space-y-1 flex-1">
              <strong className="text-sm font-bold block text-red-950">
                Document Processing Failed
              </strong>
              <p className="text-xs text-red-800 leading-relaxed">
                {document?.failure_reason ||
                  'An unexpected error interrupted the automated analysis pipeline. Your uploaded file could not be parsed.'}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-red-200">
            <Button
              variant="outline"
              size="sm"
              onClick={restartPolling}
              className="bg-white text-red-900 border-red-300 hover:bg-red-100 gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" aria-hidden="true" />
              <span>Retry Analysis</span>
            </Button>

            <Link to="/upload">
              <Button variant="primary" size="sm" className="gap-1.5">
                <Plus className="w-3.5 h-3.5" aria-hidden="true" />
                <span>Upload New Document</span>
              </Button>
            </Link>
          </div>
        </div>
      )}

      {/* Transient Polling Network Error (if any) */}
      {pollingError && !isFailed && (
        <div
          role="alert"
          className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-center justify-between gap-3"
        >
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" aria-hidden="true" />
            <span>Connecting to pipeline server... retrying status update.</span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={restartPolling}
            className="text-xs p-1 text-amber-800 hover:bg-amber-100"
          >
            Retry now
          </Button>
        </div>
      )}

      {/* Main Multi-Stage Processing Stepper Card */}
      <Card elevation="sm" className="border-secondary-200">
        <CardHeader className="pb-4 border-b border-secondary-100">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base text-primary-950">Processing Legal Pipeline</CardTitle>
              <CardDescription className="text-xs text-secondary-500 mt-0.5">
                {isLoading
                  ? 'Initiating automated legal analysis pipeline...'
                  : isComplete
                  ? 'All nine pipeline stages completed successfully.'
                  : isFailed
                  ? 'Pipeline execution halted due to an unrecoverable processing error.'
                  : 'Automated 9-stage legal contract simplification and clause risk evaluation.'}
              </CardDescription>
            </div>

            {!isComplete && !isFailed && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-primary-50 text-primary-800 border border-primary-100">
                <RefreshCw className="w-3 h-3 animate-spin text-primary-600" aria-hidden="true" />
                <span>In Progress</span>
              </span>
            )}
          </div>
        </CardHeader>

        <CardContent className="p-6 sm:p-8">
          {/* Exact nine stages shown simultaneously with active animated state (PRD Ch. 15.1) */}
          <ProgressStepper
            currentStatus={currentStatus}
            failedStageId={isFailed ? (currentStatus as ProcessingStageId) : null}
          />
        </CardContent>

        <CardFooter className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-4 border-t border-secondary-100 bg-secondary-50/40">
          <Link to="/dashboard" className="w-full sm:w-auto">
            <Button variant="ghost" size="sm" className="w-full justify-center gap-1.5 text-xs text-secondary-600">
              <ArrowLeft className="w-3.5 h-3.5" aria-hidden="true" />
              <span>Return to Dashboard</span>
            </Button>
          </Link>

          <Link to="/history" className="w-full sm:w-auto">
            <Button variant="outline" size="sm" className="w-full justify-center text-xs">
              <span>View Document Archive</span>
            </Button>
          </Link>
        </CardFooter>
      </Card>
    </div>
  );
};

export default ProcessingPage;
