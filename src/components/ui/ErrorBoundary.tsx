import React from 'react';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
}

export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error, errorInfo: null };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error Boundary caught an error:', error);
    console.error('Error Info:', errorInfo);
    this.setState({ error, errorInfo });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="rounded-lg border border-brand-red bg-brand-red/10 p-6">
          <h3 className="mb-2 font-medium text-brand-red">Error</h3>
          <p className="mb-4 text-sm text-brand-red">Something went wrong.</p>
          <details className="text-xs text-brand-red">
            <summary className="cursor-pointer font-medium">
              Error Details:
            </summary>
            <pre className="mt-2 whitespace-pre-wrap">
              {this.state.error?.toString()}
              {this.state.errorInfo?.componentStack}
            </pre>
          </details>
          <button
            onClick={() =>
              this.setState({ hasError: false, error: null, errorInfo: null })
            }
            className="mt-4 rounded bg-brand-red px-4 py-2 text-white hover:brightness-90"
          >
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
