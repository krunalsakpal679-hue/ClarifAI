import { describe, it, expect, beforeEach } from 'vitest';
import { mockAuthService, __resetMockAuthDatabase } from '../mocks/auth';

describe('AuthService (PRD Section 8.1 & Section 11 Mock Strategy)', () => {
  beforeEach(() => {
    __resetMockAuthDatabase();
  });

  describe('signup()', () => {
    it('successfully registers a new user and returns user profile + in-memory access token', async () => {
      const uniqueEmail = `newuser_${Date.now()}@clarifai.internal`;
      const result = await mockAuthService.signup({
        email: uniqueEmail,
        password: 'Password123!',
      });

      expect(result.user).toBeDefined();
      expect(result.user.email).toBe(uniqueEmail);
      expect(result.access).toMatch(/^mock_jwt_access_/);

      // Verify no refresh token is returned in frontend response body (PRD Section 9.6)
      const record = result as unknown as Record<string, unknown>;
      expect(record['refresh']).toBeUndefined();
      expect(record['refreshToken']).toBeUndefined();
    });

    it('rejects duplicate email signup with 400 Bad Request error per PRD Ch. 10', async () => {
      const existingEmail = 'existing@clarifai.internal';

      await expect(
        mockAuthService.signup({
          email: existingEmail,
          password: 'Password123!',
        })
      ).rejects.toMatchObject({
        response: {
          status: 400,
          data: {
            email: ['A user with this email address already exists.'],
          },
        },
      });
    });
  });

  describe('login()', () => {
    it('successfully authenticates valid credentials and returns user + access token', async () => {
      const result = await mockAuthService.login({
        email: 'counsel@clarifai.internal',
        password: 'Password123!',
      });

      expect(result.user).toBeDefined();
      expect(result.user.email).toBe('counsel@clarifai.internal');
      expect(result.access).toMatch(/^mock_jwt_access_/);

      // Verify no refresh token is exposed to client code (PRD Section 9.6)
      const record = result as unknown as Record<string, unknown>;
      expect(record['refresh']).toBeUndefined();
      expect(record['refreshToken']).toBeUndefined();
    });

    it('rejects invalid password with generic 401 error (PRD Ch. 31/32)', async () => {
      await expect(
        mockAuthService.login({
          email: 'counsel@clarifai.internal',
          password: 'WrongPassword999!',
        })
      ).rejects.toMatchObject({
        response: {
          status: 401,
          data: {
            detail: 'Invalid email or password.',
          },
        },
      });
    });

    it('rejects non-existent email with identical generic 401 error (PRD Ch. 31/32)', async () => {
      await expect(
        mockAuthService.login({
          email: 'doesnotexist@clarifai.internal',
          password: 'Password123!',
        })
      ).rejects.toMatchObject({
        response: {
          status: 401,
          data: {
            detail: 'Invalid email or password.',
          },
        },
      });
    });
  });

  describe('refresh()', () => {
    it('rotates and returns new access token with NO client token argument (PRD Section 8.1 & 9.6)', async () => {
      // Call refresh with no parameters
      const result = await mockAuthService.refresh();

      expect(result.access).toBeDefined();
      expect(result.access).toMatch(/^mock_jwt_rotated_access_/);
    });
  });

  describe('logout()', () => {
    it('invalidates active session and subsequent refresh fails with 401', async () => {
      const logoutResult = await mockAuthService.logout();
      expect(logoutResult.message).toBe('Successfully logged out.');

      // Subsequent refresh must fail with 401
      await expect(mockAuthService.refresh()).rejects.toMatchObject({
        response: {
          status: 401,
        },
      });
    });
  });
});
