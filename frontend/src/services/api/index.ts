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

/**
 * Service Factory & Mock/Real Switch (PRD Section 11)
 *
 * Isolated to services/api/index.ts:
 * When VITE_USE_MOCKS !== 'false', the application uses the realistic mock service layer.
 */
export const USE_MOCKS: boolean = import.meta.env.VITE_USE_MOCKS !== 'false';

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

export * from './client';
export * from './auth';
export * from './dashboard';
export * from './documents';
export * from './chat';
export * from './comparison';

