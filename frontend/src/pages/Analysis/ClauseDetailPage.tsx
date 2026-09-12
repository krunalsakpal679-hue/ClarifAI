import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';

export const ClauseDetailPage: React.FC = () => {
  const { id, clauseId } = useParams<{ id: string; clauseId: string }>();

  return (
    <div className="space-y-6">
      {/* Breadcrumb navigation */}
      <div className="flex items-center gap-2 text-xs text-secondary-500">
        <Link to="/dashboard" className="hover:underline">Dashboard</Link>
        <span>/</span>
        <Link to={`/documents/${id}`} className="hover:underline">Document Analysis</Link>
        <span>/</span>
        <span className="text-secondary-800 font-medium">Clause Detail</span>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-secondary-200">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="danger" size="sm">High Severity Risk</Badge>
            <span className="text-xs text-secondary-500 font-mono">Clause: {clauseId}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-primary-950">
            Section 14.2: Indemnification and Defense
          </h1>
        </div>
        <Link to={`/documents/${id}`}>
          <Button variant="outline" size="sm">
            &larr; Back to Document Analysis
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Original Legal Text */}
        <Card elevation="sm" className="border-secondary-300">
          <CardHeader>
            <CardTitle className="text-base font-medium text-secondary-800">
              Original Contract Text
            </CardTitle>
            <CardDescription>
              Exact verbatim extract parsed from source document.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="p-4 bg-secondary-50 rounded-lg border border-secondary-200 font-serif text-sm leading-relaxed text-secondary-900 select-text">
              "Customer shall defend, indemnify, and hold harmless Vendor, its affiliates, directors, and employees from and against any and all claims, liabilities, losses, damages, costs, and expenses (including reasonable attorneys' fees) arising out of or related to Customer's use of the Services or breach of this Agreement, without cap or limitation."
            </div>
          </CardContent>
        </Card>

        {/* Plain-English Simplification & Analysis */}
        <Card elevation="sm" className="border-secondary-300">
          <CardHeader>
            <CardTitle className="text-base font-medium text-primary-900">
              Plain-English Breakdown &amp; Risk Driver
            </CardTitle>
            <CardDescription>
              Simplified representation for non-lawyers and business decision-makers.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 bg-primary-50/50 rounded-lg border border-primary-200 text-sm text-primary-950 leading-relaxed">
              <p className="font-semibold text-xs text-primary-800 uppercase tracking-wider mb-1">What This Means</p>
              You agree to pay all legal defense expenses and damages for any lawsuit connected to your use of this software, with absolutely no maximum dollar limit, even if the vendor shares fault.
            </div>

            <div className="p-4 bg-red-50 rounded-lg border border-red-200 text-xs text-red-900 leading-relaxed space-y-1">
              <p className="font-semibold uppercase tracking-wider text-red-700">Risk Severity Rationale</p>
              <p>Uncapped unilateral indemnity exposes your organization to limitless financial liability for third-party claims.</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Suggested Negotiation Redline */}
      <Card elevation="sm" className="border-accent-200 bg-gradient-to-r from-accent-50/40 to-transparent">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Badge variant="warning" size="sm">Suggested Redline</Badge>
            <CardTitle className="text-base">Recommended Counter-Language</CardTitle>
          </div>
          <CardDescription>
            Use this balanced clause during contract negotiations to cap risk exposure.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="p-4 bg-white rounded-lg border border-secondary-200 text-sm font-mono text-secondary-800">
            "Each party shall defend and indemnify the other solely against third-party claims resulting directly from gross negligence or willful misconduct, subject always to the aggregate liability cap set forth in Section 8."
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
