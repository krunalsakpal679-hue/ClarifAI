import { describe, it, expect, beforeEach } from 'vitest';
import { documentService } from '../api';
import {
  __setMockDocuments,
  __resetMockDocuments,
  INITIAL_MOCK_DOCUMENTS,
} from '../mocks/documents';

describe('DocumentService (PRD Section 8.2 & Ch. 20, 29.2, 30.2)', () => {
  beforeEach(() => {
    __resetMockDocuments();
  });

  it('lists paginated documents with Section 8.2 schema', async () => {
    const res = await documentService.list({ page: 1, page_size: 10 });

    expect(res).toBeDefined();
    expect(res.count).toBe(INITIAL_MOCK_DOCUMENTS.length);
    expect(Array.isArray(res.results)).toBe(true);
    expect(res.results.length).toBe(INITIAL_MOCK_DOCUMENTS.length);

    // Verify document properties
    const firstDoc = res.results[0];
    expect(firstDoc.id).toBeDefined();
    expect(firstDoc.original_filename).toBeDefined();
    expect(firstDoc.status).toBeDefined();
    expect(firstDoc.overall_risk).toBe('high');
  });

  it('supports pagination parameters correctly', async () => {
    const resPage1 = await documentService.list({ page: 1, page_size: 2 });
    expect(resPage1.results.length).toBe(2);
    expect(resPage1.next).toContain('page=2');
    expect(resPage1.previous).toBeNull();

    const resPage2 = await documentService.list({ page: 2, page_size: 2 });
    expect(resPage2.results.length).toBe(2);
    expect(resPage2.results[0].id).not.toBe(resPage1.results[0].id);
    expect(resPage2.previous).toContain('page=1');
  });

  it('returns empty list when user has 0 documents', async () => {
    __setMockDocuments([]);

    const res = await documentService.list();
    expect(res.count).toBe(0);
    expect(res.results).toEqual([]);
    expect(res.next).toBeNull();
    expect(res.previous).toBeNull();
  });

  it('deletes document successfully matching Section 8.2 contract', async () => {
    const initialList = await documentService.list();
    const docToDelete = initialList.results[0];
    expect(docToDelete).toBeDefined();

    await documentService.delete(docToDelete.id);

    const updatedList = await documentService.list();
    expect(updatedList.count).toBe(initialList.count - 1);
    expect(updatedList.results.find((d) => d.id === docToDelete.id)).toBeUndefined();
  });

  it('throws error when attempting to delete non-existent document (404)', async () => {
    await expect(documentService.delete('non-existent-doc-id')).rejects.toThrow(
      /Document not found or access denied/i
    );
  });

  describe('upload (Section 8.2 & PRD Ch. 14, 22.5, 58)', () => {
    it('uploads valid PDF document and returns DocumentUploadResponse', async () => {
      const file = new File(['%PDF-1.4 sample content'], 'Vendor_Agreement_2026.pdf', {
        type: 'application/pdf',
      });

      const progressValues: number[] = [];
      const response = await documentService.upload(file, (p) => {
        progressValues.push(p);
      });

      expect(response).toBeDefined();
      expect(response.id).toBeDefined();
      expect(response.original_filename).toBe('Vendor_Agreement_2026.pdf');
      expect(response.status).toBe('queued');
      expect(response.uploaded_at).toBeDefined();

      // Progress reached 100%
      expect(progressValues.length).toBeGreaterThanOrEqual(1);
      expect(progressValues[progressValues.length - 1]).toBe(100);

      // Verify newly uploaded document appears in list()
      const listRes = await documentService.list();
      expect(listRes.results.some((doc) => doc.id === response.id)).toBe(true);
    });

    it('cancels active upload when AbortSignal is aborted', async () => {
      const file = new File(['%PDF-1.4 content'], 'Sample_Contract.pdf', {
        type: 'application/pdf',
      });
      const controller = new AbortController();

      const uploadPromise = documentService.upload(file, undefined, controller.signal);
      // Abort immediately
      controller.abort();

      await expect(uploadPromise).rejects.toThrow(/canceled/i);
    });

    it('rejects password-protected PDF with distinct specific error message (PRD Ch. 58 R-12)', async () => {
      const passwordFile = new File(['%PDF-1.4 encrypted content'], 'Confidential_Password_Protected.pdf', {
        type: 'application/pdf',
      });

      await expect(documentService.upload(passwordFile)).rejects.toThrow(
        'Password-protected PDFs are not supported. Please upload an unencrypted document.'
      );
    });

    it('rejects corrupted PDF with specific corrupted message', async () => {
      const corruptedFile = new File(['bad content'], 'corrupted_file.pdf', {
        type: 'application/pdf',
      });

      await expect(documentService.upload(corruptedFile)).rejects.toThrow(
        'PDF file is corrupted or unparseable.'
      );
    });
  });

  describe('getById (Section 8.2 Combined Document Detail / Status Endpoint)', () => {
    it('retrieves combined document metadata and status by ID', async () => {
      const doc = await documentService.getById('doc-msa-001');

      expect(doc).toBeDefined();
      expect(doc.id).toBe('doc-msa-001');
      expect(doc.original_filename).toBe('Master_Services_Agreement_Enterprise_2026.pdf');
      expect(doc.status).toBe('complete');
      expect(doc.overall_risk).toBe('high');
    });

    it('throws 404 when document is not found', async () => {
      await expect(documentService.getById('non-existent-id')).rejects.toThrow(/404/);
    });
  });

  describe('getSummary (Section 8.3 Document Summary Endpoint)', () => {
    it('retrieves four-field executive summary by ID', async () => {
      const summary = await documentService.getSummary('doc-msa-001');

      expect(summary).toBeDefined();
      expect(summary.document_id).toBe('doc-msa-001');
      expect(summary.purpose_text).toBeTruthy();
      expect(summary.key_risks_text).toBeTruthy();
      expect(summary.key_terms_text).toBeTruthy();
      expect(summary.obligations_text).toBeTruthy();
      expect(summary.translation_available).toBe(true);
    });

    it('retrieves translated Hindi summary when lang=hi', async () => {
      const summary = await documentService.getSummary('doc-msa-001', 'hi');

      expect(summary).toBeDefined();
      expect(summary.purpose_text).toContain('मास्टर सेवा समझौता');
    });
  });

  describe('getClauses (Section 8.3 Document Clauses Endpoint)', () => {
    it('retrieves all clauses across four severities and eight categories', async () => {
      const response = await documentService.getClauses('doc-msa-001');

      expect(response).toBeDefined();
      expect(response.results.length).toBeGreaterThanOrEqual(8);

      const severities = new Set(response.results.map((c) => c.severity));
      expect(severities.has('High')).toBe(true);
      expect(severities.has('Moderate')).toBe(true);
      expect(severities.has('Low')).toBe(true);
      expect(severities.has('Safe')).toBe(true);

      const categories = new Set<string>(
        response.results.map((c) => c.category).filter(Boolean) as string[]
      );
      expect(categories.has('Renewal')).toBe(true);
      expect(categories.has('Auto-renewal')).toBe(false);
    });

    it('filters clauses by severity', async () => {
      const response = await documentService.getClauses('doc-msa-001', 'en', 'high');
      expect(response.results.every((c) => c.severity === 'High')).toBe(true);
    });
  });

  describe('getClauseDetail (Section 8.3 Single Clause Detail Endpoint)', () => {
    it('retrieves single clause detail matching Section 8.3 shape', async () => {
      const clause = await documentService.getClauseDetail('doc-msa-001', 'clause-101');

      expect(clause).toBeDefined();
      expect(clause.id).toBe('clause-101');
      expect(clause.document_id).toBe('doc-msa-001');
      expect(clause.position).toBe(1);
      expect(clause.severity).toBe('High');
      expect(clause.category).toBe('Liability');
      expect(clause.original_text).toContain('Customer shall defend, indemnify');
      expect(clause.simplified_text).toContain('maximum dollar limit');
      expect(clause.explanation).toContain('Uncapped unilateral indemnification');
      expect(clause.rule_findings.length).toBeGreaterThan(0);
    });

    it('returns Hindi translation when lang=hi is requested', async () => {
      const clause = await documentService.getClauseDetail('doc-msa-001', 'clause-101', 'hi');

      expect(clause).toBeDefined();
      expect(clause.simplified_text).toContain('मुकदमा होता है');
      expect(clause.translation_available).toBe(true);
    });

    it('throws 404 when clause is not found', async () => {
      await expect(
        documentService.getClauseDetail('doc-msa-001', 'non-existent-clause')
      ).rejects.toThrow(/404/);
    });

    it('throws 404 when document is not found', async () => {
      await expect(
        documentService.getClauseDetail('non-existent-doc', 'clause-101')
      ).rejects.toThrow(/404/);
    });
  });
});



