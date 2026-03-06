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
      className="absolute bottom-full left-0 right-0 mb-1 bg-card border border-border rounded-lg shadow-lg overflow-hidden z-50"
    >
      <div className="px-3 py-2 border-b border-border">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Projects</p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center p-4">
          <div className="w-5 h-5 border-2 border-border border-t-primary rounded-full animate-spin" />
        </div>
      ) : projects.length === 0 ? (
        <div className="p-4 text-center">
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
              className={`flex items-center gap-3 w-full px-3 py-2 text-sm text-left hover:bg-muted transition-colors ${
                project.project_id === selectedProjectId ? 'bg-primary/5 text-primary' : 'text-foreground'
              }`}
            >
              <span className="w-6 h-6 rounded-md bg-primary/20 text-primary flex items-center justify-center text-xs font-bold shrink-0">
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
