/**
 * Real API Service for Section 8.7 Dashboard Summary
 */
import { apiClient } from './client';
import type { DashboardSummaryResponse, IDashboardService } from '../../types';

export const realDashboardService: IDashboardService = {
  getSummary: async (): Promise<DashboardSummaryResponse> => {
    const response = await apiClient.get<DashboardSummaryResponse>('/api/dashboard/summary');
    return response.data;
  },
};
