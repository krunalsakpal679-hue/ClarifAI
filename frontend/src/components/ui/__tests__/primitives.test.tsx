import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import {
  Button,
  Input,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  Badge,
  Spinner,
  SkeletonBlock,
} from '../index';

describe('Design System Primitives (components/ui/)', () => {
  describe('Button', () => {
    it('renders with children and handles click events', () => {
      const handleClick = vi.fn();
      render(<Button onClick={handleClick}>Click Me</Button>);

      const button = screen.getByRole('button', { name: /click me/i });
      expect(button).toBeInTheDocument();
      fireEvent.click(button);
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('renders loading spinner and disables button when isLoading is true', () => {
      render(<Button isLoading>Submitting</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
      expect(button).toHaveAttribute('aria-busy', 'true');
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('applies correct variant styles', () => {
      const { rerender } = render(<Button variant="primary">Primary</Button>);
      expect(screen.getByRole('button')).toHaveClass('bg-accent');

      rerender(<Button variant="destructive">Delete</Button>);
      expect(screen.getByRole('button')).toHaveClass('bg-risk-high');
    });
  });

  describe('Input', () => {
    it('renders label, input, and helper text', () => {
      render(
        <Input
          label="Contract Title"
          helperText="Enter contract title"
          placeholder="e.g. NDA"
        />
      );

      expect(screen.getByLabelText(/contract title/i)).toBeInTheDocument();
      expect(screen.getByText(/enter contract title/i)).toBeInTheDocument();
    });

    it('renders error message and aria-invalid when error is present', () => {
      render(<Input label="Email" error="Invalid email address" />);
      const input = screen.getByLabelText(/email/i);
      expect(input).toHaveAttribute('aria-invalid', 'true');
      expect(screen.getByRole('alert')).toHaveTextContent(/invalid email address/i);
    });
  });

  describe('Card', () => {
    it('renders card header, title, description, and content', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Clause Analysis</CardTitle>
            <CardDescription>Overview of analyzed terms</CardDescription>
          </CardHeader>
          <CardContent>Body content goes here</CardContent>
          <CardFooter>Footer actions</CardFooter>
        </Card>
      );

      expect(screen.getByText('Clause Analysis')).toBeInTheDocument();
      expect(screen.getByText('Overview of analyzed terms')).toBeInTheDocument();
      expect(screen.getByText('Body content goes here')).toBeInTheDocument();
      expect(screen.getByText('Footer actions')).toBeInTheDocument();
    });
  });

  describe('Badge', () => {
    it('renders risk severity badges with icon and text (WCAG rule)', () => {
      render(<Badge severity="HIGH">High Risk</Badge>);
      const badge = screen.getByText('High Risk');
      expect(badge).toBeInTheDocument();
      expect(badge.parentElement).toHaveClass('text-risk-high');
    });

    it('renders processing status badges', () => {
      render(<Badge status="COMPLETED" />);
      expect(screen.getByText('Complete')).toBeInTheDocument();
    });
  });

  describe('Spinner', () => {
    it('renders with status role and accessible sr-only label', () => {
      render(<Spinner label="Processing legal document" />);
      const status = screen.getByRole('status');
      expect(status).toBeInTheDocument();
      expect(screen.getByText('Processing legal document')).toBeInTheDocument();
    });
  });

  describe('SkeletonBlock', () => {
    it('renders with aria-hidden for accessibility', () => {
      const { container } = render(<SkeletonBlock height={20} width={100} />);
      const skeleton = container.firstChild as HTMLElement;
      expect(skeleton).toHaveAttribute('aria-hidden', 'true');
      expect(skeleton).toHaveClass('animate-pulse');
    });
  });
});
