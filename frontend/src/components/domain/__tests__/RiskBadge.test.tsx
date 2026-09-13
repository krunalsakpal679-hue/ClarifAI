import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { RiskBadge } from '../RiskBadge';

describe('RiskBadge Component (components/domain/RiskBadge)', () => {
  it('renders High Risk badge with icon and label', () => {
    render(<RiskBadge severity="High" />);
    const badge = screen.getByRole('status', { name: /Severity: High Risk/i });
    expect(badge).toBeInTheDocument();
    expect(screen.getByText('High Risk')).toBeInTheDocument();
    expect(badge).toHaveClass('bg-risk-high-bg');
    expect(badge).toHaveClass('text-risk-high-text');
  });

  it('renders Moderate Risk badge with icon and label', () => {
    render(<RiskBadge severity="Moderate" />);
    const badge = screen.getByRole('status', { name: /Severity: Moderate Risk/i });
    expect(badge).toBeInTheDocument();
    expect(screen.getByText('Moderate Risk')).toBeInTheDocument();
    expect(badge).toHaveClass('bg-risk-moderate-bg');
    expect(badge).toHaveClass('text-risk-moderate-text');
  });

  it('renders Low Risk badge with icon and label', () => {
    render(<RiskBadge severity="Low" />);
    const badge = screen.getByRole('status', { name: /Severity: Low Risk/i });
    expect(badge).toBeInTheDocument();
    expect(screen.getByText('Low Risk')).toBeInTheDocument();
    expect(badge).toHaveClass('bg-risk-low-bg');
    expect(badge).toHaveClass('text-risk-low-text');
  });

  it('renders Safe badge with icon and label', () => {
    render(<RiskBadge severity="Safe" />);
    const badge = screen.getByRole('status', { name: /Severity: Safe/i });
    expect(badge).toBeInTheDocument();
    expect(screen.getByText('Safe')).toBeInTheDocument();
    expect(badge).toHaveClass('bg-risk-safe-bg');
    expect(badge).toHaveClass('text-risk-safe-text');
  });

  it('normalizes lowercase or uppercase severity inputs', () => {
    render(<RiskBadge severity="high" />);
    expect(screen.getByText('High Risk')).toBeInTheDocument();
  });

  it('renders Unclassified fallback when severity is null or unrecognized', () => {
    render(<RiskBadge severity={null} />);
    const badge = screen.getByRole('status', { name: /Severity: Unclassified/i });
    expect(badge).toBeInTheDocument();
    expect(screen.getByText('Unclassified')).toBeInTheDocument();
  });
});
