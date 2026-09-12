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
});

