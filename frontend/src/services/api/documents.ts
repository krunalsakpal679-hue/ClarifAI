/**
 * Real API Service for Section 8.2 Document List & Detail
 */
import { apiClient } from './client';
import type {
  DocumentItem,
  DocumentListParams,
  DocumentUploadResponse,
  IDocumentService,
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
};



