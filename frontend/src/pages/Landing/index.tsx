import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../../store/authStore';
import { Button } from '../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';

export const LandingPage: React.FC = () => {
  const { t } = useTranslation();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  return (
    <div className="space-y-16 py-8">
      {/* Hero Section */}
      <section className="text-center max-w-3xl mx-auto space-y-6">
        <Badge variant="info" size="md" className="uppercase tracking-wider font-semibold">
          AI Legal Intelligence Platform
        </Badge>
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-serif font-bold text-primary-950 tracking-tight leading-tight">
          Clear Legal Insights.{' '}
          <span className="text-primary-700">Zero Guesswork.</span>
        </h1>
        <p className="text-lg text-secondary-600 leading-relaxed max-w-2xl mx-auto">
          {t('common.tagline', 'AI-Powered Legal Document Simplification & Risk Analysis')}
        </p>
        <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
          {isAuthenticated ? (
            <Link to="/dashboard">
              <Button size="lg" variant="primary">
                Go to Dashboard &rarr;
              </Button>
            </Link>
          ) : (
            <>
              <Link to="/signup">
                <Button size="lg" variant="primary">
                  Get Started Free &rarr;
                </Button>
              </Link>
              <Link to="/login">
                <Button size="lg" variant="outline">
                  Sign In
                </Button>
              </Link>
            </>
          )}
        </div>
      </section>

      {/* Feature Grid */}
      <section className="space-y-8">
        <div className="text-center max-w-xl mx-auto">
          <h2 className="text-2xl font-serif font-bold text-primary-900">
            Engineered for Contract Clarity
          </h2>
          <p className="text-secondary-600 text-sm mt-1">
            Every feature is designed with strict source-text grounding and defense-in-depth safety.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card elevation="sm" className="border-secondary-200">
            <CardHeader>
              <div className="w-10 h-10 rounded-lg bg-primary-100 text-primary-800 flex items-center justify-center font-bold mb-2">
                📄
              </div>
              <CardTitle className="text-base">Document Simplification</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-secondary-600 leading-relaxed">
                Translate legalese into accessible, plain-English summaries tailored to your preferred reading level.
              </p>
            </CardContent>
          </Card>

          <Card elevation="sm" className="border-secondary-200">
            <CardHeader>
              <div className="w-10 h-10 rounded-lg bg-amber-100 text-amber-800 flex items-center justify-center font-bold mb-2">
                ⚠️
              </div>
              <CardTitle className="text-base">Clause Risk Scoring</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-secondary-600 leading-relaxed">
                Identify indemnities, unilateral liabilities, and hidden pitfalls with 4-tier risk severity classification.
              </p>
            </CardContent>
          </Card>

          <Card elevation="sm" className="border-secondary-200">
            <CardHeader>
              <div className="w-10 h-10 rounded-lg bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold mb-2">
                ⚖️
              </div>
              <CardTitle className="text-base">Version Comparison</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-secondary-600 leading-relaxed">
                Diff contract revisions side-by-side with automated clause alignment and risk elevation alerts.
              </p>
            </CardContent>
          </Card>

          <Card elevation="sm" className="border-secondary-200">
            <CardHeader>
              <div className="w-10 h-10 rounded-lg bg-blue-100 text-blue-800 flex items-center justify-center font-bold mb-2">
                💬
              </div>
              <CardTitle className="text-base">Grounded Chatbot</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-secondary-600 leading-relaxed">
                Ask questions about your uploaded agreements and receive answers anchored with exact clause citations.
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Safety & Compliance Card */}
      <section>
        <Card elevation="md" className="bg-primary-950 text-white border-none p-8">
          <div className="max-w-2xl space-y-4">
            <Badge variant="outline" size="sm" className="border-accent-400 text-accent-300">
              Security & Compliance
            </Badge>
            <h2 className="text-2xl font-serif font-bold text-white">
              Enterprise Privacy by Architecture
            </h2>
            <p className="text-primary-200 text-sm leading-relaxed">
              Your sensitive legal documents never leak into open training pipelines. Authentication tokens are strictly held in memory with secure httpOnly cookie rotation, and document processing adheres strictly to isolated tenant controls.
            </p>
          </div>
        </Card>
      </section>
    </div>
  );
};
