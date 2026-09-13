import type {
  IAuthService,
  SignUpRequest,
  SignUpResponse,
  LoginRequest,
  LoginResponse,
  RefreshResponse,
  LogoutResponse,
} from '../../types/auth';
import type { User } from '../../types';

/**
 * ============================================================================
 * MOCK DATA: Authentication Service Implementation (PRD Section 11 & Section 8.1)
 * ============================================================================
 *
 * Simulates Django backend auth endpoints with realistic network delays,
 * in-memory mock user repository, and validation error contracts.
 */

// Simulated delay helper
const delay = (ms = 250) => new Promise((resolve) => setTimeout(resolve, ms));

// MOCK DATA: In-memory registered user repository
interface MockUserRecord {
  user: User;
  passwordHash: string;
}

const mockUserDatabase: Map<string, MockUserRecord> = new Map([
  [
    'counsel@clarifai.internal',
    {
      user: {
        id: 'usr_counsel_001',
        email: 'counsel@clarifai.internal',
        fullName: 'Jane Counsel',
        preferredLanguage: 'en',
        createdAt: '2026-09-01T08:00:00.000Z',
      },
      passwordHash: 'Password123!',
    },
  ],
  [
    'existing@clarifai.internal',
    {
      user: {
        id: 'usr_existing_002',
        email: 'existing@clarifai.internal',
        fullName: 'Existing User',
        preferredLanguage: 'en',
        createdAt: '2026-09-02T10:00:00.000Z',
      },
      passwordHash: 'Password123!',
    },
  ],
]);

export interface MockHttpError extends Error {
  response: {
    status: number;
    data: Record<string, unknown>;
  };
}

const createMockHttpError = (
  status: number,
  data: Record<string, unknown>,
  message: string
): MockHttpError => {
  const err = new Error(message) as MockHttpError;
  err.response = { status, data };
  return err;
};

// MOCK DATA: Simulated server-side httpOnly refresh session state
let mockActiveRefreshSession: { userId: string } | null = {
  userId: 'usr_counsel_001',
};

export const mockAuthService: IAuthService = {
  /**
   * MOCK DATA: Signup endpoint simulation
   */
  async signup(payload: SignUpRequest): Promise<SignUpResponse> {
    await delay(300);

    const normalizedEmail = payload.email.trim().toLowerCase();

    // Check for duplicate email (PRD Ch. 10 user story)
    if (mockUserDatabase.has(normalizedEmail)) {
      throw createMockHttpError(
        400,
        { email: ['A user with this email address already exists.'] },
        'A user with this email address already exists.'
      );
    }

    const newUser: User = {
      id: `usr_${Date.now().toString(36)}`,
      email: payload.email.trim(),
      fullName: payload.email.split('@')[0] || 'ClarifAI User',
      preferredLanguage: 'en',
      createdAt: new Date().toISOString(),
    };

    // Store in mock database
    mockUserDatabase.set(normalizedEmail, {
      user: newUser,
      passwordHash: payload.password,
    });

    // Set active mock refresh session
    mockActiveRefreshSession = { userId: newUser.id };

    return {
      user: newUser,
      access: `mock_jwt_access_${newUser.id}_${Date.now()}`,
    };
  },

  /**
   * MOCK DATA: Login endpoint simulation
   */
  async login(payload: LoginRequest): Promise<LoginResponse> {
    await delay(300);

    const normalizedEmail = payload.email.trim().toLowerCase();
    const record = mockUserDatabase.get(normalizedEmail);

    // Generic error on failure per PRD Ch. 31/32: Never reveal if email exists or password failed
    if (!record || record.passwordHash !== payload.password) {
      throw createMockHttpError(
        401,
        { detail: 'Invalid email or password.' },
        'Invalid email or password.'
      );
    }

    // Set active mock refresh session
    mockActiveRefreshSession = { userId: record.user.id };

    return {
      user: record.user,
      access: `mock_jwt_access_${record.user.id}_${Date.now()}`,
    };
  },

  /**
   * MOCK DATA: Refresh endpoint simulation (No token argument per Section 8.1)
   */
  async refresh(): Promise<RefreshResponse> {
    await delay(200);

    if (!mockActiveRefreshSession) {
      throw createMockHttpError(
        401,
        { detail: 'Authentication refresh token was not provided.' },
        'Authentication refresh token was not provided.'
      );
    }

    return {
      access: `mock_jwt_rotated_access_${mockActiveRefreshSession.userId}_${Date.now()}`,
    };
  },

  /**
   * MOCK DATA: Logout endpoint simulation
   */
  async logout(): Promise<LogoutResponse> {
    await delay(150);
    // Invalidate mock server session
    mockActiveRefreshSession = null;

    return {
      message: 'Successfully logged out.',
    };
  },
};

// Export helper for tests to reset mock state
export const __resetMockAuthDatabase = () => {
  mockActiveRefreshSession = { userId: 'usr_counsel_001' };
};

export default mockAuthService;
