import { describe, it, expect, beforeEach } from 'vitest';
import { dashboardService } from '../api';
import {
  __setMockDashboardSummary,
  __resetMockDashboardSummary,
} from '../mocks/dashboard';

describe('DashboardService (PRD Section 8.7 & Ch. 20)', () => {
  beforeEach(() => {
    __resetMockDashboardSummary();
  });

  it('fetches aggregate statistics matching Section 8.7 schema', async () => {
    const summary = await dashboardService.getSummary();

    expect(summary).toBeDefined();
    expect(typeof summary.total_documents).toBe('number');
    expect(typeof summary.in_progress_count).toBe('number');
    expect(typeof summary.flagged_risk_count).toBe('number');
    expect(typeof summary.completed_count).toBe('number');
    expect(typeof summary.failed_count).toBe('number');

    // Default mock totals
    expect(summary.total_documents).toBe(6);
    expect(summary.in_progress_count).toBe(1);
    expect(summary.flagged_risk_count).toBe(3);
    expect(summary.completed_count).toBe(4);
    expect(summary.failed_count).toBe(1);
  });

  it('reflects updated statistics when mock data changes', async () => {
    __setMockDashboardSummary({
      total_documents: 15,
      completed_count: 12,
      flagged_risk_count: 5,
    });

    const summary = await dashboardService.getSummary();
    expect(summary.total_documents).toBe(15);
    expect(summary.completed_count).toBe(12);
    expect(summary.flagged_risk_count).toBe(5);
  });
});
