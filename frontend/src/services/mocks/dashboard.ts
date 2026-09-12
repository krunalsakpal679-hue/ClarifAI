// MOCK DATA
/**
 * Mock Service for Section 8.7 Dashboard Summary (PRD Section 11 Mock Strategy)
 */
import type { DashboardSummaryResponse, IDashboardService } from '../../types';

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

const INITIAL_SUMMARY: DashboardSummaryResponse = {
  total_documents: 6,
  in_progress_count: 1,
  flagged_risk_count: 3,
  completed_count: 4,
  failed_count: 1,
};

let currentSummary: DashboardSummaryResponse = { ...INITIAL_SUMMARY };

export const mockDashboardService: IDashboardService = {
  getSummary: async (): Promise<DashboardSummaryResponse> => {
    // Simulate network delay per PRD Section 11
    await delay(150);
    return { ...currentSummary };
  },
};

/**
 * Testing helpers to set/reset mock dashboard data
 */
export const __setMockDashboardSummary = (summary: Partial<DashboardSummaryResponse>): void => {
  currentSummary = { ...currentSummary, ...summary };
};

export const __resetMockDashboardSummary = (): void => {
  currentSummary = { ...INITIAL_SUMMARY };
};
