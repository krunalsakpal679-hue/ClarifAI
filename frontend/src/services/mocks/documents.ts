// MOCK DATA
/**
 * Mock Service for Section 8.2 Document List (PRD Section 11 Mock Strategy)
 */
import type {
  DocumentItem,
  DocumentListParams,
  DocumentStatusType,
  DocumentUploadResponse,
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
  {
    id: 'doc-sample-123',
    original_filename: 'Sample_Services_Agreement_123.pdf',
    file_reference: 'uploads/documents/doc-sample-123_Sample.pdf',
    document_type: 'Master Services Agreement',
    status: 'extracting',
    failure_reason: null,
    overall_risk: null,
    uploaded_at: '2026-09-12T14:30:00.000Z',
    updated_at: '2026-09-12T14:35:00.000Z',
  },
];

let mockDocumentsDb: DocumentItem[] = INITIAL_MOCK_DOCUMENTS.map((d) => ({ ...d }));
let autoProgressEnabled = false;

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

  upload: async (
    file: File,
    onProgress?: (progressPercentage: number) => void,
    signal?: AbortSignal
  ): Promise<DocumentUploadResponse> => {
    if (signal?.aborted) {
      throw new DOMException('Upload canceled by user', 'AbortError');
    }

    const lowerName = file.name.toLowerCase();

    // 1. Password-protected PDF check (Distinct message per PRD Ch. 14, Ch. 58 R-12)
    if (lowerName.includes('password') || lowerName.includes('encrypted')) {
      await delay(100);
      throw new Error('Password-protected PDFs are not supported. Please upload an unencrypted document.');
    }

    // 2. Corrupted PDF check
    if (lowerName.includes('corrupted')) {
      await delay(100);
      throw new Error('PDF file is corrupted or unparseable.');
    }

    // 3. Empty PDF check
    if (file.size === 0 || lowerName.includes('empty')) {
      await delay(100);
      throw new Error('PDF file is corrupted or empty.');
    }

    // Step-by-step progress simulation (e.g. 25% -> 50% -> 75% -> 100%)
    const steps = [25, 50, 75, 100];
    for (const step of steps) {
      if (signal?.aborted) {
        throw new DOMException('Upload canceled by user', 'AbortError');
      }
      await delay(80);
      if (signal?.aborted) {
        throw new DOMException('Upload canceled by user', 'AbortError');
      }
      onProgress?.(step);
    }

    const newDocId = `doc-upload-${Date.now().toString(36)}-${Math.random().toString(36).substring(2, 6)}`;
    const newDoc: DocumentItem = {
      id: newDocId,
      original_filename: file.name,
      file_reference: `uploads/documents/${newDocId}_${file.name}`,
      document_type: 'Legal Document',
      status: 'queued',
      failure_reason: null,
      overall_risk: null,
      uploaded_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    mockDocumentsDb.unshift(newDoc);

    return {
      id: newDoc.id,
      original_filename: newDoc.original_filename,
      file_reference: newDoc.file_reference,
      status: newDoc.status,
      uploaded_at: newDoc.uploaded_at,
    };
  },

  getById: async (id: string): Promise<DocumentItem> => {
    await delay(50);
    const doc = mockDocumentsDb.find((d) => d.id === id);
    if (!doc) {
      if (id.startsWith('doc-')) {
        const fallbackDoc: DocumentItem = {
          id,
          original_filename: `Document_${id}.pdf`,
          file_reference: `uploads/documents/${id}.pdf`,
          document_type: 'Legal Document',
          status: 'extracting',
          failure_reason: null,
          overall_risk: null,
          uploaded_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        mockDocumentsDb.push(fallbackDoc);
        return { ...fallbackDoc };
      }
      throw new Error(`Document not found with ID ${id} (404)`);
    }

    // Auto progression simulation for in-progress documents
    if (autoProgressEnabled && doc.status !== 'complete' && doc.status !== 'failed') {
      const stageSequence: DocumentStatusType[] = [
        'queued',
        'extracting',
        'ocr',
        'segmenting',
        'classifying',
        'simplifying',
        'summarizing',
        'indexing',
        'complete',
      ];
      const currentIndex = stageSequence.indexOf(doc.status);
      if (currentIndex !== -1 && currentIndex < stageSequence.length - 1) {
        doc.status = stageSequence[currentIndex + 1];
        doc.updated_at = new Date().toISOString();
      }
    }

    return { ...doc };
  },
};

/**
 * Testing helpers to set/reset mock document fixtures
 */
export const __setMockDocuments = (docs: DocumentItem[]): void => {
  mockDocumentsDb = [...docs];
};

export const __setMockDocumentProgression = (enabled: boolean): void => {
  autoProgressEnabled = enabled;
};

export const __setMockDocumentStatus = (
  id: string,
  status: DocumentStatusType,
  failureReason: string | null = null
): void => {
  const doc = mockDocumentsDb.find((d) => d.id === id);
  if (doc) {
    doc.status = status;
    doc.failure_reason = failureReason;
    doc.updated_at = new Date().toISOString();
  }
};

export const __resetMockDocuments = (): void => {
  mockDocumentsDb = INITIAL_MOCK_DOCUMENTS.map((doc) => ({ ...doc }));
  autoProgressEnabled = false;
};

