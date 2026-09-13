import { describe, it, expect, beforeEach, vi } from 'vitest';
import { realReportService } from '../api/reports';
import { mockReportService } from '../mocks/reports';
import { apiClient } from '../api/client';

describe('Report Services (PRD Ch. 21, Ch. 30.6 & Section 8.6)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockReportService.__resetMockReports();
  });

  describe('Mock Report Service', () => {
    it('generates document report returning 201-like shape with reportId and complete status', async () => {
      const report = await mockReportService.generateDocumentReport('doc-sample-123', 'en');

      expect(report.id).toMatch(/^rep-doc-doc-sample-123/);
      expect(report.document).toBe('doc-sample-123');
      expect(report.comparison).toBeNull();
      expect(report.language).toBe('en');
      expect(report.status).toBe('complete');
      expect(report.file_reference).toContain('.pdf');
    });

    it('generates comparison report returning 201-like shape with reportId and complete status', async () => {
      const report = await mockReportService.generateComparisonReport('comp-1-2', 'hi');

      expect(report.id).toMatch(/^rep-comp-comp-1-2/);
      expect(report.comparison).toBe('comp-1-2');
      expect(report.document).toBeNull();
      expect(report.language).toBe('hi');
      expect(report.status).toBe('complete');
    });

    it('downloads report returning a valid PDF binary Blob', async () => {
      const report = await mockReportService.generateDocumentReport('doc-sample-123', 'en');
      const blob = await mockReportService.downloadReport(report.id);

      expect(blob).toBeInstanceOf(Blob);
      expect(blob.type).toBe('application/pdf');
      expect(blob.size).toBeGreaterThan(0);
    });

    it('simulates generation failure when failure flag is set', async () => {
      mockReportService.__simulateNextFailure(true);

      await expect(
        mockReportService.generateDocumentReport('doc-sample-123', 'en')
      ).rejects.toThrow(/Failed to compile document report PDF/i);
    });

    it('simulates download failure when failure flag is set', async () => {
      const report = await mockReportService.generateDocumentReport('doc-sample-123', 'en');
      mockReportService.__simulateNextFailure(true);

      await expect(mockReportService.downloadReport(report.id)).rejects.toThrow(
        /Report download failed/i
      );
    });
  });

  describe('Real Report Service (API Client)', () => {
    it('calls POST /api/documents/{id}/report/ for document reports', async () => {
      const mockPost = vi.spyOn(apiClient, 'post').mockResolvedValueOnce({
        data: {
          id: 'rep-doc-123',
          document: 'doc-123',
          comparison: null,
          language: 'en',
          status: 'complete',
          created_at: new Date().toISOString(),
        },
      });

      const report = await realReportService.generateDocumentReport('doc-123', 'en');

      expect(mockPost).toHaveBeenCalledWith(
        '/api/documents/doc-123/report/',
        { language: 'en' },
        { params: { lang: 'en' } }
      );
      expect(report.id).toBe('rep-doc-123');
    });

    it('calls POST /api/comparisons/{id}/report/ for comparison reports', async () => {
      const mockPost = vi.spyOn(apiClient, 'post').mockResolvedValueOnce({
        data: {
          id: 'rep-comp-456',
          document: null,
          comparison: 'comp-456',
          language: 'hi',
          status: 'complete',
          created_at: new Date().toISOString(),
        },
      });

      const report = await realReportService.generateComparisonReport('comp-456', 'hi');

      expect(mockPost).toHaveBeenCalledWith(
        '/api/comparisons/comp-456/report/',
        { language: 'hi' },
        { params: { lang: 'hi' } }
      );
      expect(report.id).toBe('rep-comp-456');
    });

    it('calls GET /api/reports/{id}/download/ with responseType blob', async () => {
      const mockBlob = new Blob(['%PDF-1.4 test'], { type: 'application/pdf' });
      const mockGet = vi.spyOn(apiClient, 'get').mockResolvedValueOnce({
        data: mockBlob,
      });

      const blob = await realReportService.downloadReport('rep-doc-123');

      expect(mockGet).toHaveBeenCalledWith('/api/reports/rep-doc-123/download/', {
        responseType: 'blob',
      });
      expect(blob).toBe(mockBlob);
    });
  });
});
