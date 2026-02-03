/**
 * Project selector dropdown component.
 */

import type { Project } from '@/types';

interface ProjectSelectorProps {
  projects: Project[];
  selectedProjectId: string | null;
  onSelect: (projectId: string) => void;
  isLoading?: boolean;
}

export function ProjectSelector({
  projects,
  selectedProjectId,
  onSelect,
  isLoading,
}: ProjectSelectorProps) {
  const selectedProject = projects.find((p) => p.project_id === selectedProjectId);

  return (
    <div className="project-selector">
      <label htmlFor="project-select" className="sr-only">
        Select Project
      </label>
      <select
        id="project-select"
        value={selectedProjectId ?? ''}
        onChange={(e) => onSelect(e.target.value)}
        disabled={isLoading || projects.length === 0}
        className="project-select"
      >
        <option value="" disabled>
          {isLoading ? 'Loading projects...' : 'Select a project'}
        </option>
        {projects.map((project) => (
          <option key={project.project_id} value={project.project_id}>
            {getProjectLabel(project)}
          </option>
        ))}
      </select>
      {selectedProject && (
        <a
          href={selectedProject.url}
          target="_blank"
          rel="noopener noreferrer"
          className="project-link"
          title="Open in GitHub"
        >
          ↗
        </a>
      )}
    </div>
  );
}

function getProjectLabel(project: Project): string {
  const typeIcon = {
    organization: '🏢',
    user: '👤',
    repository: '📁',
  }[project.type];

  return `${typeIcon} ${project.owner_login} / ${project.name}`;
}
