import axios, { type AxiosInstance, type InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '../../store/authStore';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

/**
 * Shared Axios HTTP Client for ClarifAI Frontend (PRD Section 9.6 & Ch. 26.1)
 *
 * Configured with:
 * - `withCredentials: true` to ensure the httpOnly refresh cookie is automatically
 *   included on requests to authentication refresh and API endpoints.
 * - In-memory access token retrieval via `useAuthStore.getState().accessToken`.
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Attach in-memory access token if present
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().accessToken;
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Token refresh delegate (pluggable for mock layer and real backend)
let refreshPromise: Promise<string> | null = null;

export const defaultTokenRefresh = async (): Promise<string> => {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      try {
        const response = await axios.post<{ access: string }>(
          `${API_BASE_URL}/auth/refresh`,
          {},
          { withCredentials: true }
        );
        return response.data.access;
      } finally {
        refreshPromise = null;
      }
    })();
  }
  return refreshPromise;
};

let tokenRefreshHandler: () => Promise<string> = defaultTokenRefresh;

export const setTokenRefreshHandler = (handler: () => Promise<string>) => {
  tokenRefreshHandler = handler;
};

// Response interceptor: on 401, attempt silent token refresh once
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Check if error is 401 and request can be silently refreshed
    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/login') &&
      !originalRequest.url?.includes('/auth/signup') &&
      !originalRequest.url?.includes('/auth/refresh') &&
      !originalRequest.url?.includes('/auth/logout')
    ) {
      originalRequest._retry = true;

      try {
        const newAccessToken = await tokenRefreshHandler();
        useAuthStore.getState().setAccessToken(newAccessToken);
        originalRequest.headers = originalRequest.headers || {};
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        useAuthStore.getState().logout();
        if (typeof window !== 'undefined' && !window.location.pathname?.includes('/login')) {
          try {
            window.location.href = '/login';
          } catch {
            // Ignore jsdom navigation warning in test environments
          }
        }
        return Promise.reject(refreshError);
      }
    }

    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      (Array.isArray(error.response?.data?.email) && error.response.data.email[0]) ||
      error.message ||
      'An unexpected network error occurred';

    return Promise.reject({
      status: error.response?.status,
      message,
      errors: error.response?.data?.errors || error.response?.data,
    });
  }
);

export default apiClient;
