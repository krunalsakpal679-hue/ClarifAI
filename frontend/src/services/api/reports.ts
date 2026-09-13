/**
 * Real Reports API Service (PRD Ch. 21, Ch. 30.6 & Section 8.6)
 *
 * Endpoints:
 * - POST /api/documents/{id}/report/?lang={lang} -> Generate document PDF report
 * - POST /api/comparisons/{id}/report/?lang={lang} -> Generate comparison PDF report
 * - GET  /api/reports/{id}/download/ -> Stream binary PDF file
 */
import { apiClient } from './client';
import type { IReportService, ReportDetail } from '../../types/reports';
import type { SupportedLanguage } from '../../i18n';

export const realReportService: IReportService = {
  generateDocumentReport: async (
    documentId: string,
    lang: SupportedLanguage = 'en'
  ): Promise<ReportDetail> => {
    const response = await apiClient.post<ReportDetail>(
      `/api/documents/${documentId}/report/`,
      { language: lang },
      { params: { lang } }
    );
    return response.data;
  },

  generateComparisonReport: async (
    comparisonId: string,
    lang: SupportedLanguage = 'en'
  ): Promise<ReportDetail> => {
    const response = await apiClient.post<ReportDetail>(
      `/api/comparisons/${comparisonId}/report/`,
      { language: lang },
      { params: { lang } }
    );
    return response.data;
  },

  downloadReport: async (reportId: string): Promise<Blob> => {
    const response = await apiClient.get<Blob>(`/api/reports/${reportId}/download/`, {
      responseType: 'blob',
    });
    return response.data;
  },
};
