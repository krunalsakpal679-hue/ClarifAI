import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  ShieldCheck,
  Search,
  Lock,
  Layers,
  Sparkles,
  CheckCircle2,
  RefreshCw,
  Globe,
  Sliders,
} from 'lucide-react';
import {
  Button,
  Input,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  Badge,
  Spinner,
  SkeletonBlock,
} from './components/ui';
import { useAppStore } from './store';

export const App: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { language, setLanguage } = useAppStore();

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [inputValue, setInputValue] = useState<string>('Standard Non-Disclosure Agreement');
  const [hasError, setHasError] = useState<boolean>(false);

  const toggleLanguage = () => {
    const nextLang = language === 'en' ? 'hi' : 'en';
    setLanguage(nextLang);
    i18n.changeLanguage(nextLang);
  };

  return (
    <div className="min-h-screen bg-neutral-subtle text-primary selection:bg-accent selection:text-white pb-16">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-40 bg-white/90 backdrop-blur-md border-b border-neutral-border shadow-elevation-1">
        <div className="max-w-constrained mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-accent/10 p-2 rounded-control text-accent border border-accent/20">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-h3 font-bold text-primary tracking-tight">ClarifAI</span>
                <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-accent-light text-accent border border-accent/30">
                  {t('designSystem.phase')}
                </span>
              </div>
              <p className="text-[12px] text-neutral-text-secondary hidden sm:block">
                {t('common.tagline')}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Language Switcher */}
            <Button
              variant="secondary"
              size="sm"
              onClick={toggleLanguage}
              leftIcon={<Globe className="w-4 h-4 text-accent" />}
              aria-label="Toggle UI language between English and Hindi"
            >
              <span className="font-semibold">{language === 'en' ? 'हिन्दी' : 'English'}</span>
            </Button>

            {/* Simulating Loading Toggle */}
            <Button
              variant="tertiary"
              size="sm"
              onClick={() => setIsLoading((prev) => !prev)}
              leftIcon={<RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />}
            >
              {isLoading ? 'Reset State' : 'Simulate Loading'}
            </Button>
          </div>
        </div>
      </header>

      {/* Main Container constrained to PRD Ch. 24 Breakpoints */}
      <main className="max-w-constrained mx-auto px-4 sm:px-6 lg:px-8 pt-8 flex flex-col gap-10">
        {/* Hero Section */}
        <section className="bg-white rounded-card p-6 sm:p-8 border border-neutral-border shadow-elevation-1">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="max-w-2xl">
              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-risk-safe-bg border border-risk-safe-border text-risk-safe text-caption font-semibold uppercase tracking-wider mb-3">
                <CheckCircle2 className="w-3.5 h-3.5" />
                {t('designSystem.phase')}
              </div>
              <h1 className="text-h1 font-bold text-primary tracking-tight mb-2">
                {t('designSystem.title')}
              </h1>
              <p className="text-body text-neutral-text-secondary leading-relaxed">
                Foundational design system, typography, color palette tokens, accessible primitives,
                and UI internationalization built per PRD v2.3 (Chapters 9.1, 23, 24, and 25).
              </p>
            </div>

            {/* Architecture Card */}
            <div className="bg-neutral-subtle rounded-control p-4 border border-neutral-border/80 flex flex-col gap-2 min-w-[260px]">
              <div className="flex items-center gap-2 text-caption font-semibold text-primary">
                <Layers className="w-4 h-4 text-accent" />
                <span>Frontend Architecture</span>
              </div>
              <div className="text-[13px] text-neutral-text-secondary flex flex-col gap-1">
                <span>• React 18 + Vite + TypeScript (Strict)</span>
                <span>• Tailwind CSS + Framer Motion</span>
                <span>• Zustand + Axios Client</span>
                <span>• react-i18next (en / hi)</span>
              </div>
            </div>
          </div>
        </section>

        {/* PRD Chapter 9.1 Admin Decision Banner */}
        <section className="bg-accent-light/50 border border-accent/20 rounded-card p-4 sm:p-5 flex items-start gap-3.5">
          <div className="p-2 rounded-control bg-accent/10 text-accent shrink-0 mt-0.5">
            <Lock className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-body font-semibold text-primary">
              PRD Chapter 9.1 Role Decision Enforcement
            </h4>
            <p className="text-caption text-neutral-text-secondary mt-0.5 leading-relaxed">
              Per PRD v2.3 Final Decision (Section 9.1), no Administrator role, admin dashboard, or
              admin API endpoints exist in ClarifAI. All permissions strictly isolate authenticated
              users to their own documents. Zero admin code is present.
            </p>
          </div>
        </section>

        {/* Section 1: Color Palette Tokens (PRD Ch. 23.1) */}
        <section className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h2 className="text-h2 font-semibold text-primary flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-accent" />
              {t('designSystem.colorPalette')} (PRD 23.1)
            </h2>
            <span className="text-caption text-neutral-text-secondary">Exact Token Values</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {/* Primary Navy */}
            <div className="bg-white p-3.5 rounded-card border border-neutral-border shadow-elevation-1 flex flex-col gap-2">
              <div className="h-12 rounded-control bg-primary flex items-center justify-center text-white font-mono text-xs font-semibold">
                #1B2A4A
              </div>
              <div>
                <span className="text-caption font-semibold text-primary block">Primary / Navy</span>
                <span className="text-[11px] text-neutral-text-secondary">Brand & Headers</span>
              </div>
            </div>

            {/* Accent Deep Blue */}
            <div className="bg-white p-3.5 rounded-card border border-neutral-border shadow-elevation-1 flex flex-col gap-2">
              <div className="h-12 rounded-control bg-accent flex items-center justify-center text-white font-mono text-xs font-semibold">
                #2E5AAC
              </div>
              <div>
                <span className="text-caption font-semibold text-primary block">Accent / Deep Blue</span>
                <span className="text-[11px] text-neutral-text-secondary">Buttons & Active UI</span>
              </div>
            </div>

            {/* Neutral Surface */}
            <div className="bg-white p-3.5 rounded-card border border-neutral-border shadow-elevation-1 flex flex-col gap-2">
              <div className="h-12 rounded-control bg-neutral-subtle border border-neutral-border flex items-center justify-center text-primary font-mono text-xs font-semibold">
                #F7F8FA
              </div>
              <div>
                <span className="text-caption font-semibold text-primary block">Neutral Surface</span>
                <span className="text-[11px] text-neutral-text-secondary">Background & Canvas</span>
              </div>
            </div>

            {/* Neutral Border */}
            <div className="bg-white p-3.5 rounded-card border border-neutral-border shadow-elevation-1 flex flex-col gap-2">
              <div className="h-12 rounded-control bg-neutral-border flex items-center justify-center text-primary font-mono text-xs font-semibold">
                #C9CFD9
              </div>
              <div>
                <span className="text-caption font-semibold text-primary block">Neutral Border</span>
                <span className="text-[11px] text-neutral-text-secondary">Dividers & Cards</span>
              </div>
            </div>

            {/* Text Secondary */}
            <div className="bg-white p-3.5 rounded-card border border-neutral-border shadow-elevation-1 flex flex-col gap-2">
              <div className="h-12 rounded-control bg-neutral-text-secondary flex items-center justify-center text-white font-mono text-xs font-semibold">
                #5B6472
              </div>
              <div>
                <span className="text-caption font-semibold text-primary block">Text Secondary</span>
                <span className="text-[11px] text-neutral-text-secondary">Supporting Text</span>
              </div>
            </div>
          </div>

          {/* Risk Severity Colors (WCAG 2.1 AA Icon Paired) */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-1">
            <div className="bg-white p-3.5 rounded-card border border-neutral-border shadow-elevation-1 flex flex-col gap-2">
              <div className="h-10 rounded-control bg-risk-high flex items-center justify-center text-white font-mono text-xs font-semibold">
                #B23B3B
              </div>
              <div>
                <span className="text-caption font-semibold text-risk-high block">Risk: High</span>
                <span className="text-[11px] text-neutral-text-secondary">Severe Liability & Clauses</span>
              </div>
            </div>

            <div className="bg-white p-3.5 rounded-card border border-neutral-border shadow-elevation-1 flex flex-col gap-2">
              <div className="h-10 rounded-control bg-risk-moderate flex items-center justify-center text-white font-mono text-xs font-semibold">
                #C77B22
              </div>
              <div>
                <span className="text-caption font-semibold text-risk-moderate block">Risk: Moderate</span>
                <span className="text-[11px] text-neutral-text-secondary">Unusual or Vague Terms</span>
              </div>
            </div>

            <div className="bg-white p-3.5 rounded-card border border-neutral-border shadow-elevation-1 flex flex-col gap-2">
              <div className="h-10 rounded-control bg-risk-low flex items-center justify-center text-white font-mono text-xs font-semibold">
                #B08D1F
              </div>
              <div>
                <span className="text-caption font-semibold text-risk-low block">Risk: Low</span>
                <span className="text-[11px] text-neutral-text-secondary">Minor Ambiguity</span>
              </div>
            </div>

            <div className="bg-white p-3.5 rounded-card border border-neutral-border shadow-elevation-1 flex flex-col gap-2">
              <div className="h-10 rounded-control bg-risk-safe flex items-center justify-center text-white font-mono text-xs font-semibold">
                #2F7D5A
              </div>
              <div>
                <span className="text-caption font-semibold text-risk-safe block">Risk: Safe</span>
                <span className="text-[11px] text-neutral-text-secondary">Standard & Balanced</span>
              </div>
            </div>
          </div>
        </section>

        {/* Section 2: UI Primitives Gallery (Task 7) */}
        <section className="flex flex-col gap-6">
          <div className="flex items-center justify-between">
            <h2 className="text-h2 font-semibold text-primary flex items-center gap-2">
              <Sliders className="w-5 h-5 text-accent" />
              Design System Primitives (components/ui/)
            </h2>
            <span className="text-caption text-neutral-text-secondary">
              Fully Typed • Accessible Focus States
            </span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Buttons Showcase */}
            <Card>
              <CardHeader>
                <CardTitle>Button Primitives</CardTitle>
                <CardDescription>
                  Variants defined per PRD 23.4: Primary, Secondary, Tertiary, and Destructive.
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-4">
                <div className="flex flex-wrap items-center gap-3">
                  <Button variant="primary" isLoading={isLoading}>
                    {t('common.actions.upload')}
                  </Button>
                  <Button variant="secondary" isLoading={isLoading}>
                    {t('common.actions.compare')}
                  </Button>
                  <Button variant="tertiary" isLoading={isLoading}>
                    {t('common.actions.cancel')}
                  </Button>
                  <Button variant="destructive" isLoading={isLoading}>
                    {t('common.actions.delete')}
                  </Button>
                </div>

                <div className="border-t border-neutral-border/60 pt-3 flex flex-wrap items-center gap-3">
                  <Button size="sm">Small</Button>
                  <Button size="md">Medium</Button>
                  <Button size="lg">Large Button</Button>
                  <Button disabled>Disabled</Button>
                </div>
              </CardContent>
            </Card>

            {/* Inputs Showcase */}
            <Card>
              <CardHeader>
                <CardTitle>Input Primitives</CardTitle>
                <CardDescription>
                  Form input with labels, helper text, and accessible error states.
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-4">
                <Input
                  label="Document Title"
                  required
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  leftIcon={<Search className="w-4 h-4" />}
                  helperText="Search contract clauses by title or category"
                />

                <Input
                  label="Clause Risk Threshold"
                  error={hasError ? 'Threshold value must be between 0.0 and 1.0' : undefined}
                  defaultValue="1.45"
                  helperText="Demonstration of inline validation error state"
                  rightIcon={
                    <button
                      type="button"
                      onClick={() => setHasError((prev) => !prev)}
                      className="text-caption font-semibold text-accent hover:underline"
                    >
                      {hasError ? 'Clear' : 'Trigger Error'}
                    </button>
                  }
                />
              </CardContent>
            </Card>

            {/* Badges Showcase (WCAG Icon Rule Enforced) */}
            <Card>
              <CardHeader>
                <CardTitle>Badges & Risk Indicators</CardTitle>
                <CardDescription>
                  WCAG 2.1 AA Compliance: Severity badges paired with iconography, never color alone.
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-4">
                <div>
                  <span className="text-caption font-semibold text-neutral-text-secondary block mb-2">
                    Clause Risk Severity (PRD 23.1)
                  </span>
                  <div className="flex flex-wrap gap-2">
                    <Badge severity="HIGH">{t('risk.high')}</Badge>
                    <Badge severity="MODERATE">{t('risk.moderate')}</Badge>
                    <Badge severity="LOW">{t('risk.low')}</Badge>
                    <Badge severity="SAFE">{t('risk.safe')}</Badge>
                  </div>
                </div>

                <div className="border-t border-neutral-border/60 pt-3">
                  <span className="text-caption font-semibold text-neutral-text-secondary block mb-2">
                    Processing Status (PRD 15.1)
                  </span>
                  <div className="flex flex-wrap gap-2">
                    <Badge status="QUEUED" />
                    <Badge status="PROCESSING" />
                    <Badge status="COMPLETED" />
                    <Badge status="FAILED" />
                  </div>
                </div>

                <div className="border-t border-neutral-border/60 pt-3">
                  <span className="text-caption font-semibold text-neutral-text-secondary block mb-2">
                    Clause Categories (PRD 16.2)
                  </span>
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="outline">Liability</Badge>
                    <Badge variant="outline">Payment</Badge>
                    <Badge variant="outline">Termination</Badge>
                    <Badge variant="outline">IP Ownership</Badge>
                    <Badge variant="outline">Confidentiality</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Cards, Spinner & Skeletons */}
            <Card variant="interactive">
              <CardHeader>
                <CardTitle>Card Variants & Skeleton Loaders</CardTitle>
                <CardDescription>
                  Demonstration of interactive hover card elevation and placeholder skeleton blocks.
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-4">
                <div className="flex items-center gap-4">
                  <span className="text-caption font-semibold text-neutral-text-secondary">
                    Spinner Sizes:
                  </span>
                  <Spinner size="sm" variant="accent" />
                  <Spinner size="md" variant="accent" />
                  <Spinner size="lg" variant="accent" />
                  <Spinner size="md" variant="primary" />
                </div>

                <div className="border-t border-neutral-border/60 pt-3 flex flex-col gap-2">
                  <span className="text-caption font-semibold text-neutral-text-secondary">
                    Skeleton Placeholders:
                  </span>
                  <SkeletonBlock height={16} width="85%" rounded="control" />
                  <SkeletonBlock height={14} width="60%" rounded="control" />
                  <SkeletonBlock height={12} width="40%" rounded="control" />
                </div>
              </CardContent>
              <CardFooter className="justify-between text-caption text-neutral-text-secondary">
                <span>Elevation Level 1 (Default) &rarr; Level 2 (Hover)</span>
                <span className="text-accent font-semibold">Hover to Elevate &rarr;</span>
              </CardFooter>
            </Card>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="max-w-constrained mx-auto px-4 sm:px-6 lg:px-8 pt-12 text-caption text-neutral-text-secondary flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-neutral-border mt-12">
        <p>ClarifAI &copy; 2026. Built strictly to PRD v2.3 Approved Baseline.</p>
        <div className="flex items-center gap-4">
          <span>PRD Chapters 9.1, 23, 24, 25</span>
          <span>•</span>
          <span>Zero Admin Policy Enforced</span>
        </div>
      </footer>
    </div>
  );
};

export default App;
