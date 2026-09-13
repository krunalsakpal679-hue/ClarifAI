/**
 * Real Comparison API Service (PRD Section 8.5 & Ch. 30.5)
 * Endpoints:
 * - POST /api/comparisons/
 * - GET  /api/comparisons/{id}/?lang={lang}
 * - GET  /api/comparisons/
 */
import { apiClient } from './client';
import type { ComparisonDetail, IComparisonService } from '../../types/comparison';

export const realComparisonService: IComparisonService = {
  create: async (documentIdA: string, documentIdB: string): Promise<ComparisonDetail> => {
    const response = await apiClient.post<ComparisonDetail>('/api/comparisons/', {
      document_a_id: documentIdA,
      document_b_id: documentIdB,
    });
    return response.data;
  },

  getResult: async (comparisonId: string, lang = 'en'): Promise<ComparisonDetail> => {
    const response = await apiClient.get<ComparisonDetail>(`/api/comparisons/${comparisonId}/`, {
      params: { lang },
    });
    return response.data;
  },

  list: async (): Promise<ComparisonDetail[]> => {
    const response = await apiClient.get<ComparisonDetail[]>('/api/comparisons/');
    return response.data;
  },
};
