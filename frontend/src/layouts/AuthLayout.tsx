import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { UILanguageSwitch } from '../components/ui/UILanguageSwitch';
import { ToastContainer } from '../components/ui/Toast';

export const AuthLayout: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-surface">
      {/* Left Branding Panel (Visible on Desktop lg+) */}
      <div className="hidden lg:flex lg:w-1/2 bg-primary-950 text-white p-12 flex-col justify-between relative overflow-hidden">
        {/* Background ambient gradient */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-primary-800/30 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-accent-900/20 rounded-full blur-3xl pointer-events-none -ml-20 -mb-20" />

        {/* Top: Logo */}
        <div className="relative z-10">
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-white font-bold text-2xl tracking-tight focus:outline-none focus:ring-2 focus:ring-accent-500 rounded-md py-1"
          >
            <div className="w-10 h-10 rounded-xl bg-primary-800 text-white flex items-center justify-center font-black text-xl shadow-elevation-1 border border-primary-700">
              C
            </div>
            <span>Clarif<span className="text-accent-400">AI</span></span>
          </Link>
          <p className="mt-2 text-primary-200 text-sm max-w-sm">
            {t('common.tagline', 'AI-Powered Legal Document Simplification & Risk Analysis')}
          </p>
        </div>

        {/* Middle: Value Pillars */}
        <div className="relative z-10 space-y-8 my-8 max-w-lg">
          <div className="space-y-3">
            <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider bg-primary-900 text-accent-300 border border-primary-800">
              Enterprise Grade
            </span>
            <h1 className="text-3xl font-serif font-bold text-white tracking-tight leading-tight">
              Demystify Complex Contracts with Confidence
            </h1>
            <p className="text-primary-200 text-sm leading-relaxed">
              Transform dense, impenetrable legal agreements into plain-English summaries, pinpointed risk scores, and actionable redline recommendations.
            </p>
          </div>

          <div className="space-y-4 pt-4 border-t border-primary-900">
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-accent-500/20 text-accent-400 flex items-center justify-center flex-shrink-0 mt-0.5 text-xs font-bold">
                ✓
              </div>
              <div>
                <h2 className="text-sm font-semibold text-white">Strict Document Grounding</h2>
                <p className="text-xs text-primary-300">Every summary and risk flag links back directly to the source text with zero hallucinated obligations.</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-accent-500/20 text-accent-400 flex items-center justify-center flex-shrink-0 mt-0.5 text-xs font-bold">
                ✓
              </div>
              <div>
                <h2 className="text-sm font-semibold text-white">Clause-by-Clause Risk Severity</h2>
                <p className="text-xs text-primary-300">Clear 4-tier risk classification: High Risk, Moderate Risk, Low Risk, and Safe provisions.</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-accent-500/20 text-accent-400 flex items-center justify-center flex-shrink-0 mt-0.5 text-xs font-bold">
                ✓
              </div>
              <div>
                <h2 className="text-sm font-semibold text-white">In-Memory Privacy Architecture</h2>
                <p className="text-xs text-primary-300">Session access tokens are held strictly in memory with secure httpOnly cookie rotation.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom: Legal Disclaimer */}
        <div className="relative z-10 pt-4 border-t border-primary-900 text-primary-400 text-xs leading-relaxed">
          <p>
            {t(
              'disclaimer.notice',
              'ClarifAI is an AI-powered legal assistance tool and is not a substitute for professional legal advice.'
            )}
          </p>
        </div>
      </div>

      {/* Right Content Panel */}
      <div className="flex-1 flex flex-col justify-between p-6 sm:p-10 lg:p-12">
        {/* Top Header inside Auth Form area */}
        <div className="flex items-center justify-between w-full max-w-md mx-auto">
          {/* Mobile Logo */}
          <Link
            to="/"
            className="lg:hidden flex items-center gap-2 text-primary-900 font-bold text-lg"
          >
            <div className="w-8 h-8 rounded-lg bg-primary-900 text-white flex items-center justify-center font-black text-sm">
              C
            </div>
            <span>Clarif<span className="text-accent-600">AI</span></span>
          </Link>

          <div className="ml-auto">
            <UILanguageSwitch />
          </div>
        </div>

        {/* Center: Auth Form Slot */}
        <div className="w-full max-w-md mx-auto my-auto py-8">
          <Outlet />
        </div>

        {/* Bottom Footer */}
        <div className="w-full max-w-md mx-auto text-center text-xs text-secondary-500 pt-4">
          <p>&copy; {new Date().getFullYear()} ClarifAI. All rights reserved.</p>
        </div>
      </div>

      {/* Global Notifications */}
      <ToastContainer />
    </div>
  );
};
