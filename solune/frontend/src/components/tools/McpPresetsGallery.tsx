import { Link } from 'react-router-dom';
import type { McpPreset } from '@/types';

interface McpPresetsGalleryProps {
  presets: McpPreset[];
  isLoading: boolean;
  error: string | null;
  onSelectPreset: (preset: McpPreset) => void;
}

export function McpPresetsGallery({
  presets,
  isLoading,
  error,
  onSelectPreset,
}: McpPresetsGalleryProps) {
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

      {isLoading && <div className="mt-6 text-sm text-muted-foreground">Loading presets…</div>}
      {error && !isLoading && (
        <div className="mt-6 rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      {!isLoading && !error && (
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
              {preset.required_secrets?.length > 0 && (
                <Link
                  to="/settings#secrets"
                  className="mt-2 inline-flex items-center gap-1 text-xs text-yellow-600 hover:text-yellow-700 dark:text-yellow-400 dark:hover:text-yellow-300"
                >
                  ⚠ Requires API key configuration
                </Link>
              )}
              <button
                type="button"
                onClick={() => onSelectPreset(preset)}
                className="mt-4 rounded-full border border-border/70 px-4 py-2 text-sm font-medium text-foreground transition-colors hover:border-primary/50 hover:bg-primary/10"
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
