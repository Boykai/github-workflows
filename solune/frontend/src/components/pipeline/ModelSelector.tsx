/**
 * ModelSelector — reusable model picker popover.
 * Groups models by provider, shows metadata, tracks recently used.
 */

import { useState, useMemo, useCallback, useRef } from 'react';
import { Popover, PopoverTrigger, PopoverContent } from '@/components/ui/popover';
import { useModels } from '@/hooks/useModels';
import { ChevronDown, Search, Check, Zap, DollarSign, Crown } from '@/lib/icons';
import type { AIModel } from '@/types';
import { cn } from '@/lib/utils';

interface ModelSelectorProps {
  selectedModelId: string | null;
  selectedModelName?: string | null;
  onSelect: (modelId: string, modelName: string) => void;
  trigger?: React.ReactNode;
  disabled?: boolean;
  allowAuto?: boolean;
  autoLabel?: string;
  triggerClassName?: string;
}

function CostTierBadge({ tier }: { tier: string }) {
  switch (tier) {
    case 'economy':
      return (
        <span className="solar-chip-success inline-flex items-center gap-0.5 rounded-full px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em]">
          <DollarSign className="h-2.5 w-2.5" />
          Economy
        </span>
      );
    case 'standard':
      return (
        <span className="inline-flex items-center gap-0.5 rounded-full border border-sky-500/25 bg-sky-500/12 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-sky-700 dark:text-sky-300">
          <Zap className="h-2.5 w-2.5" />
          Standard
        </span>
      );
    case 'premium':
      return (
        <span className="inline-flex items-center gap-0.5 rounded-full border border-amber-500/25 bg-amber-500/12 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-amber-700 dark:text-amber-300">
          <Crown className="h-2.5 w-2.5" />
          Premium
        </span>
      );
    default:
      return null;
  }
}

function formatContextWindow(size: number): string {
  if (size >= 1_000_000) return `${(size / 1_000_000).toFixed(0)}M tokens`;
  if (size >= 1000) return `${(size / 1000).toFixed(0)}K tokens`;
  return `${size} tokens`;
}

