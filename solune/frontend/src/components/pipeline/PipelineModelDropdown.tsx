/**
 * PipelineModelDropdown — pipeline-level model selection dropdown.
 * Provides "Auto" option and batch-updates all agents when a model is selected.
 */

import { ChevronDown, Sparkles } from '@/lib/icons';
import { useState, useRef, useEffect } from 'react';
import type { AIModel, PipelineModelOverride } from '@/types';
import { cn } from '@/lib/utils';

interface PipelineModelDropdownProps {
  models: AIModel[];
  currentOverride: PipelineModelOverride;
  onModelChange: (override: PipelineModelOverride) => void;
  disabled?: boolean;
}

export function PipelineModelDropdown({
  models,
  currentOverride,
  onModelChange,
  disabled = false,
}: PipelineModelDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  const displayLabel =
    currentOverride.mode === 'auto'
      ? 'Auto'
      : currentOverride.mode === 'mixed'
        ? 'Mixed'
        : currentOverride.modelName || currentOverride.modelId;

  // Group models by provider
  const grouped = models.reduce<Record<string, AIModel[]>>((acc, model) => {
    (acc[model.provider] ??= []).push(model);
    return acc;
  }, {});

  return (
    <div ref={dropdownRef} className="relative">
      <span className="mb-1 block text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
        Pipeline Model
      </span>
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className="celestial-focus flex w-full items-center justify-between gap-2 rounded-lg border border-border/60 bg-background/68 px-3 py-2 text-sm transition-colors hover:border-primary/30 hover:bg-primary/10 disabled:opacity-50 dark:border-border/80 dark:bg-[linear-gradient(180deg,hsl(var(--night)/0.94)_0%,hsl(var(--panel)/0.88)_100%)] dark:hover:bg-primary/12"
      >
        <span className="flex items-center gap-2 truncate">
          <Sparkles className="h-3.5 w-3.5 text-primary/60" />
          {displayLabel}
        </span>
        <ChevronDown
          className={cn('h-3.5 w-3.5 text-muted-foreground transition-transform', isOpen ? 'rotate-180' : '')}
        />
      </button>

      {isOpen && (
        <div className="absolute left-0 top-full z-50 mt-1 w-full rounded-lg border border-border/80 bg-popover/95 shadow-lg backdrop-blur-sm dark:border-border/85 dark:bg-[linear-gradient(180deg,hsl(var(--night)/0.97)_0%,hsl(var(--panel)/0.93)_100%)]">
          <div className="max-h-60 overflow-y-auto p-1">
            {/* Auto option */}
            <button
              type="button"
              onClick={() => {
                onModelChange({ mode: 'auto', modelId: '', modelName: '' });
                setIsOpen(false);
              }}
              className={cn('flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors hover:bg-primary/10', currentOverride.mode === 'auto' ? 'bg-primary/10 text-primary' : '')}
            >
              <Sparkles className="h-3.5 w-3.5" />
              Auto
            </button>

            <div className="my-1 border-t border-border/40" />

            {/* Models grouped by provider */}
            {Object.entries(grouped).map(([provider, providerModels]) => (
              <div key={provider}>
                <div className="px-3 py-1 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                  {provider}
                </div>
                {providerModels.map((model) => (
                  <button
                    key={model.id}
                    type="button"
                    onClick={() => {
                      onModelChange({ mode: 'specific', modelId: model.id, modelName: model.name });
                      setIsOpen(false);
                    }}
                    className={cn('flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors hover:bg-primary/10', currentOverride.mode === 'specific' && currentOverride.modelId === model.id
                        ? 'bg-primary/10 text-primary'
                        : '')}
                  >
                    {model.name}
                  </button>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
