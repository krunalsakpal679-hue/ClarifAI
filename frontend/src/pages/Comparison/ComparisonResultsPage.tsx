import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';

export const ComparisonResultsPage: React.FC = () => {
  const { idA, idB, comparisonId } = useParams<{ idA?: string; idB?: string; comparisonId?: string }>();

  const docALabel = idA || comparisonId?.split('_')[0] || 'Doc A';
  const docBLabel = idB || comparisonId?.split('_')[1] || 'Doc B';

  const diffItems = [
    {
      clause: 'Section 14: Indemnification',
      type: 'modified' as const,
      riskShift: 'Risk Increased (Moderate -> High)',
      textA: 'Each party shall indemnify the other up to $100,000 for direct breaches.',
      textB: 'Customer shall defend and hold harmless Vendor against all third-party claims without limitation.',
    },
    {
      clause: 'Section 9: Data Security & Audit Rights',
      type: 'deleted' as const,
      riskShift: 'Risk Increased (Protection Removed)',
      textA: 'Customer retains the right to audit Vendor security logs annually upon 14 days notice.',
      textB: '[Clause completely deleted in counterparty draft]',
    },
    {
      clause: 'Section 22: Arbitration & Governing Law',
      type: 'added' as const,
      riskShift: 'Neutral',
      textA: '[Not present in baseline]',
      textB: 'All disputes shall be settled by binding arbitration in Wilmington, Delaware.',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-secondary-200">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="warning" size="sm">2 High-Risk Discrepancies</Badge>
            <span className="text-xs text-secondary-500 font-mono">
              Comparing: {docALabel} vs {docBLabel}
            </span>
          </div>
          <h1 className="text-3xl font-serif font-bold text-primary-950">
            Comparison Results
          </h1>
        </div>
        <Link to="/compare">
          <Button variant="outline" size="sm">
            &larr; Configure New Comparison
          </Button>
        </Link>
      </div>

      {/* Comparison diff items */}
      <div className="space-y-4">
        {diffItems.map((item) => (
          <Card key={item.clause} elevation="sm" className="overflow-hidden">
            <CardHeader className="bg-secondary-50/60 py-3 px-6 border-b border-secondary-200 flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-sm font-semibold text-primary-900">{item.clause}</CardTitle>
                <CardDescription className="text-xs text-amber-700 font-medium">{item.riskShift}</CardDescription>
              </div>
              <Badge
                variant={
                  item.type === 'modified'
                    ? 'warning'
                    : item.type === 'deleted'
                    ? 'danger'
                    : 'info'
                }
                size="sm"
              >
                {item.type.toUpperCase()}
              </Badge>
            </CardHeader>
            <CardContent className="p-0">
              <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-secondary-200 text-xs font-mono">
                <div className="p-4 bg-red-50/20">
                  <p className="text-[10px] uppercase font-bold text-secondary-500 mb-1">
                    Baseline ({docALabel})
                  </p>
                  <p className="text-secondary-800 leading-relaxed">{item.textA}</p>
                </div>
                <div className="p-4 bg-emerald-50/20">
                  <p className="text-[10px] uppercase font-bold text-secondary-500 mb-1">
                    Counterparty ({docBLabel})
                  </p>
                  <p className="text-secondary-900 font-medium leading-relaxed">{item.textB}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};
