import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { Card, CardContent } from '../../components/ui/Card';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="max-w-md mx-auto py-16 text-center">
      <Card elevation="md" className="p-8">
        <CardContent className="space-y-4">
          <div className="text-5xl font-serif font-black text-primary-900">
            404
          </div>
          <h1 className="text-xl font-serif font-bold text-primary-950">
            Page Not Found
          </h1>
          <p className="text-xs text-secondary-600 leading-relaxed">
            The page, contract, or clause you are attempting to view does not exist or has been relocated.
          </p>
          <div className="pt-4 flex justify-center gap-3">
            <Link to="/">
              <Button variant="outline" size="sm">
                Return Home
              </Button>
            </Link>
            <Link to="/dashboard">
              <Button variant="primary" size="sm">
                Go to Dashboard
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
