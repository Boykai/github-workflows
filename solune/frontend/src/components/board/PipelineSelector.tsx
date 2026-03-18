/**
 * PipelineSelector — dropdown for selecting the active pipeline on the board.
 * Extracted from ProjectsPage to reduce page size and improve modularity.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { PipelineConfigSummary } from '@/types';

export interface PipelineSelectorProps {
  assignedPipelineId: string | null | undefined;
  savedPipelines: PipelineConfigSummary[] | undefined;
  isAssigning: boolean;
  onSelect: (pipelineId: string) => void;
}

export function PipelineSelector({
  assignedPipelineId,
  savedPipelines,
  isAssigning,
  onSelect,
}: PipelineSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const assignedPipeline = savedPipelines?.find(
    (p) => p.id === (assignedPipelineId ?? ''),
  ) ?? null;

  useEffect(() => {
    if (!isOpen) return;

    function handlePointerDown(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  const handleSelection = useCallback(
    (pipelineId: string) => {
      setIsOpen(false);
      onSelect(pipelineId);
    },
    [onSelect],
  );

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setIsOpen((current) => !current)}
        disabled={isAssigning}
        className={cn(
          'project-pipeline-select project-pipeline-trigger flex h-9 min-w-[12rem] items-center justify-between gap-3 rounded-full px-4 text-xs font-medium text-foreground',
          assignedPipelineId && 'project-pipeline-select-active',
          isOpen && 'project-pipeline-select-open',
        )}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label="Agent Pipeline"
      >
        <span className="truncate">
          {assignedPipeline?.name ?? 'No pipeline selected'}
        </span>
        <ChevronDown
          className={cn(
            'h-3.5 w-3.5 shrink-0 text-muted-foreground transition-transform',
            isOpen && 'rotate-180',
          )}
        />
      </button>

      {isOpen && (
        <div className="project-pipeline-menu absolute right-0 top-full z-30 mt-2 w-[min(20rem,calc(100vw-3rem))] overflow-hidden rounded-[1.1rem] border border-border/80">
          <div className="border-b border-border/65 px-3 py-2.5 text-[10px] font-semibold uppercase tracking-[0.22em] text-muted-foreground/90">
            Select pipeline
          </div>
          <div
            className="max-h-72 overflow-y-auto p-1.5"
            role="listbox"
            aria-label="Agent Pipeline options"
          >
            <button
              type="button"
              role="option"
              aria-selected={!assignedPipelineId}
              onClick={() => handleSelection('')}
              disabled={isAssigning}
              className={cn(
                'project-pipeline-option flex w-full items-center justify-between gap-3 rounded-[0.9rem] px-3 py-2.5 text-left text-sm disabled:cursor-not-allowed disabled:opacity-60',
                !assignedPipelineId && 'project-pipeline-option-active',
              )}
            >
              <span className="truncate">No pipeline selected</span>
              {!assignedPipelineId && (
                <span className="text-[10px] font-semibold uppercase tracking-[0.18em]">
                  Current
                </span>
              )}
            </button>
            {savedPipelines?.map((pipeline) => {
              const isSelected = pipeline.id === (assignedPipelineId ?? '');
              return (
                <button
                  key={pipeline.id}
                  type="button"
                  role="option"
                  aria-selected={isSelected}
                  onClick={() => handleSelection(pipeline.id)}
                  disabled={isAssigning}
                  className={cn(
                    'project-pipeline-option flex w-full items-center justify-between gap-3 rounded-[0.9rem] px-3 py-2.5 text-left text-sm disabled:cursor-not-allowed disabled:opacity-60',
                    isSelected && 'project-pipeline-option-active',
                  )}
                >
                  <span className="truncate">{pipeline.name}</span>
                  {isSelected && (
                    <span className="text-[10px] font-semibold uppercase tracking-[0.18em]">
                      Current
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
