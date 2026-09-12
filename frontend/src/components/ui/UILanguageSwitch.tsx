import React from 'react';
import { useTranslation } from 'react-i18next';
import { Globe } from 'lucide-react';
import { useAppStore } from '../../store';
import { cn } from '../../utils/cn';

export interface UILanguageSwitchProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  size?: 'sm' | 'md';
}

export const UILanguageSwitch: React.FC<UILanguageSwitchProps> = ({
  size = 'sm',
  className,
  ...props
}) => {
  const { i18n } = useTranslation();
  const { language, setLanguage } = useAppStore();

  const isEnglish = language === 'en';
  const targetLang = isEnglish ? 'hi' : 'en';
  const displayLabel = isEnglish ? 'हिन्दी' : 'English';
  const fullLabel = isEnglish ? 'Switch UI to Hindi' : 'Switch UI to English';

  const handleToggle = () => {
    setLanguage(targetLang);
    i18n.changeLanguage(targetLang);
  };

  return (
    <button
      type="button"
      onClick={handleToggle}
      aria-label={fullLabel}
      title={fullLabel}
      className={cn(
        'inline-flex items-center justify-center font-medium rounded-control border transition-all duration-micro',
        'border-neutral-border bg-white text-primary hover:bg-neutral-subtle hover:border-neutral-text-secondary active:bg-neutral-border/30',
        'focus-ring select-none shadow-elevation-1',
        size === 'sm' ? 'py-1.5 px-3 text-caption gap-1.5' : 'py-2 px-3.5 text-body gap-2',
        className
      )}
      {...props}
    >
      <Globe className={cn('shrink-0 text-accent', size === 'sm' ? 'w-3.5 h-3.5' : 'w-4 h-4')} aria-hidden="true" />
      <span>{displayLabel}</span>
    </button>
  );
};

export default UILanguageSwitch;
