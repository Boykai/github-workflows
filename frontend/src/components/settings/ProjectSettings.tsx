/**
 * Project Settings component.
 *
 * Per-project board config and agent pipeline mappings. Includes a
 * project selector dropdown to switch between projects.
 */

import { useState, useEffect } from 'react';
import { SettingsSection } from './SettingsSection';
import { useProjectSettings } from '@/hooks/useSettings';
import type {
  ProjectSettingsUpdate,
  ProjectBoardConfig,
  ProjectAgentMapping,
} from '@/types';

interface ProjectSettingsProps {
  /** List of available projects from the sidebar */
  projects: Array<{ project_id: string; name: string }>;
  /** Currently selected project ID from session context */
  selectedProjectId?: string;
}

export function ProjectSettings({ projects, selectedProjectId }: ProjectSettingsProps) {
  const [projectId, setProjectId] = useState(selectedProjectId ?? '');
  const { settings, isLoading, updateSettings } = useProjectSettings(projectId || undefined);

  // Board config local state
  const [columnOrder, setColumnOrder] = useState('');
  const [collapsedColumns, setCollapsedColumns] = useState('');
  const [showEstimates, setShowEstimates] = useState(false);

  // Agent mappings as JSON text for simplicity
  const [agentMappingsText, setAgentMappingsText] = useState('');

  // Sync local state from loaded settings
  useEffect(() => {
    if (!settings?.project) return;
    const ps = settings.project;

    if (ps.board_display_config) {
      setColumnOrder(ps.board_display_config.column_order.join(', '));
      setCollapsedColumns(ps.board_display_config.collapsed_columns.join(', '));
      setShowEstimates(ps.board_display_config.show_estimates);
    } else {
      setColumnOrder('');
      setCollapsedColumns('');
      setShowEstimates(false);
    }

    if (ps.agent_pipeline_mappings) {
      setAgentMappingsText(JSON.stringify(ps.agent_pipeline_mappings, null, 2));
    } else {
      setAgentMappingsText('');
    }
  }, [settings?.project]);

  // Sync project selector with external selection
  useEffect(() => {
    if (selectedProjectId) setProjectId(selectedProjectId);
  }, [selectedProjectId]);

  const buildBoardConfig = (): ProjectBoardConfig => ({
    column_order: columnOrder
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean),
    collapsed_columns: collapsedColumns
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean),
    show_estimates: showEstimates,
  });

  const parseAgentMappings = (): Record<string, ProjectAgentMapping[]> | null => {
    if (!agentMappingsText.trim()) return null;
    try {
      return JSON.parse(agentMappingsText);
    } catch {
      return null;
    }
  };

  const handleSave = async () => {
    const update: ProjectSettingsUpdate = {
      board_display_config: buildBoardConfig(),
      agent_pipeline_mappings: parseAgentMappings(),
    };
    await updateSettings(update);
  };

  if (!projects.length) {
    return (
      <SettingsSection
        title="Project Settings"
        description="Per-project board configuration and agent mappings."
        hideSave
      >
        <p className="text-sm text-muted-foreground italic">No projects available. Select a project first.</p>
      </SettingsSection>
    );
  }

  return (
    <SettingsSection
      title="Project Settings"
      description="Per-project board configuration and agent pipeline mappings."
      isDirty={!!projectId}
      onSave={handleSave}
    >
      <div className="flex flex-col gap-2">
        <label htmlFor="project-selector" className="text-sm font-medium text-foreground">Project</label>
        <select
          id="project-selector"
          className="flex h-9 w-full rounded-md border border-input bg-background text-foreground px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          value={projectId}
          onChange={(e) => setProjectId(e.target.value)}
        >
          <option value="">Select a project...</option>
          {projects.map((p) => (
            <option key={p.project_id} value={p.project_id}>
              {p.name}
            </option>
          ))}
        </select>
      </div>

      {isLoading && projectId && <p className="text-sm text-muted-foreground">Loading project settings...</p>}

      {projectId && !isLoading && (
        <>
          <h4 className="text-sm font-semibold text-foreground mt-4 border-b border-border pb-2">Board Display</h4>

          <div className="flex flex-col gap-2">
            <label htmlFor="proj-col-order" className="text-sm font-medium text-foreground">Column Order (comma-separated)</label>
            <input
              id="proj-col-order"
              type="text"
              className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              value={columnOrder}
              onChange={(e) => setColumnOrder(e.target.value)}
              placeholder="Backlog, Ready, In Progress, Done"
            />
          </div>

          <div className="flex flex-col gap-2">
            <label htmlFor="proj-collapsed" className="text-sm font-medium text-foreground">Collapsed Columns (comma-separated)</label>
            <input
              id="proj-collapsed"
              type="text"
              className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              value={collapsedColumns}
              onChange={(e) => setCollapsedColumns(e.target.value)}
              placeholder="Done"
            />
          </div>

          <div className="flex items-center gap-2">
            <label className="flex items-center gap-2 text-sm font-medium text-foreground cursor-pointer">
              <input
                type="checkbox"
                className="w-4 h-4 rounded border-input text-primary focus:ring-primary"
                checked={showEstimates}
                onChange={(e) => setShowEstimates(e.target.checked)}
              />
              Show estimates
            </label>
          </div>

          <h4 className="text-sm font-semibold text-foreground mt-4 border-b border-border pb-2">Agent Pipeline Mappings</h4>

          <div className="flex flex-col gap-2">
            <label htmlFor="proj-agents" className="text-sm font-medium text-foreground">JSON (status → agent list)</label>
            <textarea
              id="proj-agents"
              className="flex min-h-[80px] w-full rounded-md border border-input bg-background text-foreground px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring font-mono"
              rows={6}
              value={agentMappingsText}
              onChange={(e) => setAgentMappingsText(e.target.value)}
              placeholder='{"Backlog": [{"slug": "speckit.specify"}]}'
            />
          </div>
        </>
      )}
    </SettingsSection>
  );
}
