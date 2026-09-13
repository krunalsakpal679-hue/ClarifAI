import React, { useEffect, useState } from 'react';
import { cn } from '../../utils/cn';
import {
  type SeverityLevel,
  SEVERITY_LEVELS,
  SEVERITY_DEFINITIONS,
  normalizeSeverity,
} from '../../constants/severityLevels';
import type { ClauseItem } from '../../types';

export interface RiskOverviewChartProps {
  clauses: ClauseItem[];
  className?: string;
}

export const RiskOverviewChart: React.FC<RiskOverviewChartProps> = ({
  clauses,
  className,
}) => {
  const [animated, setAnimated] = useState(false);

  // Trigger building-in animation on mount (PRD Ch. 22.0)
  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimated(true);
    }, 50);
    return () => clearTimeout(timer);
  }, []);

  // Compute clause counts across the 4 canonical severities
  const counts: Record<SeverityLevel, number> = {
    High: 0,
    Moderate: 0,
    Low: 0,
    Safe: 0,
  };

  let unclassifiedCount = 0;

  clauses.forEach((clause) => {
    const normalized = normalizeSeverity(clause.severity);
    if (normalized && clause.status !== 'failed') {
      counts[normalized]++;
    } else {
      unclassifiedCount++;
    }
  });

  const totalClauses = clauses.length;

  const accessibleSummary = `Clause severity distribution: ${counts.High} high risk, ${counts.Moderate} moderate risk, ${counts.Low} low risk, ${counts.Safe} safe${
    unclassifiedCount > 0 ? `, ${unclassifiedCount} unclassified` : ''
  }. Total ${totalClauses} clauses.`;

  return (
    <div
      role="region"
      aria-label="Risk Severity Overview"
      className={cn(
        'p-5 sm:p-6 rounded-xl border border-secondary-200 bg-white shadow-sm space-y-5',
        className
      )}
      data-testid="risk-overview-chart"
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold text-primary-950 uppercase tracking-wider">
            Risk Severity Breakdown
          </h2>
          <p className="text-xs text-secondary-500 mt-0.5">
            Distribution of identified clause risks across legal severity tiers.
          </p>
        </div>

        <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-secondary-100 text-secondary-800 self-start sm:self-auto">
          {totalClauses} {totalClauses === 1 ? 'Clause' : 'Clauses'} Analyzed
        </span>
      </div>

      {/* Screen reader equivalent */}
      <p className="sr-only">{accessibleSummary}</p>

      {/* Proportional Segmented Progress Bar */}
      <div
        aria-hidden="true"
        className="w-full h-3 rounded-full bg-secondary-100 flex overflow-hidden p-0.5 gap-0.5"
      >
        {totalClauses > 0 ? (
          SEVERITY_LEVELS.map((level) => {
            const count = counts[level];
            const percent = totalClauses > 0 ? (count / totalClauses) * 100 : 0;
            const def = SEVERITY_DEFINITIONS[level];

            if (count === 0) return null;

            return (
              <div
                key={level}
                style={{
                  width: animated ? `${percent}%` : '0%',
                }}
                className={cn(
                  'h-full rounded-sm transition-all duration-700 ease-out motion-reduce:transition-none',
                  def.barColor
                )}
                title={`${def.label}: ${count} clauses`}
              />
            );
          })
        ) : (
          <div className="w-full h-full bg-secondary-200 rounded-sm" />
        )}
      </div>

      {/* Breakdown Legend Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
        {SEVERITY_LEVELS.map((level) => {
          const count = counts[level];
          const def = SEVERITY_DEFINITIONS[level];

          return (
            <div
              key={level}
              data-testid={`risk-card-${level}`}
              className={cn(
                'p-3 rounded-lg border flex flex-col justify-between transition-all',
                def.badgeBg,
                def.badgeBorder
              )}
            >
              <div className="flex items-center justify-between gap-1 mb-1">
                <span className={cn('text-xs font-bold uppercase tracking-wider', def.badgeText)}>
                  {def.label}
                </span>
                <span
                  className={cn(
                    'w-2 h-2 rounded-full shrink-0',
                    def.barColor
                  )}
                  aria-hidden="true"
                />
              </div>

              <div className="flex items-baseline gap-1">
                <span className="text-2xl font-bold font-serif text-primary-950">
                  {count}
                </span>
                <span className="text-xs text-secondary-500 font-medium">
                  {count === 1 ? 'clause' : 'clauses'}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default RiskOverviewChart;
