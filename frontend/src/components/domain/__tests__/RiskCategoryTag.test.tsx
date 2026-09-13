import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { RiskCategoryTag } from '../RiskCategoryTag';
import { RISK_CATEGORIES } from '../../../constants/riskCategories';

describe('RiskCategoryTag Component (components/domain/RiskCategoryTag)', () => {
  it('renders each of the approved 8 PRD categories accurately', () => {
    RISK_CATEGORIES.forEach((cat) => {
      const { unmount } = render(<RiskCategoryTag category={cat.id} />);
      expect(screen.getByText(cat.label)).toBeInTheDocument();
      unmount();
    });
  });

  it('renders Renewal category rather than Auto-renewal', () => {
    render(<RiskCategoryTag category="Renewal" />);
    expect(screen.getByText('Renewal')).toBeInTheDocument();
    expect(screen.queryByText('Auto-renewal')).not.toBeInTheDocument();
  });

  it('renders fallback for unclassified category', () => {
    render(<RiskCategoryTag category={null} />);
    expect(screen.getByText('General / Unclassified')).toBeInTheDocument();
  });
});
