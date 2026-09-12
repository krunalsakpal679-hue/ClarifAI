import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';

export const AnalysisResultsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  const clauses = [
    {
      id: 'clause-101',
      title: 'Section 14.2: Indemnification and Defense',
      snippet: 'Customer agrees to defend, indemnify, and hold harmless Vendor against any and all claims...',
      risk: 'high' as const,
      riskLabel: 'High Risk',
    },
    {
      id: 'clause-102',
      title: 'Section 8.1: Limitation of Liability',
      snippet: 'Neither party shall be liable for indirect, incidental, special or consequential damages...',
      risk: 'moderate' as const,
      riskLabel: 'Moderate Risk',
    },
    {
      id: 'clause-103',
      title: 'Section 4.3: Term and Termination for Cause',
      snippet: 'Either party may terminate this Agreement upon thirty (30) days written notice...',
      risk: 'low' as const,
      riskLabel: 'Low Risk',
    },
    {
      id: 'clause-104',
      title: 'Section 1.1: Definitions and Interpretation',
      snippet: 'Capitalized terms used in this Agreement shall have the meanings specified herein...',
      risk: 'safe' as const,
      riskLabel: 'Safe',
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header and Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-secondary-200">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="danger" size="sm">High Overall Risk</Badge>
            <span className="text-xs text-secondary-500 font-mono">ID: {id}</span>
          </div>
          <h1 className="text-3xl font-serif font-bold text-primary-950">
            Master Services Agreement Analysis
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <Link to={`/documents/${id}/chat`}>
            <Button variant="primary" size="md">
              💬 Chat with Document
            </Button>
          </Link>
          <Link to="/compare">
            <Button variant="outline" size="md">
              Compare with Another Doc
            </Button>
          </Link>
        </div>
      </div>

      {/* Summary Card */}
      <Card elevation="sm">
        <CardHeader>
          <CardTitle className="text-lg">Executive Plain-Language Summary</CardTitle>
          <CardDescription>
            Generated using legal-domain AI simplification models with strict source citation.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-secondary-700 leading-relaxed">
            This agreement governs commercial enterprise services provided by the vendor. The contract heavily favors the vendor in liability apportionment, requiring uncapped indemnification from the customer while strictly limiting vendor damages to the fees paid over the previous 3 months.
          </p>
        </CardContent>
      </Card>

      {/* Clause Breakdown Section */}
      <div className="space-y-4">
        <h2 className="text-xl font-serif font-bold text-primary-900">
          Extracted Clauses &amp; Risk Assessments ({clauses.length})
        </h2>

        <div className="space-y-3">
          {clauses.map((clause) => (
            <Card key={clause.id} elevation="sm" className="hover:border-primary-300 transition-colors">
              <CardContent className="p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="space-y-1 max-w-2xl">
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-semibold text-primary-900">{clause.title}</h3>
                    <Badge
                      variant={
                        clause.risk === 'high'
                          ? 'danger'
                          : clause.risk === 'moderate'
                          ? 'warning'
                          : clause.risk === 'low'
                          ? 'info'
                          : 'success'
                      }
                      size="sm"
                    >
                      {clause.riskLabel}
                    </Badge>
                  </div>
                  <p className="text-xs text-secondary-600 font-mono line-clamp-1 bg-secondary-50 p-1.5 rounded">
                    "{clause.snippet}"
                  </p>
                </div>

                <div className="flex-shrink-0">
                  <Link to={`/documents/${id}/clauses/${clause.id}`}>
                    <Button variant="outline" size="sm">
                      Inspect Clause Details &rarr;
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};
