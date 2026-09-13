/**
 * Type definitions for ClarifAI Reports (PRD Ch. 21, Ch. 30.6 & Section 8.6)
 *
 * Covers:
 * - Document Analysis Report: POST /api/documents/{id}/report/?lang={lang}
 * - Comparison Report: POST /api/comparisons/{id}/report/?lang={lang}
 * - Streamed PDF Download: GET /api/reports/{id}/download/
 */
import type { SupportedLanguage } from '../i18n';

export type ReportType = 'document' | 'comparison';

export type ReportStatus = 'pending' | 'generating' | 'complete' | 'ready' | 'failed';

export interface ReportDetail {
  id: string;
  report_id?: string;
  document: string | null;
  comparison: string | null;
  language: SupportedLanguage;
  status: ReportStatus;
  file_reference?: string | null;
  failure_reason?: string | null;
  created_at: string;
}

export interface ReportCreateInput {
  language?: SupportedLanguage;
  lang?: SupportedLanguage;
}

export interface IReportService {
  generateDocumentReport: (documentId: string, lang?: SupportedLanguage) => Promise<ReportDetail>;
  generateComparisonReport: (comparisonId: string, lang?: SupportedLanguage) => Promise<ReportDetail>;
  downloadReport: (reportId: string) => Promise<Blob>;
}
