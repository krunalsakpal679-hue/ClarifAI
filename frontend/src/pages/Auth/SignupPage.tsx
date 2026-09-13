import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
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
import {
  PasswordStrengthMeter,
  isPasswordValid,
} from '../../components/ui/PasswordStrengthMeter';
import { toast } from '../../components/ui/Toast';

export const SignupPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Field validation errors
  const [emailError, setEmailError] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const validate = (): boolean => {
    let isValid = true;
    setEmailError(null);
    setPasswordError(null);
    setFormError(null);

    // Email validation
    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      setEmailError('Email address is required.');
      isValid = false;
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail)) {
      setEmailError('Please enter a valid email address (e.g., name@company.com).');
      isValid = false;
    }

    // Password validation
    if (!password) {
      setPasswordError('Password is required.');
      isValid = false;
    } else if (!isPasswordValid(password)) {
      setPasswordError(
        'Password does not meet the security policy requirements.'
      );
      isValid = false;
    }

    return isValid;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setIsLoading(true);
    try {
      const response = await authService.signup({
        email: email.trim(),
        password,
      });

      // Update in-memory auth store
      setAuth(response.user, response.access);

      toast.success('Account created successfully! Welcome to ClarifAI.');
      navigate('/dashboard', { replace: true });
    } catch (err: unknown) {
      const errorObj = err as {
        response?: {
          data?: {
            email?: string[];
            detail?: string;
            message?: string;
          };
        };
        message?: string;
      };

      const message =
        errorObj?.response?.data?.email?.[0] ||
        errorObj?.response?.data?.detail ||
        errorObj?.response?.data?.message ||
        errorObj?.message ||
        'Registration failed. Please try again.';

      if (message.toLowerCase().includes('already exists') || errorObj?.response?.data?.email) {
        setEmailError(message);
      } else {
        setFormError(message);
      }

      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card elevation="md" className="border-secondary-200">
      <CardHeader>
        <CardTitle className="text-2xl font-serif text-primary-950">
          {t('nav.signup', 'Create Account')}
        </CardTitle>
        <CardDescription>
          Get started with AI-powered legal document simplification and clause risk intelligence.
        </CardDescription>
      </CardHeader>

      <form onSubmit={handleSubmit} noValidate>
        <CardContent className="space-y-4">
          {formError && (
            <div
              role="alert"
              className="p-3 text-xs bg-red-50 border border-red-200 text-red-700 rounded-md"
            >
              {formError}
            </div>
          )}

          <div className="space-y-1">
            <Input
              id="signup-email"
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
              aria-describedby={emailError ? 'signup-email-error' : undefined}
            />
          </div>

          <div className="space-y-1">
            <Input
              id="signup-password"
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
              autoComplete="new-password"
              aria-describedby={
                passwordError ? 'signup-password-error' : 'password-requirements'
              }
            />
            <PasswordStrengthMeter password={password} />
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
            {isLoading ? 'Creating account...' : t('auth.createAccount', 'Create Account')}
          </Button>

          <p className="text-xs text-center text-secondary-600 mt-2">
            Already have an account?{' '}
            <Link
              to="/login"
              className="text-primary-700 font-semibold hover:underline focus:outline-none focus:ring-1 focus:ring-primary-500 rounded"
            >
              {t('nav.login', 'Sign In')}
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
};

export default SignupPage;
