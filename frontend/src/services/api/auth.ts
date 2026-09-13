import { apiClient } from './client';
import type {
  IAuthService,
  SignUpRequest,
  SignUpResponse,
  LoginRequest,
  LoginResponse,
  RefreshResponse,
  LogoutResponse,
} from '../../types/auth';

/**
 * Real Authentication API Service (PRD Section 8.1 & Section 9.6)
 *
 * Connects to Django Backend auth endpoints:
 * - POST /api/auth/signup
 * - POST /api/auth/login
 * - POST /api/auth/refresh (No token argument, relies strictly on httpOnly cookie via withCredentials)
 * - POST /api/auth/logout
 */
export const apiAuthService: IAuthService = {
  async signup(payload: SignUpRequest): Promise<SignUpResponse> {
    const response = await apiClient.post<SignUpResponse>('/api/auth/signup', payload);
    return response.data;
  },

  async login(payload: LoginRequest): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>('/api/auth/login', payload);
    return response.data;
  },

  async refresh(): Promise<RefreshResponse> {
    // refresh() takes NO token argument; the browser sends the httpOnly refresh_token cookie
    const response = await apiClient.post<RefreshResponse>('/api/auth/refresh', {});
    return response.data;
  },

  async logout(): Promise<LogoutResponse> {
    const response = await apiClient.post<LogoutResponse>('/api/auth/logout', {});
    return response.data;
  },
};

export default apiAuthService;
