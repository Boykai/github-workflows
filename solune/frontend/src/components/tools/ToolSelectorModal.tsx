/**
 * ToolSelectorModal — full overlay modal with responsive tile grid for
 * selecting MCP tools to assign to an agent.
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { Check, Search, Wrench } from '@/lib/icons';
import { useToolsList } from '@/hooks/useTools';
import { cn } from '@/lib/utils';

interface ToolSelectorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (selectedToolIds: string[]) => void;
  initialSelectedIds: string[];
  projectId: string;
}

export function ToolSelectorModal({
  isOpen,
  onClose,
  onConfirm,
  initialSelectedIds,
  projectId,
}: ToolSelectorModalProps) {
  const { tools, isLoading } = useToolsList(projectId);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState('');

  // Sync initial selection
  const [prevIsOpen, setPrevIsOpen] = useState(isOpen);
  const initialIdsKey = initialSelectedIds.join(',');
  const [prevInitialIdsKey, setPrevInitialIdsKey] = useState(initialIdsKey);
  if (isOpen && (isOpen !== prevIsOpen || initialIdsKey !== prevInitialIdsKey)) {
    setPrevIsOpen(true);
    setPrevInitialIdsKey(initialIdsKey);
    setSelectedIds(new Set(initialSelectedIds));
    setSearch('');
  } else if (!isOpen && prevIsOpen) {
    setPrevIsOpen(false);
  } else if (initialIdsKey !== prevInitialIdsKey) {
    setPrevInitialIdsKey(initialIdsKey);
  }

  // Escape key handler
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const toggleTool = useCallback((toolId: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(toolId)) {
        next.delete(toolId);
      } else {
        next.add(toolId);
      }
      return next;
    });
  }, []);

  const handleConfirm = useCallback(() => {
    onConfirm(Array.from(selectedIds));
    onClose();
  }, [selectedIds, onConfirm, onClose]);

  const filteredTools = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return tools;
    return tools.filter(
      (t) => t.name.toLowerCase().includes(query) || t.description.toLowerCase().includes(query)
    );
  }, [tools, search]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50"
      role="presentation"
      onClick={onClose}
    >
      <div
        className="celestial-panel celestial-fade-in flex w-full max-w-3xl max-h-[85vh] flex-col rounded-[1.4rem] border border-border shadow-lg"
        role="presentation"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border p-4">
          <h2 className="text-lg font-semibold">Select MCP Tools</h2>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground text-lg leading-none px-2"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        {/* Search */}
        <div className="p-4 border-b border-border">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search tools by name or description"
              className="w-full rounded-md border border-border bg-background/72 py-2 pl-10 pr-3 text-sm"
            />
          </div>
        </div>

        {/* Grid */}
        <div className="flex-1 overflow-y-auto p-4">
          {isLoading && (
            <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="h-24 rounded-lg border border-border bg-background/40 animate-pulse"
                />
              ))}
            </div>
          )}

          {!isLoading && filteredTools.length === 0 && (
            <div className="flex flex-col items-center gap-2 py-8 text-center">
              <Wrench className="h-8 w-8 text-muted-foreground/50" />
              <p className="text-sm text-muted-foreground">
                {tools.length === 0
                  ? 'No MCP tools available. Visit the Tools page to upload a configuration.'
                  : 'No tools match your search.'}
              </p>
            </div>
          )}

          {!isLoading && filteredTools.length > 0 && (
            <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
              {filteredTools.map((tool) => {
                const isSelected = selectedIds.has(tool.id);
                return (
                  <button
                    key={tool.id}
                    type="button"
                    onClick={() => toggleTool(tool.id)}
                    className={cn('relative flex items-start gap-3 rounded-lg border p-3 text-left transition-colors', isSelected
                        ? 'border-primary bg-primary/8'
                        : 'border-border hover:border-primary/20 hover:bg-background/34')}
                  >
                    <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary/10">
                      <Wrench className="h-4 w-4 text-primary" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-foreground truncate">{tool.name}</p>
                      <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">
                        {tool.description}
                      </p>
                    </div>
                    {isSelected && (
                      <div className="absolute top-2 right-2 flex h-5 w-5 items-center justify-center rounded-full bg-primary">
                        <Check className="h-3 w-3 text-primary-foreground" />
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-border p-4">
          <span className="text-sm text-muted-foreground">
            {selectedIds.size} tool{selectedIds.size !== 1 ? 's' : ''} selected
          </span>
          <div className="flex gap-2">
            <button
              className="rounded-full border border-border bg-background/72 px-4 py-2 text-sm font-medium text-muted-foreground hover:bg-primary/10 hover:text-foreground"
              onClick={onClose}
            >
              Cancel
            </button>
            <button
              className="px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90"
              onClick={handleConfirm}
            >
              Confirm
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
