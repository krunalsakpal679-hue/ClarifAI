import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../../store/authStore';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../components/ui/Card';

export const SignupPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName || !email || !password || !confirmPassword) {
      setError('Please fill in all required fields.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    // Phase 02 Auth Stub (Real endpoints connected in Phase 03)
    setAuth(
      {
        id: 'usr_new_1',
        email,
        fullName,
        preferredLanguage: 'en',
        createdAt: new Date().toISOString(),
      },
      'mock_access_token_signup'
    );
    navigate('/dashboard', { replace: true });
  };

  return (
    <Card elevation="md" className="border-secondary-200">
      <CardHeader>
        <CardTitle className="text-2xl font-serif text-primary-950">
          {t('nav.signup', 'Create Account')}
        </CardTitle>
        <CardDescription>
          Get started with AI-powered legal document simplification and risk analysis.
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
            id="signup-name"
            label="Full Name"
            type="text"
            placeholder="Jane Doe"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
            autoComplete="name"
          />

          <Input
            id="signup-email"
            label="Work Email"
            type="email"
            placeholder="jane@company.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
          />

          <Input
            id="signup-password"
            label="Password"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="new-password"
          />

          <Input
            id="signup-confirm-password"
            label="Confirm Password"
            type="password"
            placeholder="••••••••"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            autoComplete="new-password"
          />
        </CardContent>

        <CardFooter className="flex flex-col gap-3 pt-2">
          <Button type="submit" variant="primary" className="w-full">
            {t('nav.signup', 'Create Account')}
          </Button>

          <p className="text-xs text-center text-secondary-600 mt-2">
            Already have an account?{' '}
            <Link to="/login" className="text-primary-700 font-semibold hover:underline">
              {t('nav.login', 'Sign In')}
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
};
