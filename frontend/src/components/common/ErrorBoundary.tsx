import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertOctagon, RotateCcw, Home, ChevronDown } from 'lucide-react';

export interface ErrorBoundaryProps {
  children?: ReactNode;
  fallback?: ReactNode | ((error: Error, reset: () => void) => ReactNode);
  onReset?: () => void;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.setState({ errorInfo });
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
    // In development or test, log to console
    if (process.env.NODE_ENV !== 'production') {
      console.error('ErrorBoundary caught an unhandled component error:', error, errorInfo);
    }
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  handleGoHome = (): void => {
    this.handleReset();
    if (typeof window !== 'undefined') {
      window.location.href = '/dashboard';
    }
  };

  render(): ReactNode {
    if (this.state.hasError) {
      if (typeof this.props.fallback === 'function') {
        return this.props.fallback(this.state.error || new Error('Unknown error'), this.handleReset);
      }
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const errorMessage = this.state.error?.message || 'An unexpected application error occurred.';

      return (
        <main
          role="alert"
          aria-live="assertive"
          className="min-h-[60vh] flex items-center justify-center p-6 bg-surface"
          data-testid="error-boundary-fallback"
        >
          <div className="max-w-lg w-full bg-white rounded-xl shadow-elevation-2 border border-secondary-200 p-6 sm:p-8 text-center space-y-6">
            <div className="mx-auto w-14 h-14 rounded-full bg-risk-high-bg border border-risk-high-border flex items-center justify-center text-risk-high shadow-xs">
              <AlertOctagon className="w-7 h-7" aria-hidden="true" />
            </div>

            <div className="space-y-2">
              <h1 className="text-2xl font-serif font-bold text-primary-950">
                Something went wrong
              </h1>
              <p className="text-sm text-secondary-600 leading-relaxed">
                ClarifAI encountered an unexpected issue while rendering this view. Your session and data are secure.
              </p>
            </div>

            <div className="p-3 bg-secondary-50 rounded-lg border border-secondary-200 text-left text-xs font-mono text-secondary-700 break-words">
              <p className="font-semibold text-secondary-900 mb-1">Error Summary:</p>
              <p>{errorMessage}</p>
            </div>

            {this.state.errorInfo && (
              <details className="text-left text-xs text-secondary-500 bg-secondary-50 p-2.5 rounded-lg border border-secondary-200 group">
                <summary className="cursor-pointer font-medium text-secondary-700 select-none flex items-center justify-between">
                  <span>Component Stack Details</span>
                  <ChevronDown className="w-3.5 h-3.5 transition-transform group-open:rotate-180" />
                </summary>
                <pre className="mt-2 text-[11px] font-mono overflow-x-auto whitespace-pre-wrap text-secondary-600 max-h-40">
                  {this.state.errorInfo.componentStack}
                </pre>
              </details>
            )}

            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
              <button
                type="button"
                onClick={this.handleReset}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-primary-900 text-white hover:bg-primary-800 focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm font-medium transition-colors shadow-xs"
              >
                <RotateCcw className="w-4 h-4" aria-hidden="true" />
                <span>Try Again</span>
              </button>

              <button
                type="button"
                onClick={this.handleGoHome}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg border border-secondary-300 text-secondary-700 hover:bg-secondary-50 focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm font-medium transition-colors"
              >
                <Home className="w-4 h-4" aria-hidden="true" />
                <span>Go to Dashboard</span>
              </button>
            </div>
          </div>
        </main>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
