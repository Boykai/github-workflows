import { Pencil, Trash2 } from 'lucide-react';
import type { RepoMcpConfigResponse, RepoMcpServerConfig } from '@/types';
import { Button } from '@/components/ui/button';
import { Tooltip } from '@/components/ui/tooltip';

interface RepoConfigPanelProps {
  repoConfig: RepoMcpConfigResponse | null;
  isLoading: boolean;
  error: string | null;
  onRefresh: () => void;
  onEdit: (server: RepoMcpServerConfig) => void;
  onDelete: (server: RepoMcpServerConfig) => void;
  editingServerName?: string | null;
  deletingServerName?: string | null;
  managedServerNames?: string[];
}

function summarizeServer(config: Record<string, unknown>) {
  const type = typeof config.type === 'string' ? config.type : 'unknown';
  const url = typeof config.url === 'string' ? config.url : null;
  const command = typeof config.command === 'string' ? config.command : null;
  return { type, detail: url ?? command ?? 'No endpoint defined' };
}

export function RepoConfigPanel({
  repoConfig,
  isLoading,
  error,
  onRefresh,
  onEdit,
  onDelete,
  editingServerName,
  deletingServerName,
  managedServerNames = [],
}: RepoConfigPanelProps) {
  return (
    <section className="ritual-stage rounded-[1.55rem] p-4 sm:rounded-[1.85rem] sm:p-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-[11px] uppercase tracking-[0.24em] text-primary/80">Repository MCP</p>
          <h4 className="mt-2 text-[1.35rem] font-display font-medium leading-tight sm:text-[1.6rem]">
            Current repository config
          </h4>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
            Live view of MCP servers discovered in the repository. The app now syncs both
            `.copilot/mcp.json` and `.vscode/mcp.json`.
          </p>
        </div>
        <button
          type="button"
          onClick={onRefresh}
          className="solar-action rounded-full px-4 py-2 text-sm font-medium text-foreground"
        >
          Refresh
        </button>
      </div>

      <div className="mt-4 flex flex-wrap gap-2 text-xs text-muted-foreground">
        {(repoConfig?.paths_checked ?? []).map((path) => {
          const active = repoConfig?.available_paths.includes(path);
          return (
            <span
              key={path}
              className={`rounded-full border px-3 py-1 ${active ? 'border-primary/50 bg-primary/10 text-foreground' : 'border-border/60 bg-background/45'}`}
            >
              {path}
            </span>
          );
        })}
      </div>

      {isLoading && (
        <div className="mt-6 text-sm text-muted-foreground">Loading repository MCP config…</div>
      )}
      {error && !isLoading && (
        <div className="mt-6 rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      {!isLoading && !error && repoConfig && repoConfig.servers.length === 0 && (
        <div className="mt-6 rounded-[1.35rem] border border-dashed border-border/80 bg-background/42 p-6 text-sm text-muted-foreground">
          No MCP servers found in the repository yet.
        </div>
      )}

      {!isLoading && !error && repoConfig && repoConfig.servers.length > 0 && (
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {repoConfig.servers.map((server) => {
            const summary = summarizeServer(server.config);
            return (
              <article
                key={server.name}
                className="rounded-[1.35rem] border border-border/70 bg-background/40 p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h5 className="text-base font-medium text-foreground">{server.name}</h5>
                      <span className="rounded-full border border-border/60 px-2 py-1 text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                        {managedServerNames.includes(server.name) ? 'Managed' : 'Repo only'}
                      </span>
                    </div>
                    <p className="mt-1 text-xs uppercase tracking-[0.22em] text-primary/80">
                      {summary.type}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <div className="flex items-center gap-1">
                      <Tooltip contentKey="tools.card.editButton">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0 hover:bg-primary/10"
                          onClick={() => onEdit(server)}
                          disabled={editingServerName === server.name}
                          aria-label={`Edit repository MCP ${server.name}`}
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </Button>
                      </Tooltip>
                      <Tooltip contentKey="tools.card.deleteButton">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="solar-action-danger h-7 w-7 p-0"
                          onClick={() => onDelete(server)}
                          disabled={deletingServerName === server.name}
                          aria-label={`Delete repository MCP ${server.name}`}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </Tooltip>
                    </div>
                    <div className="flex flex-wrap justify-end gap-2 text-[11px] text-muted-foreground">
                      {server.source_paths.map((path) => (
                        <span key={path} className="rounded-full border border-border/60 px-2 py-1">
                          {path}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
                <p className="mt-3 break-all text-sm text-muted-foreground">{summary.detail}</p>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
