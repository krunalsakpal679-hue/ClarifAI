// MOCK DATA
/**
 * Mock Service for Section 8.2 Document List (PRD Section 11 Mock Strategy)
 */
import type {
  DocumentItem,
  DocumentListParams,
  IDocumentService,
  PaginatedDocumentListResponse,
} from '../../types';

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export const INITIAL_MOCK_DOCUMENTS: DocumentItem[] = [
  {
    id: 'doc-msa-001',
    original_filename: 'Master_Services_Agreement_Enterprise_2026.pdf',
    file_reference: 'uploads/documents/doc-msa-001_Master_Services_Agreement_Enterprise_2026.pdf',
    document_type: 'Master Services Agreement',
    status: 'complete',
    failure_reason: null,
    overall_risk: 'high',
    uploaded_at: '2026-09-12T14:30:00.000Z',
    updated_at: '2026-09-12T14:35:00.000Z',
  },
  {
    id: 'doc-sla-002',
    original_filename: 'Vendor_Service_Level_Agreement_Q3.pdf',
    file_reference: 'uploads/documents/doc-sla-002_Vendor_Service_Level_Agreement_Q3.pdf',
    document_type: 'Service Level Agreement',
    status: 'complete',
    failure_reason: null,
    overall_risk: 'moderate',
    uploaded_at: '2026-09-11T16:15:00.000Z',
    updated_at: '2026-09-11T16:18:00.000Z',
  },
  {
    id: 'doc-nda-003',
    original_filename: 'Mutual_Confidentiality_NDA_AcmeCorp.pdf',
    file_reference: 'uploads/documents/doc-nda-003_Mutual_Confidentiality_NDA_AcmeCorp.pdf',
    document_type: 'Non-Disclosure Agreement',
    status: 'complete',
    failure_reason: null,
    overall_risk: 'low',
    uploaded_at: '2026-09-10T10:00:00.000Z',
    updated_at: '2026-09-10T10:02:00.000Z',
  },
  {
    id: 'doc-ip-004',
    original_filename: 'Standard_Employee_Proprietary_Info_IP.pdf',
    file_reference: 'uploads/documents/doc-ip-004_Standard_Employee_Proprietary_Info_IP.pdf',
    document_type: 'IP Agreement',
    status: 'complete',
    failure_reason: null,
    overall_risk: 'safe',
    uploaded_at: '2026-09-09T09:20:00.000Z',
    updated_at: '2026-09-09T09:22:00.000Z',
  },
  {
    id: 'doc-lease-005',
    original_filename: 'Commercial_Office_Lease_Draft_v2.pdf',
    file_reference: 'uploads/documents/doc-lease-005_Commercial_Office_Lease_Draft_v2.pdf',
    document_type: 'Lease Agreement',
    status: 'extracting',
    failure_reason: null,
    overall_risk: null,
    uploaded_at: '2026-09-12T17:45:00.000Z',
    updated_at: '2026-09-12T17:46:00.000Z',
  },
  {
    id: 'doc-scan-006',
    original_filename: 'Corrupted_Scan_Export_0912.pdf',
    file_reference: 'uploads/documents/doc-scan-006_Corrupted_Scan_Export_0912.pdf',
    document_type: null,
    status: 'failed',
    failure_reason: 'Corrupted PDF file header or unsupported encryption format.',
    overall_risk: null,
    uploaded_at: '2026-09-08T11:00:00.000Z',
    updated_at: '2026-09-08T11:01:00.000Z',
  },
];

let mockDocumentsDb: DocumentItem[] = [...INITIAL_MOCK_DOCUMENTS];

export const mockDocumentService: IDocumentService = {
  list: async (params?: DocumentListParams): Promise<PaginatedDocumentListResponse> => {
    // Simulate network delay per PRD Section 11
    await delay(150);

    const page = params?.page || 1;
    const pageSize = params?.page_size || 20;

    const startIndex = (page - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const paginatedResults = mockDocumentsDb.slice(startIndex, endIndex);

    return {
      count: mockDocumentsDb.length,
      next: endIndex < mockDocumentsDb.length ? `/api/documents/?page=${page + 1}` : null,
      previous: page > 1 ? `/api/documents/?page=${page - 1}` : null,
      results: paginatedResults,
    };
  },

  delete: async (id: string): Promise<void> => {
    await delay(150);
    const index = mockDocumentsDb.findIndex((doc) => doc.id === id);
    if (index === -1) {
      throw new Error('Document not found or access denied (404)');
    }
    mockDocumentsDb.splice(index, 1);
  },
};

/**
 * Testing helpers to set/reset mock document fixtures
 */
export const __setMockDocuments = (docs: DocumentItem[]): void => {
  mockDocumentsDb = [...docs];
};

export const __resetMockDocuments = (): void => {
  mockDocumentsDb = [...INITIAL_MOCK_DOCUMENTS];
};
