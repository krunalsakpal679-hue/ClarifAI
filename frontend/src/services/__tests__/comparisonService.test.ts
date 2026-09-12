import { describe, it, expect, beforeEach } from 'vitest';
import {
  mockComparisonService,
  __resetMockComparisons,
  SAMPLE_COMPARISON_RESULTS,
} from '../mocks/comparison';
import { __resetMockDocuments, __setMockDocumentStatus } from '../mocks/documents';

describe('ComparisonService (PRD Section 8.5 & Ch. 18, 30.5)', () => {
  beforeEach(() => {
    __resetMockDocuments();
    __resetMockComparisons();
  });

  describe('create (POST /api/comparisons/)', () => {
    it('creates pairwise comparison between two complete documents', async () => {
      const comp = await mockComparisonService.create('doc-msa-001', 'doc-sla-002');

      expect(comp).toBeDefined();
      expect(comp.id).toBe('comp-doc-msa-001-doc-sla-002');
      expect(comp.base_document_id).toBe('doc-msa-001');
      expect(comp.target_document_id).toBe('doc-sla-002');
      expect(comp.status).toBe('complete');
      expect(comp.results.length).toBeGreaterThan(0);
      expect(comp.is_low_confidence).toBe(false);
      expect(comp.confidence_warning).toBeNull();
    });

    it('rejects comparison of document against itself with 400 Bad Request', async () => {
      await expect(
        mockComparisonService.create('doc-msa-001', 'doc-msa-001')
      ).rejects.toThrow(/Cannot compare a document against itself/i);
    });

    it('rejects comparison with 422 DOCUMENT_NOT_READY if either document is incomplete', async () => {
      __setMockDocumentStatus('doc-sla-002', 'segmenting');

      await expect(
        mockComparisonService.create('doc-msa-001', 'doc-sla-002')
      ).rejects.toThrow(/DOCUMENT_NOT_READY/i);
    });

    it('flags low-confidence indicator when documents are structurally divergent per PRD Ch. 18.3', async () => {
      __setMockDocumentStatus('doc-lease-005', 'complete');
      const comp = await mockComparisonService.create('doc-msa-001', 'doc-lease-005');

      expect(comp.is_low_confidence).toBe(true);
      expect(comp.confidence_warning).toMatch(/ratio > 2\.0|significantly different/i);
    });
  });

  describe('getResult (GET /api/comparisons/{id}/)', () => {
    it('retrieves comparison detail with changed, matched, and missing items', async () => {
      const comp = await mockComparisonService.getResult('comp-msa-sla');

      expect(comp.id).toBe('comp-msa-sla');
      expect(comp.results).toHaveLength(SAMPLE_COMPARISON_RESULTS.length);

      const changed = comp.results.filter((r) => r.category === 'changed');
      const matched = comp.results.filter((r) => r.category === 'matched');
      const missing = comp.results.filter((r) => r.category === 'missing');

      expect(changed.length).toBeGreaterThan(0);
      expect(matched.length).toBeGreaterThan(0);
      expect(missing.length).toBeGreaterThan(0);
    });

    it('returns low-confidence indicator for comp-low-confidence variant', async () => {
      const comp = await mockComparisonService.getResult('comp-low-confidence');

      expect(comp.is_low_confidence).toBe(true);
      expect(comp.confidence_warning).toContain('PRD Ch. 18.3');
    });

    it('supports multilingual Hindi translation when lang=hi is specified', async () => {
      const comp = await mockComparisonService.getResult('comp-msa-sla', 'hi');

      expect(comp).toBeDefined();
      const changed = comp.results.find((r) => r.category === 'changed');
      expect(changed?.difference_explanation).toContain('हिंदी अनुवाद');
    });

    it('throws 404 error when comparison ID does not exist', async () => {
      await expect(
        mockComparisonService.getResult('comp-nonexistent-999')
      ).rejects.toThrow(/404/);
    });
  });

  describe('list (GET /api/comparisons/)', () => {
    it('lists available comparison instances', async () => {
      const list = await mockComparisonService.list!();
      expect(list.length).toBeGreaterThanOrEqual(2);
    });
  });
});
