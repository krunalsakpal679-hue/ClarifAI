/* eslint-disable react-refresh/only-export-components */
import React from 'react';
import { Check, X } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface PasswordStrengthMeterProps {
  password: string;
  showRequirements?: boolean;
  className?: string;
}

export interface PasswordRule {
  id: string;
  label: string;
  met: boolean;
}

export const getPasswordRules = (pwd: string): PasswordRule[] => [
  { id: 'length', label: 'At least 8 characters', met: pwd.length >= 8 },
  { id: 'uppercase', label: 'At least one uppercase letter (A-Z)', met: /[A-Z]/.test(pwd) },
  { id: 'lowercase', label: 'At least one lowercase letter (a-z)', met: /[a-z]/.test(pwd) },
  { id: 'number', label: 'At least one number (0-9)', met: /[0-9]/.test(pwd) },
  { id: 'special', label: 'At least one special character (!@#$%^&*)', met: /[!@#$%^&*(),.?":{}|<>_\-\\[\]]/.test(pwd) },
];

export const isPasswordValid = (pwd: string): boolean => {
  return getPasswordRules(pwd).every((r) => r.met);
};

export const PasswordStrengthMeter: React.FC<PasswordStrengthMeterProps> = ({
  password,
  showRequirements = true,
  className,
}) => {
  const rules = getPasswordRules(password);
  const metCount = rules.filter((r) => r.met).length;

  let strengthLabel = 'Weak';
  let strengthColor = 'bg-risk-high';
  let widthPercent = '20%';

  if (!password) {
    strengthLabel = 'Empty';
    strengthColor = 'bg-neutral-border';
    widthPercent = '0%';
  } else if (metCount <= 2) {
    strengthLabel = 'Weak';
    strengthColor = 'bg-risk-high';
    widthPercent = '25%';
  } else if (metCount === 3) {
    strengthLabel = 'Fair';
    strengthColor = 'bg-risk-moderate';
    widthPercent = '50%';
  } else if (metCount === 4) {
    strengthLabel = 'Good';
    strengthColor = 'bg-accent';
    widthPercent = '75%';
  } else {
    strengthLabel = 'Strong';
    strengthColor = 'bg-risk-safe';
    widthPercent = '100%';
  }

  return (
    <div className={cn('space-y-2 mt-2', className)} role="status" aria-label="Security strength indicator">
      {/* Strength Bar */}
      <div className="space-y-1">
        <div className="flex items-center justify-between text-caption font-medium">
          <span className="text-secondary-600 text-xs">Password Strength</span>
          {password && (
            <span
              className={cn(
                'text-xs font-semibold',
                strengthLabel === 'Weak' && 'text-risk-high',
                strengthLabel === 'Fair' && 'text-risk-moderate',
                strengthLabel === 'Good' && 'text-accent',
                strengthLabel === 'Strong' && 'text-risk-safe'
              )}
            >
              {strengthLabel}
            </span>
          )}
        </div>

        <div className="h-1.5 w-full bg-secondary-200 rounded-full overflow-hidden">
          <div
            className={cn('h-full transition-all duration-300 rounded-full', strengthColor)}
            style={{ width: widthPercent }}
          />
        </div>
      </div>

      {/* Requirement Rules List */}
      {showRequirements && (
        <ul className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 pt-1 text-caption text-secondary-600">
          {rules.map((rule) => (
            <li key={rule.id} className="flex items-center gap-1.5 text-[11px]">
              {rule.met ? (
                <Check className="w-3.5 h-3.5 text-risk-safe shrink-0" aria-hidden="true" />
              ) : (
                <X className="w-3.5 h-3.5 text-secondary-400 shrink-0" aria-hidden="true" />
              )}
              <span className={rule.met ? 'text-secondary-900 font-medium' : 'text-secondary-500'}>
                {rule.label}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
