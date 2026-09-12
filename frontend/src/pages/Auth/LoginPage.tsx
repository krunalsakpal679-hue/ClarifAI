import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../../store/authStore';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../components/ui/Card';

export const LoginPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const setAuth = useAuthStore((state) => state.setAuth);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Preserve redirected destination or default to dashboard
  const destination = (location.state as { from?: { pathname?: string } })?.from?.pathname || '/dashboard';

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please enter both email and password.');
      return;
    }

    // Phase 02 Auth Stub (Real endpoints connected in Phase 03)
    setAuth(
      {
        id: 'usr_test_1',
        email,
        fullName: email.split('@')[0] || 'ClarifAI User',
        preferredLanguage: 'en',
        createdAt: new Date().toISOString(),
      },
      'mock_access_token_phase_02'
    );
    navigate(destination, { replace: true });
  };

  const handleTestLogin = () => {
    setAuth(
      {
        id: 'usr_demo_1',
        email: 'legal.counsel@clarifai.internal',
        fullName: 'Legal Counsel',
        preferredLanguage: 'en',
        createdAt: new Date().toISOString(),
      },
      'mock_access_token_demo'
    );
    navigate(destination, { replace: true });
  };

  return (
    <Card elevation="md" className="border-secondary-200">
      <CardHeader>
        <CardTitle className="text-2xl font-serif text-primary-950">
          {t('nav.login', 'Sign In')}
        </CardTitle>
        <CardDescription>
          Access your legal document simplifying dashboard and clause risk intelligence.
        </CardDescription>
      </CardHeader>

      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          {error && (
            <div
              role="alert"
              className="p-3 text-xs bg-red-50 border border-red-200 text-red-700 rounded-md"
            >
              {error}
            </div>
          )}

          <Input
            id="login-email"
            label="Email Address"
            type="email"
            placeholder="you@company.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
          />

          <Input
            id="login-password"
            label="Password"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />

          <div className="text-right">
            <button
              type="button"
              className="text-xs text-primary-700 hover:text-primary-900 font-medium focus:outline-none focus:underline"
              onClick={() => alert('Password reset will be available in Phase 03.')}
            >
              Forgot password?
            </button>
          </div>
        </CardContent>

        <CardFooter className="flex flex-col gap-3 pt-2">
          <Button type="submit" variant="primary" className="w-full">
            {t('nav.login', 'Sign In')}
          </Button>

          {/* Quick Mock Login for Phase 02 Testing */}
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleTestLogin}
            className="w-full border-dashed border-secondary-300 text-secondary-700 text-xs"
          >
            ⚡ Quick Test Sign In (Demo User)
          </Button>

          <p className="text-xs text-center text-secondary-600 mt-2">
            Don't have an account?{' '}
            <Link to="/signup" className="text-primary-700 font-semibold hover:underline">
              {t('nav.signup', 'Sign Up')}
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
};
