/**
 * ProjectSelector — dropdown overlay for switching between GitHub projects.
 */

import { useEffect, useRef, useState } from 'react';
import { Check, Plus } from '@/lib/icons';
import { cn } from '@/lib/utils';
import { useOwners } from '@/hooks/useApps';
import { useCreateProject } from '@/hooks/useProjects';
import type { Project } from '@/types';

interface ProjectSelectorProps {
  isOpen: boolean;
  onClose: () => void;
  projects: Project[];
  selectedProjectId: string | null;
  isLoading: boolean;
  onSelectProject: (projectId: string) => void;
  className?: string;
}

export function ProjectSelector({
  isOpen,
  onClose,
  projects,
  selectedProjectId,
  isLoading,
  onSelectProject,
  className,
}: ProjectSelectorProps) {
  const ref = useRef<HTMLDivElement>(null);
  const titleInputRef = useRef<HTMLInputElement>(null);
  const [showNewProjectDialog, setShowNewProjectDialog] = useState(false);
  const [newProjectTitle, setNewProjectTitle] = useState('');
  const [newProjectOwner, setNewProjectOwner] = useState('');
  const [newProjectError, setNewProjectError] = useState<string | null>(null);
  const { data: owners } = useOwners();
  const createProject = useCreateProject();

  // Set default owner when owners load
  const [prevOwnersLength, setPrevOwnersLength] = useState(owners?.length ?? 0);
  if ((owners?.length ?? 0) !== prevOwnersLength) {
    setPrevOwnersLength(owners?.length ?? 0);
    if (owners && owners.length > 0 && !newProjectOwner) {
      setNewProjectOwner(owners[0].login);
    }
  }

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
      if (e.key === 'Escape') {
        if (showNewProjectDialog) {
          setShowNewProjectDialog(false);
        } else {
          onClose();
        }
      }
    }
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [isOpen, onClose, showNewProjectDialog]);

  // Reset form state when the selector closes
  const [prevSelectorIsOpen, setPrevSelectorIsOpen] = useState(isOpen);
  if (isOpen !== prevSelectorIsOpen) {
    setPrevSelectorIsOpen(isOpen);
    if (!isOpen) {
      setShowNewProjectDialog(false);
      setNewProjectTitle('');
      setNewProjectError(null);
    }
  }

  // Focus the title input when the new-project form opens
  useEffect(() => {
    if (showNewProjectDialog) {
      titleInputRef.current?.focus();
    }
  }, [showNewProjectDialog]);

  const handleCreateProject = () => {
    if (!newProjectTitle.trim()) {
      setNewProjectError('Project title is required.');
      return;
    }
    if (!newProjectOwner) {
      setNewProjectError('Owner is required.');
      return;
    }
    setNewProjectError(null);
    createProject.mutate(
      { title: newProjectTitle.trim(), owner: newProjectOwner },
      {
        onSuccess: (data) => {
          setShowNewProjectDialog(false);
          setNewProjectTitle('');
          // Auto-select the new project
          if (data.project_id) {
            onSelectProject(data.project_id);
          }
          onClose();
        },
        onError: () => {
          setNewProjectError('Failed to create project. Please try again.');
        },
      }
    );
  };

  if (!isOpen) return null;

  return (
    <div
      ref={ref}
      className={cn(
        'celestial-panel absolute bottom-full left-0 right-0 z-50 mb-2 overflow-hidden rounded-[1.25rem] border border-border/80 shadow-lg backdrop-blur-md',
        className
      )}
    >
      <div className="border-b border-border/70 bg-background/25 px-3 py-3">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-primary/80">
          Projects
        </p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center p-5">
          <div className="w-5 h-5 border-2 border-border border-t-primary rounded-full animate-spin" />
        </div>
      ) : projects.length === 0 ? (
        <div className="p-5 text-center">
          <p className="text-sm text-muted-foreground">No projects available</p>
          <p className="text-xs text-muted-foreground/60 mt-1">
            Connect a GitHub project to get started
          </p>
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
              className={cn('flex w-full items-center gap-3 px-3 py-2.5 text-left text-sm transition-colors hover:bg-primary/10', project.project_id === selectedProjectId
                  ? 'bg-primary/10 text-primary'
                  : 'text-foreground')}
            >
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/15 text-xs font-bold text-primary">
                {project.name.charAt(0).toUpperCase()}
              </span>
              <div className="flex flex-col min-w-0">
                <span className="font-medium truncate">{project.name}</span>
                <span className="text-xs text-muted-foreground truncate">
                  {project.owner_login}
                </span>
              </div>
              {project.project_id === selectedProjectId && (
                <Check className="ml-auto h-3.5 w-3.5 text-primary" />
              )}
            </button>
          ))}
        </div>
      )}

      {/* New Project option */}
      <div className="border-t border-border/70">
        {!showNewProjectDialog ? (
          <button
            type="button"
            onClick={() => setShowNewProjectDialog(true)}
            className="flex w-full items-center gap-2 px-3 py-2.5 text-left text-sm font-medium text-primary hover:bg-primary/10 transition-colors"
          >
            <Plus className="h-4 w-4" /> New Project
          </button>
        ) : (
          <div className="p-3 space-y-2">
            <p className="text-xs font-semibold text-zinc-500 dark:text-zinc-400">Create New Project</p>
            {newProjectError && (
              <p className="text-xs text-red-500">{newProjectError}</p>
            )}
            <input
              ref={titleInputRef}
              type="text"
              placeholder="Project title"
              aria-label="Project title"
              value={newProjectTitle}
              onChange={(e) => setNewProjectTitle(e.target.value)}
              className="w-full rounded-md border border-zinc-300 px-2.5 py-1.5 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
            />
            <select
              value={newProjectOwner}
              onChange={(e) => setNewProjectOwner(e.target.value)}
              aria-label="Project owner"
              className="w-full rounded-md border border-zinc-300 px-2.5 py-1.5 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
            >
              {(owners ?? []).map((o) => (
                <option key={o.login} value={o.login}>
                  {o.login} ({o.type})
                </option>
              ))}
            </select>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => {
                  setShowNewProjectDialog(false);
                  setNewProjectTitle('');
                  setNewProjectError(null);
                }}
                className="flex-1 rounded-md border border-zinc-300 px-2 py-1 text-xs font-medium text-zinc-600 hover:bg-zinc-100 dark:border-zinc-600 dark:text-zinc-400 dark:hover:bg-zinc-800"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleCreateProject}
                disabled={createProject.isPending}
                className="flex-1 rounded-md bg-primary px-2 py-1 text-xs font-medium text-white hover:bg-primary/90 disabled:opacity-50"
              >
                {createProject.isPending ? 'Creating…' : 'Create'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
