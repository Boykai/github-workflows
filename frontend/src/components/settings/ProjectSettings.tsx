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
        <p className="settings-placeholder">No projects available. Select a project first.</p>
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
      <div className="settings-field">
        <label htmlFor="project-selector">Project</label>
        <select
          id="project-selector"
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

      {isLoading && projectId && <p>Loading project settings...</p>}

      {projectId && !isLoading && (
        <>
          <h4 className="settings-subsection-title">Board Display</h4>

          <div className="settings-field">
            <label htmlFor="proj-col-order">Column Order (comma-separated)</label>
            <input
              id="proj-col-order"
              type="text"
              value={columnOrder}
              onChange={(e) => setColumnOrder(e.target.value)}
              placeholder="Backlog, Ready, In Progress, Done"
            />
          </div>

          <div className="settings-field">
            <label htmlFor="proj-collapsed">Collapsed Columns (comma-separated)</label>
            <input
              id="proj-collapsed"
              type="text"
              value={collapsedColumns}
              onChange={(e) => setCollapsedColumns(e.target.value)}
              placeholder="Done"
            />
          </div>

          <div className="settings-field">
            <label>
              <input
                type="checkbox"
                checked={showEstimates}
                onChange={(e) => setShowEstimates(e.target.checked)}
              />
              Show estimates
            </label>
          </div>

          <h4 className="settings-subsection-title">Agent Pipeline Mappings</h4>

          <div className="settings-field">
            <label htmlFor="proj-agents">JSON (status → agent list)</label>
            <textarea
              id="proj-agents"
              className="settings-textarea"
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
