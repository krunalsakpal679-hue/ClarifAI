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

    const originalUrl = originalRequest?.url || '';
    const status = error.response?.status;

    // AI-service-unavailable handling (PRD Section 56.20 & Ch. 30.8)
    // For 502/503 on AI-backed endpoints, show verbatim copy and never expose provider/quota details
    const isAiEndpoint =
      originalUrl.includes('/documents') ||
      originalUrl.includes('/chat') ||
      originalUrl.includes('/comparisons') ||
      originalUrl.includes('lang=');

    if ((status === 502 || status === 503) && isAiEndpoint) {
      const verbatimAiMessage = 'AI processing is temporarily unavailable. Please try again later.';
      return Promise.reject({
        status,
        message: verbatimAiMessage,
        error: {
          code: 'AI_SERVICE_UNAVAILABLE',
          message: verbatimAiMessage,
        },
        errors: null,
      });
    }

    // 429 Rate-limit handling (PRD Ch. 30.8)
    if (status === 429) {
      const retryAfterHeader =
        error.response?.headers?.['retry-after'] ??
        error.response?.headers?.['Retry-After'] ??
        (typeof error.response?.headers?.get === 'function' ? error.response.headers.get('retry-after') : null);

      let retrySeconds = 60;
      if (retryAfterHeader) {
        const parsed = parseInt(String(retryAfterHeader), 10);
        if (!isNaN(parsed) && parsed > 0) {
          retrySeconds = parsed;
        } else {
          const dateDiff = Math.max(1, Math.round((new Date(String(retryAfterHeader)).getTime() - Date.now()) / 1000));
          if (!isNaN(dateDiff) && dateDiff > 0) {
            retrySeconds = dateDiff;
          }
        }
      }

      const rateLimitMessage = `Too many requests, try again in ${retrySeconds}s.`;
      return Promise.reject({
        status: 429,
        message: rateLimitMessage,
        error: {
          code: 'RATE_LIMIT_EXCEEDED',
          message: rateLimitMessage,
        },
        retryAfter: retrySeconds,
        errors: error.response?.data?.errors || null,
      });
    }

    // Standard code-keyed error shape (PRD Ch. 30.8: { error: { code, message } })
    const responseError = error.response?.data?.error;
    const errorCode =
      (typeof responseError === 'object' && responseError?.code) ||
      error.response?.data?.code ||
      (status ? `HTTP_${status}` : 'NETWORK_ERROR');

    const errorMessage =
      (typeof responseError === 'object' && responseError?.message) ||
      error.response?.data?.detail ||
      error.response?.data?.message ||
      (Array.isArray(error.response?.data?.email) && error.response.data.email[0]) ||
      error.message ||
      'An unexpected network error occurred';

    return Promise.reject({
      status,
      message: errorMessage,
      error: {
        code: errorCode,
        message: errorMessage,
      },
      errors: error.response?.data?.errors || error.response?.data,
    });
  }
);

export default apiClient;

