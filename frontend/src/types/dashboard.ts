/**
 * ClarifAI Section 8.7 Dashboard Summary API Contracts (PRD Ch. 20 & Ch. 30.7)
 */

export interface DashboardSummaryResponse {
  total_documents: number;
  in_progress_count: number;
  flagged_risk_count: number;
  completed_count: number;
  failed_count: number;
}

export interface IDashboardService {
  getSummary: () => Promise<DashboardSummaryResponse>;
}
