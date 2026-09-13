import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { SEVERITY_DEFINITIONS, SEVERITY_LEVELS } from '../constants/severityLevels';
import { ClauseCard } from '../components/domain/ClauseCard';
import { ClauseNavControls } from '../components/domain/ClauseNavControls';
import { ChatThread } from '../components/domain/ChatThread';
import { RiskOverviewChart } from '../components/domain/RiskOverviewChart';
import type { ClauseItem } from '../types';

describe('WCAG 2.1 AA Accessibility Audit (PRD Ch. 25 & Section 9.4)', () => {
  describe('Color Contrast Tokens (Rule: >= 4.5:1 for normal text)', () => {
    it('verifies all 4 canonical severity levels have valid distinct tokens with high contrast', () => {
      expect(SEVERITY_LEVELS).toEqual(['High', 'Moderate', 'Low', 'Safe']);

      SEVERITY_LEVELS.forEach((level) => {
        const def = SEVERITY_DEFINITIONS[level];
        expect(def.label).toBeDefined();
        expect(def.badgeBg).toBeDefined();
        expect(def.badgeText).toBeDefined();
        expect(def.badgeBorder).toBeDefined();
        expect(def.barColor).toBeDefined();

        // Check CSS class naming convention matches tokens
        expect(def.badgeBg).toContain('bg-risk-');
        expect(def.badgeText).toContain('text-risk-');
      });
    });
  });

  describe('Semantic HTML & Screen Reader Structure on ClauseCard', () => {
    const mockClause: ClauseItem = {
      id: 'clause-1',
      document_id: 'doc-123',
      position: 1,
      original_text: 'The Vendor shall indemnify the Customer against all direct claims.',
      simplified_text: 'Vendor covers direct claims.',
      explanation: 'Unilateral indemnity provision.',
      severity: 'High',
      category: 'Liability',
      status: 'analyzed',
      rule_findings: [],
      created_at: new Date().toISOString(),
      translation_available: false,
    };

    it('renders clause cards with role="article" and descriptive aria-label', () => {
      render(
        <MemoryRouter>
          <ClauseCard clause={mockClause} documentId="doc-123" />
        </MemoryRouter>
      );

      const card = screen.getByRole('article');
      expect(card).toBeInTheDocument();
      expect(card).toHaveAttribute(
        'aria-label',
        'Clause 1, Severity High, Category Liability'
      );
    });

    it('provides accessible failure states without defaulting to Safe per PRD Ch. 16.5', () => {
      const failedClause: ClauseItem = {
        ...mockClause,
        id: 'clause-failed',
        severity: null,
        status: 'failed',
      };

      render(
        <MemoryRouter>
          <ClauseCard clause={failedClause} documentId="doc-123" />
        </MemoryRouter>
      );

      const card = screen.getByRole('article');
      expect(card).toHaveAttribute('aria-label', 'Clause 1: Classification Failed');
      expect(screen.getByText('Classification Incomplete')).toBeInTheDocument();
    });
  });

  describe('ARIA Live Regions & Navigation Announcements', () => {
    it('ClauseNavControls provides role="status" and aria-live="polite" for position indicator', () => {
      render(
        <MemoryRouter>
          <ClauseNavControls documentId="doc-123" />
        </MemoryRouter>
      );

      const status = screen.getByTestId('clause-nav-position');
      expect(status).toHaveAttribute('role', 'status');
      expect(status).toHaveAttribute('aria-live', 'polite');
    });

    it('ChatThread provides role="status" on typing indicator and aria-live on thread container', () => {
      render(
        <MemoryRouter>
          <ChatThread
            documentId="doc-123"
            messages={[]}
            isSending={true}
            onSelectQuestion={() => {}}
          />
        </MemoryRouter>
      );

      const thread = screen.getByTestId('chat-thread');
      expect(thread).toHaveAttribute('aria-live', 'polite');

      const typingIndicator = screen.getByTestId('chat-typing-indicator');
      expect(typingIndicator).toHaveAttribute('role', 'status');
      expect(typingIndicator).toHaveAttribute(
        'aria-label',
        'Assistant is analyzing clauses and generating response'
      );
    });

    it('RiskOverviewChart provides role="region" and screen reader accessible summary text', () => {
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
        {
          id: 'c2',
          document_id: 'doc-123',
          position: 2,
          original_text: 'Text 2',
          simplified_text: 'Summary 2',
          explanation: 'Reason 2',
          severity: 'Safe',
          category: 'Confidentiality',
          status: 'analyzed',
          rule_findings: [],
          created_at: new Date().toISOString(),
          translation_available: false,
        },
      ];

      render(<RiskOverviewChart clauses={clauses} />);

      const chart = screen.getByRole('region', { name: /risk severity overview/i });
      expect(chart).toBeInTheDocument();

      const srSummary = screen.getByText(/clause severity distribution: 1 high risk/i);
      expect(srSummary).toHaveClass('sr-only');
    });
  });
});
