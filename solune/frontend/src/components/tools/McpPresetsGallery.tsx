import { AlertCircle, RefreshCw, Sparkles } from '@/lib/icons';
import type { McpPreset } from '@/types';
import { Button } from '@/components/ui/button';
import { CelestialLoader } from '@/components/common/CelestialLoader';
import { isRateLimitApiError } from '@/utils/rateLimit';

interface McpPresetsGalleryProps {
  presets: McpPreset[];
  isLoading: boolean;
  error: string | null;
  rawError?: unknown;
  onSelectPreset: (preset: McpPreset) => void;
  onRetry?: () => void;
}

export function McpPresetsGallery({
  presets,
  isLoading,
  error,
  rawError,
  onSelectPreset,
  onRetry,
}: McpPresetsGalleryProps) {
  const isRateLimit = rawError != null && isRateLimitApiError(rawError);
  return (
    <section className="celestial-fade-in ritual-stage rounded-[1.55rem] p-4 sm:rounded-[1.85rem] sm:p-6">
      <div>
        <p className="text-[11px] uppercase tracking-[0.24em] text-primary/80">Preset library</p>
        <h4 className="mt-2 text-[1.35rem] font-display font-medium leading-tight sm:text-[1.6rem]">
          Quick-add MCP presets
        </h4>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
          Start from a documented MCP configuration and adjust it before saving it into the
          repository.
        </p>
      </div>

      {isLoading && (
        <div className="mt-6 flex items-center justify-center py-6">
          <CelestialLoader size="md" label="Loading presets" />
        </div>
      )}
      {error && !isLoading && (
        <div className="mt-6 flex flex-col items-center gap-3 rounded-2xl border border-destructive/30 bg-destructive/5 p-6 text-center">
          <AlertCircle className="h-5 w-5 text-destructive" aria-hidden="true" />
          <p className="text-sm text-destructive">
            {isRateLimit
              ? 'Rate limit reached. Please wait a few minutes before retrying.'
              : `Could not load presets. ${error} Please try again.`}
          </p>
          {onRetry && (
            <Button variant="outline" size="sm" onClick={onRetry}>
              <RefreshCw className="mr-1.5 h-3.5 w-3.5" aria-hidden="true" />
              Retry
            </Button>
          )}
        </div>
      )}

      {!isLoading && !error && presets.length === 0 && (
        <div className="mt-6 flex flex-col items-center gap-3 rounded-[1.35rem] border border-dashed border-border/80 bg-background/42 p-8 text-center">
          <Sparkles className="h-6 w-6 text-muted-foreground/50" aria-hidden="true" />
          <p className="text-sm text-muted-foreground">
            No presets available yet. Upload a custom MCP configuration to get started.
          </p>
        </div>
      )}

      {!isLoading && !error && presets.length > 0 && (
        <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {presets.map((preset) => (
            <article
              key={preset.id}
              className="rounded-[1.35rem] border border-border/70 bg-background/40 p-4"
            >
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.22em] text-primary/80">
                    {preset.category}
                  </p>
                  <h5 className="mt-2 text-base font-medium text-foreground">{preset.name}</h5>
                </div>
              </div>
              <p className="mt-3 text-sm text-muted-foreground">{preset.description}</p>
              <button
                type="button"
                onClick={() => onSelectPreset(preset)}
                aria-label={`Use ${preset.name} preset`}
                className="mt-4 rounded-full border border-border/70 px-4 py-2 text-sm font-medium text-foreground transition-colors hover:border-primary/50 hover:bg-primary/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
              >
                Use preset
              </button>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
