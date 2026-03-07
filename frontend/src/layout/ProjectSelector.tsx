/**
 * ProjectSelector — dropdown overlay for switching between GitHub projects.
 */

import { useEffect, useRef } from 'react';
import type { Project } from '@/types';

interface ProjectSelectorProps {
  isOpen: boolean;
  onClose: () => void;
  projects: Project[];
  selectedProjectId: string | null;
  isLoading: boolean;
  onSelectProject: (projectId: string) => void;
}

export function ProjectSelector({
  isOpen,
  onClose,
  projects,
  selectedProjectId,
  isLoading,
  onSelectProject,
}: ProjectSelectorProps) {
  const ref = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    if (!isOpen) return;
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        onClose();
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [isOpen, onClose]);

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      ref={ref}
      className="celestial-panel absolute bottom-full left-0 right-0 z-50 mb-2 overflow-hidden rounded-[1.25rem] border border-border/80 shadow-lg backdrop-blur-md"
    >
      <div className="border-b border-border/70 px-3 py-3">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-primary/80">Projects</p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center p-5">
          <div className="w-5 h-5 border-2 border-border border-t-primary rounded-full animate-spin" />
        </div>
      ) : projects.length === 0 ? (
        <div className="p-5 text-center">
          <p className="text-sm text-muted-foreground">No projects available</p>
          <p className="text-xs text-muted-foreground/60 mt-1">Connect a GitHub project to get started</p>
        </div>
      ) : (
        <div className="max-h-[280px] overflow-y-auto py-1">
          {projects.map((project) => (
            <button
              key={project.project_id}
              onClick={() => {
                onSelectProject(project.project_id);
                onClose();
              }}
              className={`flex w-full items-center gap-3 px-3 py-2.5 text-left text-sm transition-colors hover:bg-accent/45 ${
                project.project_id === selectedProjectId ? 'bg-primary/10 text-primary' : 'text-foreground'
              }`}
            >
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/15 text-xs font-bold text-primary">
                {project.name.charAt(0).toUpperCase()}
              </span>
              <div className="flex flex-col min-w-0">
                <span className="font-medium truncate">{project.name}</span>
                <span className="text-xs text-muted-foreground truncate">{project.owner_login}</span>
              </div>
              {project.project_id === selectedProjectId && (
                <span className="ml-auto text-primary text-xs">✓</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
