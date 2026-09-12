import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../../store/authStore';
import { authService } from '../../services/api';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '../../components/ui/Card';
import { toast } from '../../components/ui/Toast';

export const LoginPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const setAuth = useAuthStore((state) => state.setAuth);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const [emailError, setEmailError] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);

  // Preserve redirected destination or default to dashboard
  const destination =
    (location.state as { from?: { pathname?: string } })?.from?.pathname || '/dashboard';

  const validate = (): boolean => {
    let isValid = true;
    setEmailError(null);
    setPasswordError(null);
    setAuthError(null);

    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      setEmailError('Email address is required.');
      isValid = false;
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail)) {
      setEmailError('Please enter a valid email address.');
      isValid = false;
    }

    if (!password) {
      setPasswordError('Password is required.');
      isValid = false;
    }

    return isValid;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setIsLoading(true);
    setAuthError(null);

    try {
      const response = await authService.login({
        email: email.trim(),
        password,
      });

      // Update in-memory auth store
      setAuth(response.user, response.access);

      toast.success('Signed in successfully.');
      navigate(destination, { replace: true });
    } catch {
      // PRD Chapter 31 / 32: Always show a generic error on authentication failure
      const genericError = 'Invalid email or password.';
      setAuthError(genericError);
      toast.error(genericError);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePrefillDemoUser = () => {
    setEmail('counsel@clarifai.internal');
    setPassword('Password123!');
    setEmailError(null);
    setPasswordError(null);
    setAuthError(null);
  };

  return (
    <Card elevation="md" className="border-secondary-200">
      <CardHeader>
        <CardTitle className="text-2xl font-serif text-primary-950">
          {t('auth.signIn', 'Sign In')}
        </CardTitle>
        <CardDescription>
          Access your legal document simplifying workspace and clause risk intelligence.
        </CardDescription>
      </CardHeader>

      <form onSubmit={handleSubmit} noValidate>
        <CardContent className="space-y-4">
          {authError && (
            <div
              role="alert"
              className="p-3 text-xs bg-red-50 border border-red-200 text-red-700 rounded-md font-medium"
            >
              {authError}
            </div>
          )}

          <div className="space-y-1">
            <Input
              id="login-email"
              label="Work Email Address"
              type="email"
              placeholder="counsel@company.com"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                if (emailError) setEmailError(null);
              }}
              error={emailError || undefined}
              required
              autoComplete="email"
              aria-describedby={emailError ? 'login-email-error' : undefined}
            />
          </div>

          <div className="space-y-1">
            <Input
              id="login-password"
              label="Password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                if (passwordError) setPasswordError(null);
              }}
              error={passwordError || undefined}
              required
              autoComplete="current-password"
              aria-describedby={passwordError ? 'login-password-error' : undefined}
            />
          </div>
        </CardContent>

        <CardFooter className="flex flex-col gap-3 pt-2">
          <Button
            type="submit"
            variant="primary"
            className="w-full"
            isLoading={isLoading}
            disabled={isLoading}
          >
            {isLoading ? 'Signing in...' : t('auth.signIn', 'Sign In')}
          </Button>

          {/* Quick Demo Credentials Prefill */}
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handlePrefillDemoUser}
            className="w-full border-dashed border-secondary-300 text-secondary-600 hover:text-primary-900 text-xs"
          >
            ⚡ Auto-Fill Demo Credentials (Counsel)
          </Button>

          <p className="text-xs text-center text-secondary-600 mt-2">
            Don't have an account?{' '}
            <Link
              to="/signup"
              className="text-primary-700 font-semibold hover:underline focus:outline-none focus:ring-1 focus:ring-primary-500 rounded"
            >
              {t('nav.signup', 'Sign Up')}
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
};

export default LoginPage;
