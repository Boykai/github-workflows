/**
 * AuthGate — wraps authenticated routes.
 * Redirects unauthenticated users to /login, preserving the intended path in sessionStorage.
 * After successful auth, redirects to the stored path (or /).
 */

import { useEffect, useRef } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { MoonStar } from '@/lib/icons';
import { CelestialLoader } from '@/components/common/CelestialLoader';
import { useAuth } from '@/hooks/useAuth';

const REDIRECT_KEY = 'solune-redirect-after-login';

export function AuthGate({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const didRedirect = useRef(false);

  // After authentication, consume stored redirect path
  useEffect(() => {
    if (isAuthenticated && !didRedirect.current) {
      didRedirect.current = true;
      const stored = sessionStorage.getItem(REDIRECT_KEY);
      if (stored) {
        sessionStorage.removeItem(REDIRECT_KEY);
        navigate(stored, { replace: true });
      }
    }
  }, [isAuthenticated, navigate]);

  if (isLoading) {
    return (
      <div className="starfield flex h-screen flex-col items-center justify-center gap-4 bg-background">
        <div className="flex h-14 w-14 items-center justify-center rounded-full border border-primary/25 bg-primary/10 text-primary shadow-md">
          <MoonStar className="h-6 w-6" />
        </div>
        <CelestialLoader size="sm" label="Checking authentication" />
        <p className="text-xs uppercase tracking-[0.24em] text-muted-foreground">
          Aligning the workspace...
        </p>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Store the intended path so we can redirect after login
    const intended = location.pathname + location.search + location.hash;
    if (intended !== '/' && intended !== '/login') {
      sessionStorage.setItem(REDIRECT_KEY, intended);
    }
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
