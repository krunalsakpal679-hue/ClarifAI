/**
 * ClarifAI Section 8.2 Document List & Detail API Contracts (PRD Ch. 20, 29.2, 30.2)
 */

export type DocumentStatusType =
  | 'queued'
  | 'extracting'
  | 'ocr'
  | 'segmenting'
  | 'classifying'
  | 'simplifying'
  | 'summarizing'
  | 'indexing'
  | 'complete'
  | 'failed';

export type DocumentOverallRisk = 'high' | 'moderate' | 'low' | 'safe' | null;

export interface DocumentItem {
  id: string;
  original_filename: string;
  file_reference: string;
  document_type: string | null;
  status: DocumentStatusType;
  failure_reason: string | null;
  overall_risk: DocumentOverallRisk;
  uploaded_at: string;
  updated_at: string;
}

export interface PaginatedDocumentListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: DocumentItem[];
}

export interface DocumentListParams {
  page?: number;
  page_size?: number;
}

export interface DocumentUploadResponse {
  id: string;
  original_filename: string;
  file_reference: string;
  status: DocumentStatusType;
  uploaded_at: string;
}

export interface IDocumentService {
  list: (params?: DocumentListParams) => Promise<PaginatedDocumentListResponse>;
  delete: (id: string) => Promise<void>;
  upload: (
    file: File,
    onProgress?: (progressPercentage: number) => void,
    signal?: AbortSignal
  ) => Promise<DocumentUploadResponse>;
}


