import React, { useState } from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ErrorBoundary } from '../ErrorBoundary';

const ProblematicChild: React.FC<{ shouldThrow?: boolean; message?: string }> = ({
  shouldThrow = true,
  message = 'Critical component crash',
}) => {
  if (shouldThrow) {
    throw new Error(message);
  }
  return <div>Healthy Child Content</div>;
};

describe('ErrorBoundary Component (components/common/ErrorBoundary)', () => {
  // Suppress expected React console.error during throwing tests
  const originalError = console.error;
  beforeEach(() => {
    console.error = vi.fn();
  });
  afterEach(() => {
    console.error = originalError;
  });

  it('renders children normally when no error occurs', () => {
    render(
      <ErrorBoundary>
        <div>Child rendered successfully</div>
      </ErrorBoundary>
    );

    expect(screen.getByText('Child rendered successfully')).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('catches render error, prevents unhandled crash, and renders accessible fallback UI', () => {
    render(
      <ErrorBoundary>
        <ProblematicChild message="Test render explosion" />
      </ErrorBoundary>
    );

    const alertBanner = screen.getByRole('alert');
    expect(alertBanner).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /something went wrong/i })).toBeInTheDocument();
    expect(screen.getByText('Test render explosion')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /go to dashboard/i })).toBeInTheDocument();
  });

  it('resets error state when "Try Again" button is clicked', () => {
    const ParentComponent: React.FC = () => {
      const [hasError, setHasError] = useState(true);

      return (
        <ErrorBoundary onReset={() => setHasError(false)}>
          {hasError ? <ProblematicChild /> : <div>Recovered Child Content</div>}
        </ErrorBoundary>
      );
    };

    render(<ParentComponent />);

    expect(screen.getByRole('alert')).toBeInTheDocument();
    const tryAgainBtn = screen.getByRole('button', { name: /try again/i });
    fireEvent.click(tryAgainBtn);

    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(screen.getByText('Recovered Child Content')).toBeInTheDocument();
  });

  it('supports custom function fallback with error and reset handles', () => {
    render(
      <ErrorBoundary
        fallback={(err, reset) => (
          <div data-testid="custom-fallback">
            <p>Custom Error: {err.message}</p>
            <button type="button" onClick={reset}>
              Custom Reset
            </button>
          </div>
        )}
      >
        <ProblematicChild message="Custom explosion" />
      </ErrorBoundary>
    );

    expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();
    expect(screen.getByText('Custom Error: Custom explosion')).toBeInTheDocument();
  });

  it('invokes onError prop with error and errorInfo when caught', () => {
    const onErrorMock = vi.fn();

    render(
      <ErrorBoundary onError={onErrorMock}>
        <ProblematicChild message="Logged error" />
      </ErrorBoundary>
    );

    expect(onErrorMock).toHaveBeenCalledTimes(1);
    expect(onErrorMock).toHaveBeenCalledWith(
      expect.objectContaining({ message: 'Logged error' }),
      expect.objectContaining({ componentStack: expect.any(String) })
    );
  });
});
