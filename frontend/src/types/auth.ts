import type { User } from './index';

/**
 * Authentication API Contracts (PRD Section 8.1 & Section 9.6)
 */

export interface SignUpRequest {
  email: string;
  password: string;
}

export interface SignUpResponse {
  user: User;
  access: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  user: User;
  access: string;
}

export interface RefreshResponse {
  access: string;
}

export interface LogoutResponse {
  message: string;
}

export interface AuthApiError {
  status?: number;
  message: string;
  errors?: Record<string, string[]>;
}

export interface IAuthService {
  signup(payload: SignUpRequest): Promise<SignUpResponse>;
  login(payload: LoginRequest): Promise<LoginResponse>;
  /**
   * Refresh takes NO token parameter; relies strictly on httpOnly cookie (PRD 8.1 & 9.6).
   */
  refresh(): Promise<RefreshResponse>;
  logout(): Promise<LogoutResponse>;
}
