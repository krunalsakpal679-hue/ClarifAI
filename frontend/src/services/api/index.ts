import type { IAuthService } from '../../types/auth';
import { apiAuthService } from './auth';
import { mockAuthService } from '../mocks/auth';
import { setTokenRefreshHandler } from './client';

import type { IDashboardService } from '../../types/dashboard';
import { realDashboardService } from './dashboard';
import { mockDashboardService } from '../mocks/dashboard';

import type { IDocumentService } from '../../types/documents';
import { realDocumentService } from './documents';
import { mockDocumentService } from '../mocks/documents';

import type { IChatService } from '../../types/chat';
import { realChatService } from './chat';
import { mockChatService } from '../mocks/chat';

import type { IComparisonService } from '../../types/comparison';
import { realComparisonService } from './comparison';
import { mockComparisonService } from '../mocks/comparison';

import type { IReportService } from '../../types/reports';
import { realReportService } from './reports';
import { mockReportService } from '../mocks/reports';

/**
 * Service Factory & Mock/Real Switch (PRD Section 11 & Ch. 30.8)
 *
 * Isolated to services/api/index.ts:
 * - Production builds (PROD): Defaults to false (real backend integration) unless explicitly enabled with VITE_USE_MOCKS=true.
 * - Development & Test: Defaults to true (realistic mock service layer) unless VITE_USE_MOCKS=false.
 */
export const USE_MOCKS: boolean = import.meta.env.PROD
  ? import.meta.env.VITE_USE_MOCKS === 'true'
  : import.meta.env.VITE_USE_MOCKS !== 'false';

export const authService: IAuthService = USE_MOCKS ? mockAuthService : apiAuthService;

if (USE_MOCKS) {
  setTokenRefreshHandler(async () => {
    const res = await mockAuthService.refresh();
    return res.access;
  });
}

export const dashboardService: IDashboardService = USE_MOCKS
  ? mockDashboardService
  : realDashboardService;

export const documentService: IDocumentService = USE_MOCKS
  ? mockDocumentService
  : realDocumentService;

export const chatService: IChatService = USE_MOCKS
  ? mockChatService
  : realChatService;

export const comparisonService: IComparisonService = USE_MOCKS
  ? mockComparisonService
  : realComparisonService;

export const reportService: IReportService = USE_MOCKS
  ? mockReportService
  : realReportService;

export * from './client';
export * from './auth';
export * from './dashboard';
export * from './documents';
export * from './chat';
export * from './comparison';
export * from './reports';

