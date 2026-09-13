import React from 'react';
import { Globe } from 'lucide-react';
import { useUiStore } from '../../store/uiStore';
import { toast } from '../ui/Toast';
import { cn } from '../../utils/cn';
import type { SupportedLanguage } from '../../i18n';

export interface LanguageToggleProps {
  value?: SupportedLanguage;
  onChange?: (lang: SupportedLanguage) => void;
  className?: string;
  size?: 'sm' | 'md';
}

/**
 * Analysis Language Toggle Component (PRD Ch. 22.7, 22.10 & Section 9.5)
 *
 * Controls the AI-generated analysis output language ('en' | 'hi')
 * independently from the UI-language interface chrome.
 * Reads and writes directly to uiStore.analysisLanguage by default.
 */
export const LanguageToggle: React.FC<LanguageToggleProps> = ({
  value,
  onChange,
  className,
  size = 'sm',
}) => {
  const storeLanguage = useUiStore((s) => s.analysisLanguage);
  const setStoreLanguage = useUiStore((s) => s.setAnalysisLanguage);

  const currentLang = value ?? storeLanguage;

  const handleSelect = (nextLang: SupportedLanguage) => {
    if (nextLang === currentLang) return;

    if (onChange) {
      onChange(nextLang);
    } else {
      setStoreLanguage(nextLang);
      toast.info(
        nextLang === 'hi'
          ? 'विश्लेषण भाषा हिंदी में बदली जा रही है...'
          : 'Switching analysis language to English...'
      );
    }
  };

  return (
    <div
      role="group"
      aria-label="Analysis Language Selection"
      className={cn(
        'inline-flex items-center p-1 rounded-lg border border-secondary-200 bg-secondary-50 text-xs font-semibold shadow-xs',
        className
      )}
      data-testid="analysis-language-toggle"
    >
      <div className="flex items-center gap-1 pl-1.5 pr-2 text-secondary-500 select-none">
        <Globe className="w-3.5 h-3.5 text-accent-600 shrink-0" aria-hidden="true" />
        <span className="hidden sm:inline text-[11px] font-medium text-secondary-500">Analysis:</span>
      </div>

      <button
        type="button"
        onClick={() => handleSelect('en')}
        aria-pressed={currentLang === 'en'}
        aria-label="Select English for AI analysis / Switch analysis language to English / English"
        className={cn(
          'rounded-md font-semibold transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-primary-500',
          size === 'sm' ? 'px-2.5 py-1 text-xs' : 'px-3 py-1.5 text-sm',
          currentLang === 'en'
            ? 'bg-white text-primary-950 shadow-xs'
            : 'text-secondary-600 hover:text-primary-900'
        )}
      >
        English
      </button>

      <button
        type="button"
        onClick={() => handleSelect('hi')}
        aria-pressed={currentLang === 'hi'}
        aria-label="Select Hindi for AI analysis / Switch analysis language to Hindi / हिंदी (Hindi)"
        className={cn(
          'rounded-md font-semibold transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-primary-500',
          size === 'sm' ? 'px-2.5 py-1 text-xs' : 'px-3 py-1.5 text-sm',
          currentLang === 'hi'
            ? 'bg-white text-primary-950 shadow-xs'
            : 'text-secondary-600 hover:text-primary-900'
        )}
      >
        हिंदी (Hindi)
      </button>
    </div>
  );
};

export default LanguageToggle;
