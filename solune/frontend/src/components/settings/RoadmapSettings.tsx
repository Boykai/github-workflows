/**
 * Roadmap Settings section within project settings.
 *
 * Provides controls for roadmap engine configuration:
 * - Enable/disable toggle
 * - Seed vision textarea
 * - Batch size input (1-10)
 * - Pipeline selector
 * - Auto-launch toggle
 * - Grace minutes input
 */

import type { ProjectBoardConfig } from '@/types';

interface RoadmapSettingsProps {
  config: ProjectBoardConfig;
  pipelines: Array<{ id: string; name: string }>;
  onChange: (updates: Partial<ProjectBoardConfig>) => void;
}

export function RoadmapSettings({ config, pipelines, onChange }: RoadmapSettingsProps) {
  return (
    <div className="flex flex-col gap-4">
      <h4 className="text-sm font-semibold text-foreground border-b border-border pb-2">
        Roadmap Engine
      </h4>

      {/* Enable/Disable Toggle */}
      <label className="flex items-center gap-2 text-sm font-medium text-foreground cursor-pointer">
        <input
          type="checkbox"
          className="celestial-focus w-4 h-4 rounded border-input text-primary"
          checked={config.roadmap_enabled}
          onChange={(e) => onChange({ roadmap_enabled: e.target.checked })}
          aria-label="Enable roadmap engine"
        />
        Enable Roadmap Engine
      </label>

      {config.roadmap_enabled && (
        <>
          {/* Seed Vision */}
          <div className="flex flex-col gap-1">
            <label htmlFor="roadmap-seed" className="text-sm font-medium text-foreground">
              Seed Vision
            </label>
            <textarea
              id="roadmap-seed"
              className="celestial-focus flex min-h-[80px] w-full rounded-md border border-input bg-background text-foreground px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none"
              rows={4}
              maxLength={10000}
              value={config.roadmap_seed}
              onChange={(e) => onChange({ roadmap_seed: e.target.value })}
              placeholder="Describe your product vision and direction..."
            />
            <span className="text-xs text-muted-foreground">
              {config.roadmap_seed.length}/10,000 characters
            </span>
          </div>

          {/* Batch Size */}
          <div className="flex flex-col gap-1">
            <label htmlFor="roadmap-batch-size" className="text-sm font-medium text-foreground">
              Batch Size
            </label>
            <input
              id="roadmap-batch-size"
              type="number"
              min={1}
              max={10}
              className="celestial-focus flex h-9 w-24 rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none"
              value={config.roadmap_batch_size}
              onChange={(e) => {
                const val = parseInt(e.target.value, 10);
                if (!isNaN(val) && val >= 1 && val <= 10) {
                  onChange({ roadmap_batch_size: val });
                }
              }}
            />
            <span className="text-xs text-muted-foreground">
              Number of features per generation cycle (1–10)
            </span>
          </div>

          {/* Pipeline Selector */}
          <div className="flex flex-col gap-1">
            <label htmlFor="roadmap-pipeline" className="text-sm font-medium text-foreground">
              Target Pipeline
            </label>
            <select
              id="roadmap-pipeline"
              className="celestial-focus flex h-9 w-full rounded-md border border-input bg-background text-foreground px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none"
              value={config.roadmap_pipeline_id ?? ''}
              onChange={(e) =>
                onChange({ roadmap_pipeline_id: e.target.value || null })
              }
            >
              <option value="">Select a pipeline...</option>
              {pipelines.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          {/* Auto-Launch Toggle */}
          <label className="flex items-center gap-2 text-sm font-medium text-foreground cursor-pointer">
            <input
              type="checkbox"
              className="celestial-focus w-4 h-4 rounded border-input text-primary"
              checked={config.roadmap_auto_launch}
              onChange={(e) => onChange({ roadmap_auto_launch: e.target.checked })}
              aria-label="Enable auto-launch on idle pipeline"
            />
            Auto-launch when pipeline is idle
          </label>

          {/* Grace Minutes */}
          <div className="flex flex-col gap-1">
            <label htmlFor="roadmap-grace" className="text-sm font-medium text-foreground">
              Grace Period (minutes)
            </label>
            <input
              id="roadmap-grace"
              type="number"
              min={0}
              max={1440}
              className="celestial-focus flex h-9 w-24 rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none"
              value={config.roadmap_grace_minutes}
              onChange={(e) => {
                const val = parseInt(e.target.value, 10);
                if (!isNaN(val) && val >= 0 && val <= 1440) {
                  onChange({ roadmap_grace_minutes: val });
                }
              }}
            />
            <span className="text-xs text-muted-foreground">
              Minutes to hold items before auto-launching (0 = immediate)
            </span>
          </div>
        </>
      )}
    </div>
  );
}
