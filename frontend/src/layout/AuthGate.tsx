/**
 * AuthGate — wraps authenticated routes.
 * Redirects unauthenticated users to /login, preserving the intended path in sessionStorage.
 * After successful auth, redirects to the stored path (or /).
 */

import { useEffect, useRef } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
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
      <div className="flex flex-col items-center justify-center h-screen gap-4">
        <div className="w-8 h-8 border-4 border-border border-t-primary rounded-full animate-spin" />
        <p className="text-muted-foreground">Loading...</p>
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
