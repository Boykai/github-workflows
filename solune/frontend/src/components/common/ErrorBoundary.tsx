import { Component, type ErrorInfo, type ReactNode } from 'react';
import { getErrorHint } from '@/utils/errorHints';
import { Lightbulb } from '@/lib/icons';

interface ErrorBoundaryProps {
  children: ReactNode;
  onReset?: () => void;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * Catch rendering errors and display a fallback UI instead of crashing the
 * entire component tree.  Integrates with TanStack Query's
 * `QueryErrorResetBoundary` via the `onReset` prop.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('ErrorBoundary caught:', error, info.componentStack);
  }

  private handleReset = (): void => {
    this.setState({ hasError: false, error: null });
    this.props.onReset?.();
  };

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const errorHint = getErrorHint(this.state.error);

      return (
        <div
          role="alert"
          className="starfield flex h-full min-h-[60vh] flex-col items-center justify-center gap-4 p-8 text-center"
        >
          <span className="text-6xl font-bold text-destructive/30 celestial-float">!</span>
          <h2 className="text-3xl font-display font-medium tracking-[0.06em] celestial-fade-in">
            Something went wrong
          </h2>
          <pre className="max-w-lg rounded-lg bg-muted/50 px-4 py-3 text-sm text-destructive whitespace-pre-wrap">
            {this.state.error?.message}
          </pre>
          <div className="flex items-start gap-2 max-w-lg text-sm text-muted-foreground">
            <Lightbulb className="h-4 w-4 shrink-0 mt-0.5" />
            <p>
              {errorHint.hint}
              {errorHint.action && (
                <>
                  {' '}
                  <a href={errorHint.action.href} className="underline text-primary hover:text-primary/80">
                    {errorHint.action.label}
                  </a>
                </>
              )}
            </p>
          </div>
          <button
            type="button"
            onClick={this.handleReset}
            className="mt-2 rounded-full bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground shadow-sm transition-all hover:-translate-y-0.5 hover:bg-primary/90 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          >
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
