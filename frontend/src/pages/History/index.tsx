import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';

export const HistoryPage: React.FC = () => {
  const documents = [
    {
      id: 'doc-msa-01',
      title: 'Master Services Agreement (MSA) - Vendor A',
      type: 'MSA',
      date: '2026-09-12',
      risk: 'high' as const,
      status: 'analyzed',
    },
    {
      id: 'doc-nda-02',
      title: 'Non-Disclosure Agreement (NDA) - Mutual',
      type: 'NDA',
      date: '2026-09-11',
      risk: 'low' as const,
      status: 'analyzed',
    },
    {
      id: 'doc-sla-03',
      title: 'Cloud Infrastructure Service Level Agreement',
      type: 'SLA',
      date: '2026-09-08',
      risk: 'moderate' as const,
      status: 'analyzed',
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-secondary-200">
        <div>
          <h1 className="text-3xl font-serif font-bold text-primary-950">Document History</h1>
          <p className="text-secondary-600 text-sm mt-1">
            Access and manage previously simplified and analyzed legal contracts.
          </p>
        </div>
        <Link to="/upload">
          <Button variant="primary" size="md">
            + Upload New Document
          </Button>
        </Link>
      </div>

      <Card elevation="sm">
        <CardHeader>
          <CardTitle className="text-lg">Analyzed Documents Repository</CardTitle>
          <CardDescription>
            Showing 3 contracts stored in your workspace.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm" role="table" aria-label="Document History">
              <thead className="text-xs uppercase bg-secondary-50 text-secondary-600 border-b border-secondary-200">
                <tr>
                  <th scope="col" className="px-4 py-3 font-semibold">Document Title</th>
                  <th scope="col" className="px-4 py-3 font-semibold">Category</th>
                  <th scope="col" className="px-4 py-3 font-semibold">Processed Date</th>
                  <th scope="col" className="px-4 py-3 font-semibold">Risk Rating</th>
                  <th scope="col" className="px-4 py-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-secondary-200">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-secondary-50/60 transition-colors">
                    <td className="px-4 py-3.5 font-medium text-primary-900">
                      <Link to={`/documents/${doc.id}`} className="hover:underline">
                        {doc.title}
                      </Link>
                    </td>
                    <td className="px-4 py-3.5 text-secondary-600">
                      <Badge variant="outline" size="sm">{doc.type}</Badge>
                    </td>
                    <td className="px-4 py-3.5 text-secondary-600 text-xs">
                      {doc.date}
                    </td>
                    <td className="px-4 py-3.5">
                      <Badge
                        variant={
                          doc.risk === 'high'
                            ? 'danger'
                            : doc.risk === 'moderate'
                            ? 'warning'
                            : 'success'
                        }
                        size="sm"
                      >
                        {doc.risk === 'high' ? 'High Risk' : doc.risk === 'moderate' ? 'Moderate Risk' : 'Low Risk'}
                      </Badge>
                    </td>
                    <td className="px-4 py-3.5 text-right space-x-2">
                      <Link to={`/documents/${doc.id}`}>
                        <Button variant="outline" size="sm">Analysis</Button>
                      </Link>
                      <Link to={`/documents/${doc.id}/chat`}>
                        <Button variant="ghost" size="sm">Chat</Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
