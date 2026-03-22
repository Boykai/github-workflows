import { useEffect, useRef, useState } from 'react';
import { ChevronDown, Check } from '@/lib/icons';
import { ThemedAgentIcon } from '@/components/common/ThemedAgentIcon';
import { CelestialLoader } from '@/components/common/CelestialLoader';
import { cn } from '@/lib/utils';
import type { Project } from '@/types';

interface ProjectSelectionEmptyStateProps {
  projects: Project[];
  isLoading: boolean;
  selectedProjectId?: string | null;
  onSelectProject: (projectId: string) => Promise<void>;
  description: string;
  showProjectPicker?: boolean;
}

export function ProjectSelectionEmptyState({
  projects,
  isLoading,
  selectedProjectId = null,
  onSelectProject,
  description,
  showProjectPicker = true,
}: ProjectSelectionEmptyStateProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [pendingProjectId, setPendingProjectId] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    const handleMouseDown = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleMouseDown);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('mousedown', handleMouseDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  const handleSelectProject = async (projectId: string) => {
    setPendingProjectId(projectId);
    try {
      await onSelectProject(projectId);
      setIsOpen(false);
    } finally {
      setPendingProjectId(null);
    }
  };

  return (
    <div className="celestial-panel flex flex-1 flex-col items-center justify-center rounded-[1.4rem] border border-dashed border-border/80 bg-background/26 p-6 text-center sm:rounded-[1.5rem] sm:p-8">
      <div ref={containerRef} className="flex w-full max-w-xl flex-col items-center">
        <button
          type="button"
          onClick={showProjectPicker ? () => setIsOpen((current) => !current) : undefined}
          disabled={!showProjectPicker}
          aria-expanded={showProjectPicker ? isOpen : undefined}
          aria-haspopup={showProjectPicker ? 'listbox' : undefined}
          aria-label={showProjectPicker ? 'Choose a GitHub project' : 'Project orbit'}
          className={cn(
            'group relative mb-5 flex h-24 w-24 items-center justify-center rounded-full',
            showProjectPicker
              ? 'transition-transform duration-200 hover:scale-[1.03] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/60 focus-visible:ring-offset-2 focus-visible:ring-offset-background'
              : 'cursor-default',
          )}
        >
          <div className="absolute inset-0 rounded-full border border-border/40 bg-[radial-gradient(circle_at_center,hsl(var(--glow)/0.18)_0%,transparent_64%)] transition-colors duration-200 group-hover:border-primary/30 group-hover:bg-[radial-gradient(circle_at_center,hsl(var(--glow)/0.28)_0%,transparent_64%)]" />
          <div className="absolute inset-[10px] rounded-full border border-primary/18 transition-colors duration-200 group-hover:border-primary/34" />
          <span className="absolute left-1/2 top-1.5 h-1.5 w-1.5 -translate-x-1/2 rounded-full bg-[hsl(var(--glow))] shadow-[0_0_12px_hsl(var(--glow)/0.8)] celestial-twinkle" />
          <span className="absolute bottom-4 right-2 h-2.5 w-2.5 rounded-full bg-[hsl(var(--gold))] shadow-[0_0_18px_hsl(var(--gold)/0.45)] celestial-twinkle-delayed" />
          <span className="absolute left-2 top-1/2 h-2 w-2 -translate-y-1/2 rounded-full bg-[hsl(var(--gold)/0.55)] celestial-twinkle-slow" />
          <ThemedAgentIcon
            name="Project orbit"
            iconName="orbit"
            size="lg"
            className="h-14 w-14 border-primary/30 shadow-[0_12px_30px_hsl(var(--night)/0.3)] transition-transform duration-200 group-hover:scale-105"
          />
        </button>

        <h3 className="text-xl font-semibold text-foreground">Select a project</h3>
        <p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">{description}</p>

        {showProjectPicker && (
          <button
            type="button"
            onClick={() => setIsOpen((current) => !current)}
            className="solar-chip-soft mt-4 inline-flex items-center gap-2 rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] transition-colors hover:bg-primary/12 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/60 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          >
            Browse GitHub Projects
            <ChevronDown className={cn('h-3.5 w-3.5 transition-transform', isOpen && 'rotate-180')} />
          </button>
        )}

        {showProjectPicker && isOpen && (
          <div className="mt-5 w-full max-w-md rounded-[1.35rem] border border-border/80 bg-background/80 p-3 text-left shadow-[0_24px_80px_hsl(var(--night)/0.32)] backdrop-blur-xl">
            <div className="border-b border-border/70 px-3 pb-3">
              <p className="text-[11px] uppercase tracking-[0.24em] text-primary/80">
                GitHub Projects
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                Pick a project to activate it for this workspace.
              </p>
            </div>

            {isLoading ? (
              <div className="flex items-center justify-center p-6">
                <CelestialLoader size="sm" label="Loading projects" />
              </div>
            ) : projects.length === 0 ? (
              <div className="p-6 text-center">
                <p className="text-sm text-foreground">No projects available</p>
                <p className="mt-1 text-xs text-muted-foreground/70">
                  Connect a GitHub Project to start working here.
                </p>
              </div>
            ) : (
              <div
                className="max-h-[18rem] overflow-y-auto py-2"
                role="listbox"
                aria-label="GitHub Projects"
              >
                {projects.map((project) => {
                  const isSelected = project.project_id === selectedProjectId;
                  const isPending = pendingProjectId === project.project_id;

                  return (
                    <button
                      key={project.project_id}
                      type="button"
                      role="option"
                      aria-selected={isSelected}
                      onClick={() => handleSelectProject(project.project_id)}
                      disabled={pendingProjectId !== null}
                      className={cn(
                        'flex w-full items-center gap-3 rounded-[1rem] px-3 py-2.5 text-left text-sm transition-colors hover:bg-primary/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/60 focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-wait disabled:opacity-70',
                        isSelected ? 'bg-primary/10 text-primary' : 'text-foreground'
                      )}
                    >
                      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/15 text-xs font-bold text-primary">
                        {project.name.charAt(0).toUpperCase()}
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block truncate font-medium">{project.name}</span>
                        <span className="block truncate text-xs text-muted-foreground">
                          {project.owner_login}
                        </span>
                      </span>
                      {isPending ? (
                        <div className="h-4 w-4 rounded-full border-2 border-border border-t-primary animate-spin" />
                      ) : isSelected ? (
                        <Check className="h-4 w-4 text-primary" />
                      ) : null}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
