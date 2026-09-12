import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { Spinner } from '../../components/ui/Spinner';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card';

export const ProcessingPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [step, setStep] = useState(1);

  useEffect(() => {
    const timer1 = setTimeout(() => setStep(2), 1200);
    const timer2 = setTimeout(() => setStep(3), 2400);
    const timer3 = setTimeout(() => setStep(4), 3600);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
    };
  }, []);

  const steps = [
    { title: 'Text Extraction & Parsing', desc: 'Running OCR and document structure extraction' },
    { title: 'Clause Segmentation', desc: 'Identifying contract clauses and numbered headings' },
    { title: 'AI Plain-Language Simplification', desc: 'Generating plain-English summaries grounded in source text' },
    { title: 'Clause Risk Classification', desc: 'Scoring liability, indemnification, and risk severity' },
  ];

  return (
    <div className="max-w-xl mx-auto space-y-8 py-8 text-center">
      <div className="space-y-2">
        <h1 className="text-3xl font-serif font-bold text-primary-950">
          Analyzing Document
        </h1>
        <p className="text-xs text-secondary-500 font-mono">
          Document ID: {id || 'doc-preview'}
        </p>
      </div>

      <Card elevation="md" className="p-6">
        <CardHeader className="pb-6">
          <div className="flex justify-center mb-4">
            <Spinner size="lg" variant="primary" />
          </div>
          <CardTitle className="text-lg">Processing Legal Pipeline</CardTitle>
          <CardDescription>
            Real-time pipeline orchestration handled via backend tasks and WebSocket progress events in Phase 04.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4 text-left">
          {steps.map((s, index) => {
            const stepNum = index + 1;
            const isDone = step > stepNum;
            const isCurrent = step === stepNum;

            return (
              <div
                key={s.title}
                className={`flex items-start gap-3 p-3 rounded-lg border transition-colors ${
                  isCurrent
                    ? 'border-primary-500 bg-primary-50/50'
                    : isDone
                    ? 'border-emerald-200 bg-emerald-50/30'
                    : 'border-secondary-100 opacity-60'
                }`}
              >
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5 ${
                    isDone
                      ? 'bg-emerald-600 text-white'
                      : isCurrent
                      ? 'bg-primary-600 text-white animate-pulse'
                      : 'bg-secondary-200 text-secondary-600'
                  }`}
                >
                  {isDone ? '✓' : stepNum}
                </div>
                <div>
                  <p className="text-sm font-semibold text-secondary-900">{s.title}</p>
                  <p className="text-xs text-secondary-500">{s.desc}</p>
                </div>
              </div>
            );
          })}
        </CardContent>

        <div className="pt-6 border-t border-secondary-200 mt-6 flex justify-center">
          <Button
            variant="primary"
            size="md"
            onClick={() => navigate(`/documents/${id}`)}
          >
            View Analysis Results &rarr;
          </Button>
        </div>
      </Card>
    </div>
  );
};
