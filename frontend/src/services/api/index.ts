import type { IAuthService } from '../../types/auth';
import { apiAuthService } from './auth';
import { mockAuthService } from '../mocks/auth';
import { setTokenRefreshHandler } from './client';

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

export * from './client';
export * from './auth';
