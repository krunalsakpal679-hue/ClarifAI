/**
 * Real API Service for Section 8.2 Document List & Detail
 */
import { apiClient } from './client';
import type {
  ClauseItem,
  DocumentItem,
  DocumentListParams,
  DocumentSummary,
  DocumentUploadResponse,
  IDocumentService,
  PaginatedClauseResponse,
  PaginatedDocumentListResponse,
} from '../../types';

export const realDocumentService: IDocumentService = {
  list: async (params?: DocumentListParams): Promise<PaginatedDocumentListResponse> => {
    const response = await apiClient.get<PaginatedDocumentListResponse>('/api/documents/', {
      params,
    });
    return response.data;
  },
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/documents/${id}/`);
  },
  upload: async (
    file: File,
    onProgress?: (progressPercentage: number) => void,
    signal?: AbortSignal
  ): Promise<DocumentUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<DocumentUploadResponse>('/api/documents/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      signal,
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(Math.min(100, Math.max(0, percent)));
        }
      },
    });

    return response.data;
  },
  getById: async (id: string): Promise<DocumentItem> => {
    // Section 8.2 Combined document detail & status polling endpoint
    const response = await apiClient.get<DocumentItem>(`/api/documents/${id}/`);
    return response.data;
  },
  getSummary: async (id: string, lang = 'en'): Promise<DocumentSummary> => {
    // Section 8.3 Document Summary endpoint (PRD Ch. 16 & Ch. 30.3)
    const response = await apiClient.get<DocumentSummary>(`/api/documents/${id}/summary/`, {
      params: { lang },
    });
    return response.data;
  },
  getClauses: async (
    id: string,
    lang = 'en',
    severity?: string
  ): Promise<PaginatedClauseResponse> => {
    // Section 8.3 Document Clauses endpoint with optional severity filter (PRD Ch. 16 & Ch. 30.3)
    const params: Record<string, string> = { lang };
    if (severity) {
      params.severity = severity.toLowerCase();
    }
    const response = await apiClient.get<PaginatedClauseResponse>(`/api/documents/${id}/clauses/`, {
      params,
    });
    return response.data;
  },

  getClauseDetail: async (
    documentId: string,
    clauseId: string,
    lang = 'en'
  ): Promise<ClauseItem> => {
    // Section 8.3 Single Clause Detail endpoint (PRD Ch. 12 & Ch. 22.8)
    const response = await apiClient.get<ClauseItem>(
      `/api/documents/${documentId}/clauses/${clauseId}/`,
      {
        params: { lang },
      }
    );
    return response.data;
  },
};



