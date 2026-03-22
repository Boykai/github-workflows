/**
 * AppPreview — iframe wrapper for live application preview.
 * Includes sandbox attribute for XSS/clickjacking protection,
 * loading state, and offline/error state fallback.
 */

import { useState } from 'react';
import { AlertTriangle, Monitor } from '@/lib/icons';

interface AppPreviewProps {
  port: number | null;
  appName: string;
  isActive: boolean;
}

export function AppPreview({ port, appName, isActive }: AppPreviewProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  if (!isActive || !port) {
    return (
      <div className="flex h-96 flex-col items-center justify-center rounded-lg border border-dashed border-zinc-300 bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900/50">
        <Monitor className="mb-3 h-10 w-10 text-zinc-400" />
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          {isActive ? 'No port assigned' : 'Start the app to see a live preview'}
        </p>
      </div>
    );
  }

  const previewUrl = `http://localhost:${port}`;

  return (
    <div className="relative overflow-hidden rounded-lg border border-zinc-200 dark:border-zinc-700">
      {/* Loading overlay */}
      {isLoading && !hasError && (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/80 dark:bg-zinc-900/80">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-zinc-300 border-t-emerald-500" />
        </div>
      )}

      {/* Error fallback */}
      {hasError && (
        <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-white dark:bg-zinc-900">
          <AlertTriangle className="mb-2 h-8 w-8 text-amber-500" />
          <p className="text-sm text-zinc-500">Could not load preview for {appName}</p>
        </div>
      )}

      <iframe
        title={`Preview: ${appName}`}
        src={previewUrl}
        sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
        className="h-96 w-full"
        onLoad={() => setIsLoading(false)}
        onError={() => {
          setIsLoading(false);
          setHasError(true);
        }}
      />
    </div>
  );
}
