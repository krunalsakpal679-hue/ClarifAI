import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';

export const ComparisonSetupPage: React.FC = () => {
  const navigate = useNavigate();
  const [docA, setDocA] = useState('doc-msa-01');
  const [docB, setDocB] = useState('doc-nda-02');

  const handleCompare = (e: React.FormEvent) => {
    e.preventDefault();
    if (!docA || !docB) return;
    navigate(`/compare/${docA}/${docB}`);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="text-center space-y-2">
        <Badge variant="info" size="sm" className="uppercase tracking-wider">
          Contract Redlining
        </Badge>
        <h1 className="text-3xl font-serif font-bold text-primary-950">
          Compare Legal Documents
        </h1>
        <p className="text-sm text-secondary-600">
          Select two document versions to compare clause changes, additions, deletions, and risk level shifts side by side.
        </p>
      </div>

      <Card elevation="sm">
        <CardHeader>
          <CardTitle className="text-lg">Comparison Configuration</CardTitle>
          <CardDescription>
            Choose a baseline contract and a counter-party or revised draft.
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleCompare}>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Document A Selector */}
              <div className="space-y-3 p-4 rounded-xl border border-secondary-200 bg-secondary-50/50">
                <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-primary-100 text-primary-800">
                  Document A (Baseline)
                </span>
                <label className="block text-xs font-semibold text-secondary-700">
                  Select Base Contract
                </label>
                <select
                  value={docA}
                  onChange={(e) => setDocA(e.target.value)}
                  className="w-full text-sm rounded-lg border border-secondary-300 bg-white p-2.5 focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="doc-msa-01">MSA - Standard Corporate Draft v1</option>
                  <option value="doc-nda-02">Mutual NDA - Standard 2026</option>
                  <option value="doc-sla-03">Cloud SLA - Provider Baseline</option>
                </select>
                <p className="text-[11px] text-secondary-500">Serves as the reference point for clause alignment.</p>
              </div>

              {/* Document B Selector */}
              <div className="space-y-3 p-4 rounded-xl border border-secondary-200 bg-secondary-50/50">
                <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-accent-100 text-accent-800">
                  Document B (Counter-Party / Revised)
                </span>
                <label className="block text-xs font-semibold text-secondary-700">
                  Select Comparison Target
                </label>
                <select
                  value={docB}
                  onChange={(e) => setDocB(e.target.value)}
                  className="w-full text-sm rounded-lg border border-secondary-300 bg-white p-2.5 focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="doc-nda-02">Mutual NDA - Standard 2026</option>
                  <option value="doc-msa-01">MSA - Standard Corporate Draft v1</option>
                  <option value="doc-vendor-redline">Vendor Redline Draft v2 (Revised)</option>
                </select>
                <p className="text-[11px] text-secondary-500">The counterparty revision or updated contract.</p>
              </div>
            </div>
          </CardContent>

          <CardFooter className="flex justify-between items-center pt-2">
            <Button
              type="button"
              variant="outline"
              size="md"
              onClick={() => navigate('/dashboard')}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="md"
            >
              Run Version Comparison &rarr;
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
};
