/**
 * Real API Service for Section 8.2 Document List & Detail
 */
import { apiClient } from './client';
import type {
  DocumentListParams,
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
};
