/**
 * Mock Reports Service for ClarifAI (PRD Section 11, Ch. 21 & Section 8.6)
 *
 * Implements the two-step generate-then-download report lifecycle:
 * 1. POST /api/documents/{id}/report/?lang={lang}
 * 2. POST /api/comparisons/{id}/report/?lang={lang}
 * 3. GET /api/reports/{id}/download/
 */
import type { IReportService, ReportDetail } from '../../types/reports';
import type { SupportedLanguage } from '../../i18n';

const mockReportsStore: Map<string, ReportDetail> = new Map();
let simulateFailureOnce = false;

// Pre-populate with standard sample reports
const initDefaultReports = () => {
  mockReportsStore.clear();
  const sampleDocReport: ReportDetail = {
    id: 'rep-doc-sample-123',
    report_id: 'rep-doc-sample-123',
    document: 'doc-sample-123',
    comparison: null,
    language: 'en',
    status: 'complete',
    file_reference: '/mock-storage/reports/clarifai_report_rep-doc-sample-123.pdf',
    failure_reason: null,
    created_at: new Date().toISOString(),
  };
  mockReportsStore.set(sampleDocReport.id, sampleDocReport);
};

initDefaultReports();

export const mockReportService: IReportService & {
  __resetMockReports: () => void;
  __simulateNextFailure: (flag?: boolean) => void;
  __getMockReports: () => ReportDetail[];
} = {
  generateDocumentReport: async (
    documentId: string,
    lang: SupportedLanguage = 'en'
  ): Promise<ReportDetail> => {
    // Artificial small latency to simulate pipeline compilation
    await new Promise((resolve) => setTimeout(resolve, 150));

    if (simulateFailureOnce || documentId.includes('fail')) {
      simulateFailureOnce = false;
      throw new Error('Failed to compile document report PDF. Generation pipeline encountered an error.');
    }

    const reportId = `rep-doc-${documentId}-${Date.now().toString().slice(-4)}`;
    const report: ReportDetail = {
      id: reportId,
      report_id: reportId,
      document: documentId,
      comparison: null,
      language: lang,
      status: 'complete',
      file_reference: `/mock-storage/reports/clarifai_report_${reportId}.pdf`,
      failure_reason: null,
      created_at: new Date().toISOString(),
    };

    mockReportsStore.set(reportId, report);
    return report;
  },

  generateComparisonReport: async (
    comparisonId: string,
    lang: SupportedLanguage = 'en'
  ): Promise<ReportDetail> => {
    await new Promise((resolve) => setTimeout(resolve, 150));

    if (simulateFailureOnce || comparisonId.includes('fail')) {
      simulateFailureOnce = false;
      throw new Error('Failed to compile comparison report PDF. Generation pipeline encountered an error.');
    }

    const reportId = `rep-comp-${comparisonId}-${Date.now().toString().slice(-4)}`;
    const report: ReportDetail = {
      id: reportId,
      report_id: reportId,
      document: null,
      comparison: comparisonId,
      language: lang,
      status: 'complete',
      file_reference: `/mock-storage/reports/clarifai_report_${reportId}.pdf`,
      failure_reason: null,
      created_at: new Date().toISOString(),
    };

    mockReportsStore.set(reportId, report);
    return report;
  },

  downloadReport: async (reportId: string): Promise<Blob> => {
    await new Promise((resolve) => setTimeout(resolve, 100));

    if (simulateFailureOnce || reportId.includes('fail-download')) {
      simulateFailureOnce = false;
      throw new Error('Report download failed: Binary stream interrupted or file not found.');
    }

    const report = mockReportsStore.get(reportId);
    const docOrComp = report?.document ? `Document: ${report.document}` : `Comparison: ${report?.comparison || 'N/A'}`;
    const langLabel = report?.language === 'hi' ? 'Hindi (हिंदी)' : 'English';

    // Construct a valid mock PDF binary blob
    const pdfContent = [
      '%PDF-1.4\n',
      '% ClarifAI Legal Analysis & Risk Report\n',
      `% Report ID: ${reportId}\n`,
      `% Target: ${docOrComp}\n`,
      `% Language: ${langLabel}\n`,
      `% Generated: ${report?.created_at || new Date().toISOString()}\n`,
      '%%EOF\n',
    ].join('');

    return new Blob([pdfContent], { type: 'application/pdf' });
  },

  __resetMockReports: () => {
    simulateFailureOnce = false;
    initDefaultReports();
  },

  __simulateNextFailure: (flag = true) => {
    simulateFailureOnce = flag;
  },

  __getMockReports: () => {
    return Array.from(mockReportsStore.values());
  },
};
