/**
 * ToolsPanel — container for the Tools page MCP tool catalog.
 *
 * Shows tool cards, empty state, search, and upload action.
 * Mirrors AgentsPanel pattern.
 */

import { useDeferredValue, useState } from 'react';
import { Search, Wrench } from 'lucide-react';
import { useToolsList } from '@/hooks/useTools';
import { ToolCard } from './ToolCard';
import { UploadMcpModal } from './UploadMcpModal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface ToolsPanelProps {
  projectId: string;
}

export function ToolsPanel({ projectId }: ToolsPanelProps) {
  const {
    tools,
    isLoading,
    error,
    uploadTool,
    isUploading,
    uploadError,
    resetUploadError,
    syncTool,
    syncingId,
    deleteTool,
    deletingId,
    deleteResult,
  } = useToolsList(projectId);

  const [showUploadModal, setShowUploadModal] = useState(false);
  const [search, setSearch] = useState('');
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const deferredSearch = useDeferredValue(search);

  const filteredTools = tools.filter((tool) => {
    const query = deferredSearch.trim().toLowerCase();
    if (query.length === 0) return true;
    return (
      tool.name.toLowerCase().includes(query) ||
      tool.description.toLowerCase().includes(query)
    );
  });

  const handleDelete = async (toolId: string) => {
    // First check for affected agents
    const result = await deleteTool({ toolId, confirm: false });
    if (!result.success && result.affected_agents.length > 0) {
      setDeleteConfirmId(toolId);
    } else if (!result.success) {
      // No affected agents but need confirmation
      const confirmed = window.confirm('Are you sure you want to delete this MCP tool?');
      if (confirmed) {
        await deleteTool({ toolId, confirm: true });
      }
    }
  };

  const handleConfirmDelete = async () => {
    if (!deleteConfirmId) return;
    await deleteTool({ toolId: deleteConfirmId, confirm: true });
    setDeleteConfirmId(null);
  };

  return (
    <div className="flex min-w-0 flex-col gap-6">
      <div className="ritual-stage flex flex-col gap-4 rounded-[1.55rem] p-4 sm:rounded-[1.8rem] sm:p-6 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-[11px] uppercase tracking-[0.24em] text-primary/80">Tool archive</p>
          <h3 className="mt-2 text-[1.55rem] font-display font-medium leading-tight sm:text-[1.9rem]">MCP Tools</h3>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
            Manage MCP configurations that sync to your GitHub repository for use by Custom Agents.
          </p>
        </div>
        <Button onClick={() => { resetUploadError(); setShowUploadModal(true); }} size="lg">
          + Upload MCP Config
        </Button>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-40 rounded-[1.4rem] border border-border bg-muted/30 animate-pulse"
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
        <div className="flex flex-col items-center gap-3 rounded-[1.5rem] border-2 border-dashed border-border bg-muted/10 p-8 text-center">
          <Wrench className="h-8 w-8 text-muted-foreground/50" />
          <p className="text-lg font-medium text-foreground">No MCP tools configured yet</p>
          <p className="max-w-md text-sm text-muted-foreground">
            Upload your first MCP configuration to get started. Configurations will be synced to your GitHub repository for use by Custom Agents.
          </p>
          <Button onClick={() => { resetUploadError(); setShowUploadModal(true); }}>
            Upload your first MCP config
          </Button>
        </div>
      )}

      {/* Tool list with search */}
      {!isLoading && !error && tools.length > 0 && (
        <section className="ritual-stage scroll-mt-6 rounded-[1.55rem] p-4 sm:rounded-[1.85rem] sm:p-6">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
            <div>
              <p className="text-[11px] uppercase tracking-[0.24em] text-primary/80">Catalog controls</p>
              <h4 className="mt-2 text-[1.35rem] font-display font-medium leading-tight sm:text-[1.6rem]">Filter tools</h4>
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
            <div className="mt-6 rounded-[1.35rem] border border-dashed border-border/80 bg-background/35 p-8 text-center">
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
      {deleteConfirmId && deleteResult && !deleteResult.success && deleteResult.affected_agents.length > 0 && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" role="presentation" onClick={() => setDeleteConfirmId(null)}>
          <div className="bg-card rounded-lg border border-border shadow-lg p-6 w-full max-w-md" role="presentation" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-semibold mb-2">Tool in use</h3>
            <p className="text-sm text-muted-foreground mb-3">
              This tool is assigned to the following agents:
            </p>
            <ul className="mb-4 space-y-1">
              {deleteResult.affected_agents.map((agent) => (
                <li key={agent.id} className="text-sm font-medium">• {agent.name}</li>
              ))}
            </ul>
            <p className="text-sm text-muted-foreground mb-4">
              Deleting it will remove it from these agents. Are you sure?
            </p>
            <div className="flex justify-end gap-2">
              <button
                className="px-4 py-2 text-sm font-medium rounded-md bg-muted hover:bg-muted/80 text-muted-foreground"
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
        onClose={() => setShowUploadModal(false)}
        onUpload={uploadTool}
        isUploading={isUploading}
        uploadError={uploadError}
        existingNames={tools.map((t) => t.name)}
      />
    </div>
  );
}
