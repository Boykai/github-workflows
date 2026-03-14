/**
 * NotFoundPage — 404 route fallback.
 */

import { useNavigate } from 'react-router-dom';

export function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="starfield flex h-full flex-col items-center justify-center gap-4 p-8 text-center">
      <span className="text-6xl font-bold text-primary/30 celestial-float">404</span>
      <h1 className="text-4xl font-display font-medium tracking-[0.06em] celestial-fade-in">
        Lost Between Sun & Moon
      </h1>
      <p className="max-w-md text-muted-foreground">
        The page you’re looking for drifted out of orbit. Return home to rejoin the main
        constellation.
      </p>
      <button
        type="button"
        onClick={() => navigate('/')}
        className="mt-2 rounded-full bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground shadow-sm transition-all hover:-translate-y-0.5 hover:bg-primary/90 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
      >
        Go Home
      </button>
    </div>
  );
}
