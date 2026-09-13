/* eslint-disable @typescript-eslint/no-explicit-any */
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { apiClient, setTokenRefreshHandler, defaultTokenRefresh } from '../api/client';
import { useAuthStore } from '../../store/authStore';

describe('apiClient 401 Silent Refresh Interceptor (PRD Section 9.6 & Ch. 26.1)', () => {
  const originalAdapter = apiClient.defaults.adapter;

  beforeEach(() => {
    useAuthStore.getState().clearAuth();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    apiClient.defaults.adapter = originalAdapter;
    setTokenRefreshHandler(defaultTokenRefresh);
  });

  it('triggers silent refresh on 401, updates in-memory token, and retries request', async () => {
    const mockUser = {
      id: 'usr_counsel_001',
      email: 'counsel@clarifai.internal',
      fullName: 'Jane Counsel',
      preferredLanguage: 'en' as const,
      createdAt: '2026-09-01T00:00:00.000Z',
    };

    useAuthStore.getState().setAuth(mockUser, 'expired_access_token');

    let refreshCalled = false;
    const newAccessToken = 'refreshed_valid_access_token_777';

    setTokenRefreshHandler(async () => {
      refreshCalled = true;
      return newAccessToken;
    });

    let attempts = 0;
    apiClient.defaults.adapter = async (config: any) => {
      attempts++;
      if (attempts === 1) {
        const err: any = new Error('Request failed with status code 401');
        err.response = { status: 401, data: { detail: 'Token expired' }, config };
        err.config = config;
        throw err;
      }

      return {
        status: 200,
        statusText: 'OK',
        data: { id: 'doc_123', title: 'Analyzed Document' },
        headers: {},
        config,
      };
    };

    const response = await apiClient.get('/documents/doc_123');

    expect(refreshCalled).toBe(true);
    expect(useAuthStore.getState().accessToken).toBe(newAccessToken);
    expect(response.data).toEqual({ id: 'doc_123', title: 'Analyzed Document' });
    expect(attempts).toBe(2);
  });

  it('clears credentials in authStore when token refresh fails', async () => {
    useAuthStore.getState().setAuth(
      {
        id: 'usr_counsel_001',
        email: 'counsel@clarifai.internal',
        fullName: 'Jane Counsel',
        preferredLanguage: 'en' as const,
        createdAt: '2026-09-01T00:00:00.000Z',
      },
      'expired_access_token'
    );

    setTokenRefreshHandler(async () => {
      const err: any = new Error('Refresh token expired');
      err.response = { status: 401 };
      throw err;
    });

    apiClient.defaults.adapter = async (config: any) => {
      const err: any = new Error('Request failed with status code 401');
      err.response = { status: 401, data: { detail: 'Token expired' }, config };
      err.config = config;
      throw err;
    };

    await expect(apiClient.get('/documents/doc_123')).rejects.toBeDefined();

    // Store must be logged out
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
    expect(useAuthStore.getState().accessToken).toBeNull();
    expect(useAuthStore.getState().user).toBeNull();
  });

  it('does NOT trigger silent refresh loop when 401 occurs on auth endpoints', async () => {
    let refreshInvoked = false;
    setTokenRefreshHandler(async () => {
      refreshInvoked = true;
      return 'new_token';
    });

    apiClient.defaults.adapter = async (config: any) => {
      const err: any = new Error('Invalid email or password.');
      err.response = { status: 401, data: { detail: 'Invalid email or password.' }, config };
      err.config = config;
      throw err;
    };

    await expect(apiClient.post('/api/auth/login', { email: 'bad@clarifai.internal', password: 'bad' })).rejects.toMatchObject({
      status: 401,
      message: 'Invalid email or password.',
      error: {
        message: 'Invalid email or password.',
      },
    });

    expect(refreshInvoked).toBe(false);
  });

  it('handles 429 rate-limiting with Retry-After header and surfaces formatted message', async () => {
    apiClient.defaults.adapter = async (config: any) => {
      const err: any = new Error('Rate limit exceeded');
      err.response = {
        status: 429,
        headers: { 'retry-after': '45' },
        data: { error: { code: 'RATE_LIMIT_EXCEEDED', message: 'Too many requests' } },
        config,
      };
      err.config = config;
      throw err;
    };

    await expect(apiClient.get('/documents/doc_123')).rejects.toMatchObject({
      status: 429,
      message: 'Too many requests, try again in 45s.',
      retryAfter: 45,
      error: {
        code: 'RATE_LIMIT_EXCEEDED',
        message: 'Too many requests, try again in 45s.',
      },
    });
  });

  it('handles 502/503 on AI endpoints with exact verbatim copy and strips provider details', async () => {
    apiClient.defaults.adapter = async (config: any) => {
      const err: any = new Error('Bad Gateway');
      err.response = {
        status: 503,
        data: {
          detail: 'OpenAI quota exceeded: model gpt-4o-mini rate_limit_error',
          error: { code: 'OPENAI_ERROR', message: 'Raw internal LLM crash' },
        },
        config,
      };
      err.config = config;
      throw err;
    };

    const rejected = await apiClient.get('/documents/doc_123/chat').catch((e) => e);

    expect(rejected).toEqual({
      status: 503,
      message: 'AI processing is temporarily unavailable. Please try again later.',
      error: {
        code: 'AI_SERVICE_UNAVAILABLE',
        message: 'AI processing is temporarily unavailable. Please try again later.',
      },
      errors: null,
    });
    // Ensure raw quota / provider details are NOT exposed
    expect(rejected.message).not.toContain('OpenAI');
    expect(rejected.message).not.toContain('quota');
  });

  it('preserves code-keyed error shape { error: { code, message } } on standard API errors', async () => {
    apiClient.defaults.adapter = async (config: any) => {
      const err: any = new Error('Request failed with 404');
      err.response = {
        status: 404,
        data: {
          error: {
            code: 'DOCUMENT_NOT_FOUND',
            message: 'Requested document does not exist.',
          },
        },
        config,
      };
      err.config = config;
      throw err;
    };

    await expect(apiClient.get('/documents/missing_doc')).rejects.toMatchObject({
      status: 404,
      message: 'Requested document does not exist.',
      error: {
        code: 'DOCUMENT_NOT_FOUND',
        message: 'Requested document does not exist.',
      },
    });
  });
});

