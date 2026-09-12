import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ComparisonConfidenceIndicator } from '../ComparisonConfidenceIndicator';
import { ComparisonClausePair } from '../ComparisonClausePair';
import { ComparisonResultGroup } from '../ComparisonResultGroup';
import type { ComparisonClauseItem } from '../../../types/comparison';

describe('Comparison Domain Components (components/domain/)', () => {
  describe('ComparisonConfidenceIndicator (PRD Ch. 18.3)', () => {
    it('renders prominent alert with role="alert" and aria-live="polite"', () => {
      render(<ComparisonConfidenceIndicator />);

      const alert = screen.getByRole('alert');
      expect(alert).toBeInTheDocument();
      expect(alert).toHaveAttribute('aria-live', 'polite');
      expect(
        screen.getByText(/Low Alignment Confidence Notice/i)
      ).toBeInTheDocument();
      expect(screen.getByText(/clause ratio exceeding 2\.0:1/i)).toBeInTheDocument();
    });

    it('displays custom warning text when provided', () => {
      const customWarning = 'Custom alignment warning for test documents.';
      render(<ComparisonConfidenceIndicator warning={customWarning} />);

      expect(screen.getByText(customWarning)).toBeInTheDocument();
    });
  });

  describe('ComparisonClausePair', () => {
    const changedItem: ComparisonClauseItem = {
      id: 'diff-1',
      category: 'changed',
      base_clause_id: 'clause-101',
      target_clause_id: 'clause-201',
      text_a: 'Mutual indemnification capped at $500,000.',
      text_b: 'Uncapped unilateral customer indemnification.',
      similarity_score: 0.72,
      difference_explanation: 'Indemnity altered from mutual to unilateral uncapped.',
      position_a: 14,
      position_b: 14,
    };

    it('renders changed clause with side-by-side texts, explanation, and match score', () => {
      render(
        <ComparisonClausePair
          item={changedItem}
          docALabel="Doc A (Base)"
          docBLabel="Doc B (Target)"
        />
      );

      expect(screen.getByText(/Changed Clause/i)).toBeInTheDocument();
      expect(screen.getByText('72% match')).toBeInTheDocument();
      expect(screen.getByText(/Change Summary:/i)).toBeInTheDocument();
      expect(
        screen.getByText('Indemnity altered from mutual to unilateral uncapped.')
      ).toBeInTheDocument();

      // Check text in both sides
      expect(screen.getByText('Mutual indemnification capped at $500,000.')).toBeInTheDocument();
      expect(screen.getByText('Uncapped unilateral customer indemnification.')).toBeInTheDocument();

      // Check labels
      expect(screen.getByText('Doc A (Base)')).toBeInTheDocument();
      expect(screen.getByText('Doc B (Target)')).toBeInTheDocument();

      // Check screen-reader accessible announcement
      expect(screen.getByText(/Classification: changed/i)).toBeInTheDocument();
    });

    it('renders matched clause with identical match badge', () => {
      const matchedItem: ComparisonClauseItem = {
        id: 'diff-2',
        category: 'matched',
        base_clause_id: 'clause-105',
        target_clause_id: 'clause-205',
        text_a: 'Standard confidentiality clause.',
        text_b: 'Standard confidentiality clause.',
        similarity_score: 1.0,
      };

      render(<ComparisonClausePair item={matchedItem} />);

      expect(screen.getByText(/Identical \/ Matched/i)).toBeInTheDocument();
      expect(screen.getByText('100% match')).toBeInTheDocument();
      expect(screen.getByText(/Classification: matched/i)).toBeInTheDocument();
    });

    it('renders deleted clause with deleted in revised badge and missing text placeholder', () => {
      const deletedItem: ComparisonClauseItem = {
        id: 'diff-3',
        category: 'missing',
        base_clause_id: 'clause-107',
        target_clause_id: null,
        text_a: 'Security audit rights clause.',
        text_b: null,
        similarity_score: 0.0,
      };

      render(<ComparisonClausePair item={deletedItem} />);

      expect(screen.getByText(/Deleted in Revised/i)).toBeInTheDocument();
      expect(
        screen.getByText(/Clause completely deleted in counterparty draft/i)
      ).toBeInTheDocument();
    });

    it('renders added clause with added in revised badge and baseline placeholder', () => {
      const addedItem: ComparisonClauseItem = {
        id: 'diff-4',
        category: 'missing',
        base_clause_id: null,
        target_clause_id: 'clause-208',
        text_a: null,
        text_b: 'Arbitration and class action waiver clause.',
        similarity_score: 0.0,
      };

      render(<ComparisonClausePair item={addedItem} />);

      expect(screen.getByText('Added in Revised')).toBeInTheDocument();
      expect(
        screen.getByText(/Clause was not present in baseline contract/i)
      ).toBeInTheDocument();
    });
  });

  describe('ComparisonResultGroup', () => {
    it('renders group header with category title, count badge, and items', () => {
      const items: ComparisonClauseItem[] = [
        {
          id: 'diff-1',
          category: 'changed',
          text_a: 'Clause A text',
          text_b: 'Clause B text',
          similarity_score: 0.8,
        },
      ];

      render(<ComparisonResultGroup category="changed" items={items} />);

      expect(screen.getByRole('heading', { name: /Changed Clauses/i })).toBeInTheDocument();
      expect(screen.getByText('1 clause')).toBeInTheDocument();
      expect(screen.getByTestId('comparison-group-changed')).toBeInTheDocument();
    });

    it('renders contextual empty state when items list is empty', () => {
      render(<ComparisonResultGroup category="missing" items={[]} />);

      expect(
        screen.getByText(/No added or deleted clauses detected between these drafts/i)
      ).toBeInTheDocument();
    });
  });
});
