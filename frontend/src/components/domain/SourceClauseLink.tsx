import React from 'react';
import { Link } from 'react-router-dom';
import { FileText, ArrowUpRight } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface SourceClauseLinkProps {
  documentId: string;
  clauseId: string;
  className?: string;
}

export const SourceClauseLink: React.FC<SourceClauseLinkProps> = ({
  documentId,
  clauseId,
  className,
}) => {
  // Format clause ID for friendly display (e.g., 'clause-101' -> 'Clause #101' or 'Clause #1')
  const match = clauseId.match(/\d+/);
  const displayLabel = match ? `Clause #${match[0]}` : clauseId;

  return (
    <Link
      to={`/documents/${documentId}/clauses/${clauseId}`}
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium font-mono',
        'bg-primary-50 text-primary-800 border border-primary-200 hover:bg-primary-100 hover:border-primary-300',
        'transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-1',
        className
      )}
      aria-label={`View referenced ${displayLabel}`}
      data-testid={`source-clause-link-${clauseId}`}
    >
      <FileText className="w-3.5 h-3.5 text-primary-600 shrink-0" aria-hidden="true" />
      <span>{displayLabel}</span>
      <ArrowUpRight className="w-3 h-3 text-primary-500 shrink-0" aria-hidden="true" />
    </Link>
  );
};
