import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Download,
  FileCheck,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { Button } from '../ui/Button';
import { Spinner } from '../ui/Spinner';
import { Badge } from '../ui/Badge';
import { toast } from '../ui/Toast';
import { reportService } from '../../services/api';
import type { SupportedLanguage } from '../../i18n';
import type { ReportType } from '../../types/reports';
import { cn } from '../../utils/cn';

export type ReportFlowState = 'idle' | 'generating' | 'ready' | 'downloaded' | 'failed';

export interface ReportDownloadButtonProps {
  reportType: ReportType;
  targetId: string;
  lang?: SupportedLanguage;
  size?: 'sm' | 'md';
  variant?: 'primary' | 'outline' | 'ghost' | 'secondary';
  className?: string;
  onDownloadComplete?: (reportId: string) => void;
  onError?: (error: Error) => void;
}

/**
 * Two-Step Report Generate-Then-Download Domain Component (PRD Ch. 21, Ch. 30.6 & Section 8.6)
 *
 * Implements 4 discrete lifecycle states:
 * 1. idle: "Export Report" / "Generate Report"
 * 2. generating: Spinner with "Generating Report..."
 * 3. ready (preview): Inline confirmation "Report Ready (PDF)" with "Download PDF" action
 * 4. downloaded: Success state with checkmark + re-download option
 * 5. failed: Alert state with "Retry" action
 */
export const ReportDownloadButton: React.FC<ReportDownloadButtonProps> = ({
  reportType,
  targetId,
  lang = 'en',
  size = 'sm',
  variant = 'outline',
  className,
  onDownloadComplete,
  onError,
}) => {
  const { t } = useTranslation();
  const [flowState, setFlowState] = useState<ReportFlowState>('idle');
  const [reportId, setReportId] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Step 1: Generate Report (POST /api/documents/{id}/report/ or /api/comparisons/{id}/report/)
  const handleGenerate = async () => {
    if (!targetId) return;

    setFlowState('generating');
    setErrorMessage(null);

    try {
      const result =
        reportType === 'document'
          ? await reportService.generateDocumentReport(targetId, lang)
          : await reportService.generateComparisonReport(targetId, lang);

      const generatedId = result.id || result.report_id || `rep-${targetId}`;
      setReportId(generatedId);
      setFlowState('ready');
      toast.info(t('reports.readyConfirmation', 'Report compiled and ready for download!'));
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setErrorMessage(error.message);
      setFlowState('failed');
      onError?.(error);
      toast.error(t('reports.failedNotice', 'Report generation failed. Please try again.'));
    }
  };

  // Step 2: Download PDF (GET /api/reports/{id}/download/)
  const handleDownload = async () => {
    if (!reportId) return;

    setIsDownloading(true);
    try {
      const blob = await reportService.downloadReport(reportId);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `clarifai_${reportType}_report_${targetId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      setFlowState('downloaded');
      setIsDownloading(false);
      onDownloadComplete?.(reportId);
      toast.success(t('reports.successNotice', 'Report downloaded successfully!'));
    } catch (err) {
      setIsDownloading(false);
      const error = err instanceof Error ? err : new Error(String(err));
      setErrorMessage(error.message);
      setFlowState('failed');
      onError?.(error);
      toast.error(t('reports.failedNotice', 'Download failed. Please try again.'));
    }
  };

  // 1. GENERATING STATE
  if (flowState === 'generating') {
    return (
      <div className={cn('inline-flex items-center gap-2', className)} data-testid="report-state-generating">
        <Button
          variant={variant}
          size={size}
          disabled
          aria-busy="true"
          className="gap-2 cursor-wait opacity-90"
        >
          <Spinner size="sm" />
          <span>{t('reports.generating', 'Generating Report...')}</span>
        </Button>
      </div>
    );
  }

  // 2. READY / PREVIEW STATE
  if (flowState === 'ready') {
    return (
      <div
        className={cn('inline-flex items-center gap-2 p-1 rounded-lg bg-emerald-50 border border-emerald-200', className)}
        data-testid="report-state-ready"
      >
        <Badge variant="success" size="sm" className="hidden sm:inline-flex gap-1 py-0.5 px-2">
          <FileCheck className="w-3 h-3" />
          <span>{t('reports.ready', 'Report Ready (PDF)')}</span>
        </Badge>
        <Button
          variant="primary"
          size={size}
          onClick={handleDownload}
          disabled={isDownloading}
          className="gap-1.5 shadow-xs text-xs font-semibold bg-emerald-700 hover:bg-emerald-800"
          aria-label={t('reports.downloadPdf', 'Download PDF')}
        >
          {isDownloading ? (
            <Spinner size="sm" />
          ) : (
            <Download className="w-3.5 h-3.5" aria-hidden="true" />
          )}
          <span>{t('reports.downloadPdf', 'Download PDF')}</span>
        </Button>
      </div>
    );
  }

  // 3. DOWNLOADED STATE
  if (flowState === 'downloaded') {
    return (
      <div
        className={cn('inline-flex items-center gap-2', className)}
        data-testid="report-state-downloaded"
      >
        <Badge variant="success" size="sm" className="gap-1 py-1 px-2.5">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
          <span>{t('reports.downloaded', 'Downloaded')}</span>
        </Badge>
        <Button
          variant="ghost"
          size={size}
          onClick={handleDownload}
          className="gap-1 text-xs text-secondary-600 hover:text-primary-950 px-2"
          title={t('reports.reDownload', 'Download Again')}
          aria-label={t('reports.reDownload', 'Download Again')}
        >
          <Download className="w-3.5 h-3.5" aria-hidden="true" />
          <span className="hidden sm:inline">{t('reports.reDownload', 'Download Again')}</span>
        </Button>
      </div>
    );
  }

  // 4. FAILED STATE
  if (flowState === 'failed') {
    return (
      <div
        className={cn('inline-flex items-center gap-2 p-1 rounded-lg bg-red-50 border border-red-200', className)}
        data-testid="report-state-failed"
        role="alert"
      >
        <div className="flex items-center gap-1.5 px-2 text-xs text-red-700">
          <AlertTriangle className="w-3.5 h-3.5 text-red-600 shrink-0" aria-hidden="true" />
          <span className="hidden md:inline font-medium">
            {errorMessage ? 'Error' : t('reports.failed', 'Generation Failed')}
          </span>
        </div>
        <Button
          variant="outline"
          size={size}
          onClick={handleGenerate}
          className="gap-1 text-xs border-red-300 text-red-800 hover:bg-red-100"
          aria-label={t('reports.retry', 'Retry Report')}
        >
          <RotateCcw className="w-3 h-3" aria-hidden="true" />
          <span>{t('reports.retry', 'Retry Report')}</span>
        </Button>
      </div>
    );
  }

  // 5. IDLE STATE (Default)
  return (
    <Button
      variant={variant}
      size={size}
      onClick={handleGenerate}
      className={cn('gap-2 text-secondary-700 hover:text-primary-950', className)}
      title={t('reports.exportReport', 'Export Report')}
      aria-label={t('reports.exportReport', 'Export Report')}
      data-testid="report-state-idle"
    >
      <Download className="w-4 h-4 text-primary-800" aria-hidden="true" />
      <span>{t('reports.exportReport', 'Export Report')}</span>
    </Button>
  );
};

export default ReportDownloadButton;