export function ModelSelector({
  selectedModelId,
  selectedModelName,
  onSelect,
  trigger,
  disabled = false,
  allowAuto = false,
  autoLabel = 'Auto',
  triggerClassName,
}: ModelSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const { models, modelsByProvider, isLoading, isRefreshing, refreshModels } = useModels();
  const recentModelIdsRef = useRef<string[]>([]);

  const addRecentModel = useCallback((modelId: string) => {
    const ids = recentModelIdsRef.current;
    const idx = ids.indexOf(modelId);
    if (idx !== -1) ids.splice(idx, 1);
    ids.unshift(modelId);
    if (ids.length > 3) ids.pop();
  }, []);

  const recentModels = useMemo(
    () =>
      recentModelIdsRef.current
        .map((id) => models.find((m) => m.id === id))
        .filter((m): m is AIModel => m !== undefined),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [models, isOpen]
  );

  const filteredProviderGroups = useMemo(() => {
    if (!search.trim()) return modelsByProvider;
    const q = search.toLowerCase();
    return modelsByProvider
      .map((g) => ({
        ...g,
        models: g.models.filter(
          (m) =>
            m.name.toLowerCase().includes(q) ||
            m.provider.toLowerCase().includes(q) ||
            m.id.toLowerCase().includes(q)
        ),
      }))
      .filter((g) => g.models.length > 0);
  }, [modelsByProvider, search]);

  const handleSelect = useCallback(
    (model: AIModel) => {
      addRecentModel(model.id);
      onSelect(model.id, model.name);
      setIsOpen(false);
      setSearch('');
    },
    [addRecentModel, onSelect]
  );

  const handleOpenChange = useCallback((open: boolean) => {
    setIsOpen(open);
    if (!open) setSearch('');
  }, []);

  const selectedModel = models.find((m) => m.id === selectedModelId);
  const triggerLabel =
    selectedModel?.name ?? selectedModelName ?? (allowAuto ? autoLabel : 'Select model');

  return (
    <Popover open={isOpen} onOpenChange={handleOpenChange}>
      <PopoverTrigger asChild>
        <button
          type="button"
          disabled={disabled}
          className={cn(
            'celestial-focus flex items-center gap-1.5 rounded-lg border border-border/60 bg-background/68 px-2.5 py-1.5 text-xs transition-colors hover:bg-primary/10 disabled:cursor-not-allowed disabled:opacity-60 dark:border-border/80 dark:bg-[linear-gradient(180deg,hsl(var(--night)/0.95)_0%,hsl(var(--panel)/0.9)_100%)] dark:hover:bg-primary/12',
            triggerClassName
          )}
        >
          {trigger || (
            <>
              <span
                className={
                  selectedModelId || selectedModelName
                    ? 'text-foreground truncate'
                    : 'text-muted-foreground truncate'
                }
              >
                {triggerLabel}
              </span>
              <ChevronDown className="h-3 w-3 shrink-0 text-muted-foreground" />
            </>
          )}
        </button>
      </PopoverTrigger>

      <PopoverContent side="bottom" align="start" className="w-72 p-0">
        {/* Search */}
        <div className="flex items-center gap-2 border-b border-border/50 px-3 py-2">
          <Search className="h-3.5 w-3.5 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search models..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 bg-transparent text-xs outline-none placeholder:text-muted-foreground/60"
          />
          <button
            type="button"
            onClick={() => void refreshModels()}
            className="celestial-focus rounded-md border border-border/60 px-2 py-1 text-[10px] font-medium text-muted-foreground transition-colors hover:bg-primary/10 hover:text-foreground focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isRefreshing}
          >
            {isRefreshing ? 'Refreshing…' : 'Refresh'}
          </button>
        </div>

        <div className="max-h-64 overflow-y-auto p-1.5">
          {isLoading && (
            <div className="flex items-center justify-center py-4">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-border border-t-primary" />
            </div>
          )}

          {!isLoading && allowAuto && (
            <div className="mb-1">
              <button
                type="button"
                onClick={() => {
                  onSelect('', '');
                  setIsOpen(false);
                  setSearch('');
                }}
                className={cn(
                  'celestial-focus flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-xs transition-colors hover:bg-primary/10 focus-visible:outline-none',
                  !selectedModelId ? 'bg-primary/10' : ''
                )}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="font-medium text-foreground">{autoLabel}</span>
                    {!selectedModelId && <Check className="h-3 w-3 text-primary" />}
                  </div>
                  <div className="mt-0.5 text-[10px] text-muted-foreground">
                    Use the agent&apos;s configured default model
                  </div>
                </div>
              </button>
              <div className="my-1 border-b border-border/30" />
            </div>
          )}

          {/* Recent models */}
          {!search && recentModels.length > 0 && (
            <div className="mb-1">
              <div className="px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                Recent
              </div>
              {recentModels.map((model) => (
                <ModelRow
                  key={`recent-${model.id}`}
                  model={model}
                  isSelected={model.id === selectedModelId}
                  onSelect={handleSelect}
                />
              ))}
              <div className="my-1 border-b border-border/30" />
            </div>
          )}

          {/* Provider groups */}
          {filteredProviderGroups.map((group) => (
            <div key={group.provider} className="mb-1">
              <div className="px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                {group.provider}
              </div>
              {group.models.map((model) => (
                <ModelRow
                  key={model.id}
                  model={model}
                  isSelected={model.id === selectedModelId}
                  onSelect={handleSelect}
                />
              ))}
            </div>
          ))}

          {!isLoading && filteredProviderGroups.length === 0 && (
            <div className="py-3 text-center text-xs text-muted-foreground">
              No models found
            </div>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}

function ModelRow({
  model,
  isSelected,
  onSelect,
}: {
  model: AIModel;
  isSelected: boolean;
  onSelect: (model: AIModel) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onSelect(model)}
      className={cn(
        'celestial-focus flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-xs transition-colors hover:bg-primary/10 focus-visible:outline-none',
        isSelected ? 'bg-primary/10' : ''
      )}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <span className="font-medium text-foreground">{model.name}</span>
          {isSelected && <Check className="h-3 w-3 text-primary" />}
        </div>
        <div className="flex items-center gap-2 mt-0.5">
          {model.context_window_size ? (
            <span className="text-[10px] text-muted-foreground">
              {formatContextWindow(model.context_window_size)}
            </span>
          ) : null}
          {model.cost_tier ? <CostTierBadge tier={model.cost_tier} /> : null}
        </div>
      </div>
    </button>
  );
}
