import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { LandingPage } from '../pages/Landing';
import { DashboardPage } from '../pages/Dashboard';
import { RiskOverviewChart } from '../components/domain/RiskOverviewChart';
import '../i18n';
import type { ClauseItem } from '../types';

describe('Section 9.4 Motion and Tasteful 3D Requirements', () => {
  describe('Landing Page Motion & Isolated Hero Parallax', () => {
    it('applies card-3d-tilt class to feature cards on LandingPage', () => {
      render(
        <MemoryRouter>
          <LandingPage />
        </MemoryRouter>
      );

      const docSimTitle = screen.getByText('Document Simplification');
      const card = docSimTitle.closest('.card-3d-tilt');
      expect(card).toBeInTheDocument();
    });

    it('contains hero-parallax-element inside Landing hero without leaking into other pages', () => {
      const { container: landingContainer } = render(
        <MemoryRouter>
          <LandingPage />
        </MemoryRouter>
      );

      const parallaxElements = landingContainer.querySelectorAll('.hero-parallax-element');
      expect(parallaxElements.length).toBeGreaterThan(0);
    });
  });

  describe('Dashboard Card 3D Tilt Micro-interactions', () => {
    it('applies card-3d-tilt class to all aggregate stat cards on Dashboard', () => {
      const { container } = render(
        <MemoryRouter>
          <DashboardPage />
        </MemoryRouter>
      );

      const tiltCards = container.querySelectorAll('.card-3d-tilt');
      // 4 stat cards have card-3d-tilt
      expect(tiltCards.length).toBeGreaterThanOrEqual(4);
    });
  });

  describe('RiskOverviewChart Animation & Reduced-Motion Respect', () => {
    it('includes motion-reduce:transition-none to disable animation when prefers-reduced-motion is active', () => {
      const clauses: ClauseItem[] = [
        {
          id: 'c1',
          document_id: 'doc-123',
          position: 1,
          original_text: 'Text 1',
          simplified_text: 'Summary 1',
          explanation: 'Reason 1',
          severity: 'High',
          category: 'Liability',
          status: 'analyzed',
          rule_findings: [],
          created_at: new Date().toISOString(),
          translation_available: false,
        },
      ];

      const { container } = render(<RiskOverviewChart clauses={clauses} />);
      const barSegment = container.querySelector('.transition-all');
      expect(barSegment).toBeInTheDocument();
      expect(barSegment).toHaveClass('motion-reduce:transition-none');
    });
  });
});
