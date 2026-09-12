import axios, { type AxiosInstance, type InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '../../store/authStore';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

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

// Response interceptor for unified error formatting
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.message ||
      error.response?.data?.detail ||
      error.message ||
      'An unexpected network error occurred';

    return Promise.reject({
      status: error.response?.status,
      message,
      errors: error.response?.data?.errors,
    });
  }
);

export default apiClient;
