import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../../store/authStore';
import { Button } from '../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';

export const DashboardPage: React.FC = () => {
  const { t } = useTranslation();
  const user = useAuthStore((state) => state.user);

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-secondary-200">
        <div>
          <h1 className="text-3xl font-serif font-bold text-primary-950">
            Welcome back, {user?.fullName || 'Counsel'}
          </h1>
          <p className="text-secondary-600 text-sm mt-1">
            Review document simplification summaries, inspect clause risk flags, and compare contract versions.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/upload">
            <Button variant="primary" size="md">
              + {t('common.actions.upload', 'Upload Document')}
            </Button>
          </Link>
          <Link to="/compare">
            <Button variant="outline" size="md">
              {t('common.actions.compare', 'Compare Documents')}
            </Button>
          </Link>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <Card elevation="sm">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs uppercase font-medium">Documents Analyzed</CardDescription>
            <CardTitle className="text-3xl font-serif text-primary-900">12</CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-xs text-secondary-500">Across 3 legal document categories</span>
          </CardContent>
        </Card>

        <Card elevation="sm">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs uppercase font-medium">Flagged High-Risk Clauses</CardDescription>
            <CardTitle className="text-3xl font-serif text-red-600">7</CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-xs text-red-600 font-medium">Requires immediate legal counsel review</span>
          </CardContent>
        </Card>

        <Card elevation="sm">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs uppercase font-medium">Comparisons Executed</CardDescription>
            <CardTitle className="text-3xl font-serif text-primary-900">4</CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-xs text-secondary-500">Side-by-side clause alignment</span>
          </CardContent>
        </Card>
      </div>

      {/* Recent Documents Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-serif font-bold text-primary-900">Recent Documents</h2>
          <Link to="/history" className="text-sm text-primary-700 font-medium hover:underline">
            View all history &rarr;
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card elevation="sm" className="hover:border-primary-300 transition-colors">
            <CardHeader className="flex flex-row items-start justify-between">
              <div>
                <CardTitle className="text-base">Master Services Agreement (MSA) - Vendor A</CardTitle>
                <CardDescription className="text-xs">Uploaded 2 hours ago &bull; 24 Pages</CardDescription>
              </div>
              <Badge variant="danger" size="sm">High Risk</Badge>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-xs text-secondary-600 line-clamp-2">
                Contains uncapped indemnification obligations and unilateral termination provisions in Section 14.
              </p>
              <div className="flex items-center gap-2 pt-2 border-t border-secondary-100">
                <Link to="/documents/doc-msa-01">
                  <Button variant="outline" size="sm">
                    View Analysis &rarr;
                  </Button>
                </Link>
                <Link to="/documents/doc-msa-01/chat">
                  <Button variant="ghost" size="sm">
                    Chat with Doc
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>

          <Card elevation="sm" className="hover:border-primary-300 transition-colors">
            <CardHeader className="flex flex-row items-start justify-between">
              <div>
                <CardTitle className="text-base">Non-Disclosure Agreement (NDA) - Mutual</CardTitle>
                <CardDescription className="text-xs">Uploaded Yesterday &bull; 6 Pages</CardDescription>
              </div>
              <Badge variant="success" size="sm">Low Risk</Badge>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-xs text-secondary-600 line-clamp-2">
                Standard mutual NDA clauses with standard 3-year survival term and standard confidentiality exclusions.
              </p>
              <div className="flex items-center gap-2 pt-2 border-t border-secondary-100">
                <Link to="/documents/doc-nda-02">
                  <Button variant="outline" size="sm">
                    View Analysis &rarr;
                  </Button>
                </Link>
                <Link to="/documents/doc-nda-02/chat">
                  <Button variant="ghost" size="sm">
                    Chat with Doc
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
