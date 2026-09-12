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
 * - POST /auth/signup
 * - POST /auth/login
 * - POST /auth/refresh (No token argument, relies strictly on httpOnly cookie via withCredentials)
 * - POST /auth/logout
 */
export const apiAuthService: IAuthService = {
  async signup(payload: SignUpRequest): Promise<SignUpResponse> {
    const response = await apiClient.post<SignUpResponse>('/auth/signup', payload);
    return response.data;
  },

  async login(payload: LoginRequest): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>('/auth/login', payload);
    return response.data;
  },

  async refresh(): Promise<RefreshResponse> {
    // refresh() takes NO token argument; the browser sends the httpOnly refresh_token cookie
    const response = await apiClient.post<RefreshResponse>('/auth/refresh', {});
    return response.data;
  },

  async logout(): Promise<LogoutResponse> {
    const response = await apiClient.post<LogoutResponse>('/auth/logout', {});
    return response.data;
  },
};

export default apiAuthService;
