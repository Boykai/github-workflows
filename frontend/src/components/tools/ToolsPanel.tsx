/**
 * ToolsPanel — container for the Tools page MCP tool catalog.
 *
 * Shows tool cards, empty state, search, and upload action.
 * Mirrors AgentsPanel pattern.
 */

import { useDeferredValue, useMemo, useState } from 'react';
import { Search, Wrench } from 'lucide-react';
import { useToolsList } from '@/hooks/useTools';
import { useRepoMcpConfig } from '@/hooks/useRepoMcpConfig';
import { useMcpPresets } from '@/hooks/useMcpPresets';
import { useConfirmation } from '@/hooks/useConfirmation';
import { ToolCard } from './ToolCard';
import { EditRepoMcpModal } from './EditRepoMcpModal';
import { UploadMcpModal } from './UploadMcpModal';
import { RepoConfigPanel } from './RepoConfigPanel';
import { McpPresetsGallery } from './McpPresetsGallery';
import { GitHubToolsetSelector } from './GitHubToolsetSelector';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import type { McpPreset, McpToolConfig, McpToolConfigCreate, RepoMcpServerConfig } from '@/types';

interface ToolsPanelProps {
  projectId: string;
}

export function ToolsPanel({ projectId }: ToolsPanelProps) {
  const { confirm } = useConfirmation();
  const {
    tools,
    isLoading,
    error,
    uploadTool,
    isUploading,
    uploadError,
    resetUploadError,
    updateTool,
    isUpdating,
    updateError,
    resetUpdateError,
    syncTool,
    syncingId,
    deleteTool,
    deletingId,
    deleteResult,
  } = useToolsList(projectId);

  const [showUploadModal, setShowUploadModal] = useState(false);
  const [editingTool, setEditingTool] = useState<McpToolConfig | null>(null);
  const [editingRepoServer, setEditingRepoServer] = useState<RepoMcpServerConfig | null>(null);
  const [draftTool, setDraftTool] = useState<Partial<McpToolConfigCreate> | null>(null);
  const [search, setSearch] = useState('');
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const deferredSearch = useDeferredValue(search);
  const {
    repoConfig,
    isLoading: isRepoConfigLoading,
    error: repoConfigError,
    refetch: refetchRepoConfig,
    updateRepoServer,
    isUpdating: isRepoServerUpdating,
    updatingServerName,
    updateError: repoServerUpdateError,
    resetUpdateError: resetRepoServerUpdateError,
    deleteRepoServer,
    isDeleting: isRepoServerDeleting,
    deletingServerName,
    deleteError: repoServerDeleteError,
    resetDeleteError: resetRepoServerDeleteError,
  } = useRepoMcpConfig(projectId);
  const { presets, isLoading: arePresetsLoading, error: presetsError } = useMcpPresets();

  const managedToolByServerName = useMemo(() => {
    const index = new Map<string, McpToolConfig>();

    tools.forEach((tool) => {
      try {
        const parsed = JSON.parse(tool.config_content) as { mcpServers?: Record<string, unknown> };
        Object.keys(parsed.mcpServers ?? {}).forEach((serverName) => {
          index.set(serverName, tool);
        });
      } catch {
        // Ignore invalid tool payloads and keep rendering the page.
      }
    });

    return index;
  }, [tools]);

  const handleOpenCreate = () => {
    resetUploadError();
    resetUpdateError();
    resetRepoServerUpdateError();
    setEditingTool(null);
    setEditingRepoServer(null);
    setDraftTool(null);
    setShowUploadModal(true);
  };

  const handleOpenEdit = (tool: McpToolConfig) => {
    resetUploadError();
    resetUpdateError();
    resetRepoServerUpdateError();
    setEditingTool(tool);
    setEditingRepoServer(null);
    setDraftTool(null);
    setShowUploadModal(true);
  };

  const handlePresetSelect = (preset: McpPreset) => {
    resetUploadError();
    resetUpdateError();
    resetRepoServerUpdateError();
    setEditingTool(null);
    setEditingRepoServer(null);
    setDraftTool({
      name: preset.name,
      description: preset.description,
      config_content: preset.config_content,
      github_repo_target: '',
    });
    setShowUploadModal(true);
  };

  const filteredTools = tools.filter((tool) => {
    const query = deferredSearch.trim().toLowerCase();
    if (query.length === 0) return true;
    return (
      tool.name.toLowerCase().includes(query) || tool.description.toLowerCase().includes(query)
    );
  });

  const handleDelete = async (toolId: string) => {
    // First check for affected agents; backend deletes immediately when none are affected.
    const result = await deleteTool({ toolId, confirm: false });
    if (!result.success && result.affected_agents.length > 0) {
      setDeleteConfirmId(toolId);
    }
  };

  const handleConfirmDelete = async () => {
    if (!deleteConfirmId) return;
    await deleteTool({ toolId: deleteConfirmId, confirm: true });
    setDeleteConfirmId(null);
  };

  const handleEditRepoServer = (server: RepoMcpServerConfig) => {
    const managedTool = managedToolByServerName.get(server.name);
    if (managedTool) {
      handleOpenEdit(managedTool);
      return;
    }

    resetRepoServerUpdateError();
    setEditingTool(null);
    setDraftTool(null);
    setEditingRepoServer(server);
  };

  const handleDeleteRepoServer = async (server: RepoMcpServerConfig) => {
    const managedTool = managedToolByServerName.get(server.name);
    if (managedTool) {
      await handleDelete(managedTool.id);
      return;
    }

    resetRepoServerDeleteError();
    const confirmed = await confirm({
      title: 'Delete Repository MCP',
      description: `Remove MCP server "${server.name}" from the repository config files?`,
      variant: 'danger',
      confirmLabel: 'Delete',
    });
    if (!confirmed) {
      return;
    }

    try {
      await deleteRepoServer(server.name);
    } catch {
      // Mutation state already surfaces the error in the panel.
    }
  };

  return (
    <div className="celestial-fade-in flex min-w-0 flex-col gap-6">
      <RepoConfigPanel
        repoConfig={repoConfig}
        isLoading={isRepoConfigLoading}
        error={repoConfigError}
        onRefresh={() => {
          void refetchRepoConfig();
        }}
        onEdit={handleEditRepoServer}
        onDelete={(server) => {
          void handleDeleteRepoServer(server);
        }}
        editingServerName={isRepoServerUpdating ? updatingServerName : editingRepoServer?.name}
        deletingServerName={isRepoServerDeleting ? deletingServerName : null}
        managedServerNames={[...managedToolByServerName.keys()]}
      />

      {repoServerDeleteError && (
        <div className="rounded-[1.25rem] border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
          {repoServerDeleteError}
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-[1.2fr_1fr]">
        <McpPresetsGallery
          presets={presets}
          isLoading={arePresetsLoading}
          error={presetsError}
          onSelectPreset={handlePresetSelect}
        />
        <GitHubToolsetSelector onCreate={uploadTool} isSubmitting={isUploading || isUpdating} />
      </div>

      <div className="ritual-stage flex flex-col gap-4 rounded-[1.55rem] p-4 sm:rounded-[1.8rem] sm:p-6 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-[11px] uppercase tracking-[0.24em] text-primary/80">Tool archive</p>
          <h3 className="mt-2 text-[1.55rem] font-display font-medium leading-tight sm:text-[1.9rem]">
            MCP Tools
          </h3>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
            Manage MCP configurations that sync to your repository and can be attached to Custom
            Agents.
          </p>
        </div>
        <Button onClick={handleOpenCreate} size="lg">
          + Upload MCP Config
        </Button>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-40 rounded-[1.4rem] border border-border bg-background/40 animate-pulse"
            />
          ))}
        </div>
      )}

      {/* Error state */}
      {error && !isLoading && (
        <div className="flex flex-col items-center gap-2 rounded-[1.4rem] border border-destructive/30 bg-destructive/5 p-6 text-center">
          <span className="text-sm text-destructive">Failed to load tools</span>
          <p className="text-xs text-muted-foreground">{error}</p>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !error && tools.length === 0 && (
        <div className="celestial-panel flex flex-col items-center gap-3 rounded-[1.5rem] border-2 border-dashed border-border bg-background/28 p-8 text-center">
          <Wrench className="h-8 w-8 text-muted-foreground/50" />
          <p className="text-lg font-medium text-foreground">No MCP tools configured yet</p>
          <p className="max-w-md text-sm text-muted-foreground">
            Upload your first MCP configuration to get started. Configurations will sync to your
            repository and become available when attached to a Custom Agent.
          </p>
          <Button onClick={handleOpenCreate}>Upload your first MCP config</Button>
        </div>
      )}

      {/* Tool list with search */}
      {!isLoading && !error && tools.length > 0 && (
        <section className="ritual-stage scroll-mt-6 rounded-[1.55rem] p-4 sm:rounded-[1.85rem] sm:p-6">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
            <div>
              <p className="text-[11px] uppercase tracking-[0.24em] text-primary/80">
                Catalog controls
              </p>
              <h4 className="mt-2 text-[1.35rem] font-display font-medium leading-tight sm:text-[1.6rem]">
                Filter tools
              </h4>
            </div>

            <div className="xl:min-w-[28rem]">
              <div className="relative">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Search by name or description"
                  aria-label="Search tools catalog"
                  className="moonwell h-12 rounded-full border-border/60 pl-10"
                />
              </div>
            </div>
          </div>

          {filteredTools.length === 0 ? (
            <div className="mt-6 rounded-[1.35rem] border border-dashed border-border/80 bg-background/42 p-8 text-center">
              <p className="text-sm text-muted-foreground">No tools match the current filters.</p>
              <Button variant="ghost" className="mt-3" onClick={() => setSearch('')}>
                Reset filters
              </Button>
            </div>
          ) : (
            <div className="constellation-grid mt-6 grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
              {filteredTools.map((tool) => (
                <ToolCard
                  key={tool.id}
                  tool={tool}
                  onEdit={handleOpenEdit}
                  onSync={(id) => syncTool(id)}
                  onDelete={handleDelete}
                  isSyncing={syncingId === tool.id}
                  isDeleting={deletingId === tool.id}
                />
              ))}
            </div>
          )}
        </section>
      )}

      {/* Delete confirmation with affected agents */}
      {deleteConfirmId &&
        deleteResult &&
        !deleteResult.success &&
        deleteResult.affected_agents.length > 0 && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
            role="presentation"
            onClick={() => setDeleteConfirmId(null)}
          >
            <div
              className="bg-card rounded-lg border border-border shadow-lg p-6 w-full max-w-md"
              role="presentation"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold mb-2">Tool in use</h3>
              <p className="text-sm text-muted-foreground mb-3">
                This tool is assigned to the following agents:
              </p>
              <ul className="mb-4 space-y-1">
                {deleteResult.affected_agents.map((agent) => (
                  <li key={agent.id} className="text-sm font-medium">
                    • {agent.name}
                  </li>
                ))}
              </ul>
              <p className="text-sm text-muted-foreground mb-4">
                Deleting it will remove it from these agents. Are you sure?
              </p>
              <div className="flex justify-end gap-2">
                <button
                  className="solar-action rounded-full px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
                  onClick={() => setDeleteConfirmId(null)}
                >
                  Cancel
                </button>
                <button
                  className="px-4 py-2 text-sm font-medium rounded-md bg-destructive text-destructive-foreground hover:bg-destructive/90"
                  onClick={handleConfirmDelete}
                >
                  Delete anyway
                </button>
              </div>
            </div>
          </div>
        )}

      {/* Upload Modal */}
      <UploadMcpModal
        isOpen={showUploadModal}
        onClose={() => {
          setShowUploadModal(false);
          setEditingTool(null);
          setEditingRepoServer(null);
          setDraftTool(null);
        }}
        onUpload={uploadTool}
        onUpdate={(toolId, data) => updateTool({ toolId, data })}
        isSubmitting={isUploading || isUpdating}
        submitError={uploadError ?? updateError}
        existingNames={tools.map((t) => t.name)}
        editingTool={editingTool}
        initialDraft={draftTool}
      />

      <EditRepoMcpModal
        isOpen={editingRepoServer !== null}
        server={editingRepoServer}
        isSubmitting={isRepoServerUpdating}
        submitError={repoServerUpdateError}
        onClose={() => {
          setEditingRepoServer(null);
        }}
        onSave={(serverName, data) => updateRepoServer({ serverName, data })}
      />
    </div>
  );
}
