/**
 * NotFoundPage — 404 route fallback.
 */

import { useNavigate } from 'react-router-dom';

export function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 p-8 text-center">
      <span className="text-6xl font-bold text-primary/30">404</span>
      <h1 className="text-2xl font-bold tracking-tight">Page Not Found</h1>
      <p className="text-muted-foreground">The page you're looking for doesn't exist.</p>
      <button
        onClick={() => navigate('/')}
        className="mt-2 px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
      >
        Go Home
      </button>
    </div>
  );
}
