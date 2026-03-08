/**
 * ToolCard — displays a single MCP tool configuration with sync status and actions.
 */

import { Pencil, RefreshCw, Trash2, Wrench } from 'lucide-react';
import type { McpToolConfig } from '@/types';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tooltip } from '@/components/ui/tooltip';

interface ToolCardProps {
  tool: McpToolConfig;
  onEdit: (tool: McpToolConfig) => void;
  onSync: (toolId: string) => void;
  onDelete: (toolId: string) => void;
  isSyncing?: boolean;
  isDeleting?: boolean;
}

function SyncStatusBadge({ status, error }: { status: string; error?: string }) {
  const styles: Record<string, string> = {
    synced: 'solar-chip-success',
    pending: 'solar-chip-warning',
    error: 'solar-chip-danger',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] shadow-sm ${styles[status] ?? styles.pending}`}
      title={status === 'error' ? error : undefined}
    >
      {status === 'pending' && (
        <span className="h-2.5 w-2.5 rounded-full border-2 border-current border-t-transparent animate-spin" />
      )}
      {status === 'synced' ? 'Synced to GitHub' : status === 'error' ? 'Sync Error' : 'Pending'}
    </span>
  );
}

export function ToolCard({ tool, onEdit, onSync, onDelete, isSyncing, isDeleting }: ToolCardProps) {
  return (
    <Card className="moonwell rounded-[1.35rem] border-border/75 shadow-none transition-colors hover:border-primary/20">
      <CardContent className="p-4 sm:p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3 min-w-0">
            <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10">
              <Wrench className="h-4 w-4 text-primary" />
            </div>
            <div className="min-w-0">
              <h4 className="truncate text-sm font-semibold text-foreground">{tool.name}</h4>
              {tool.description && (
                <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">{tool.description}</p>
              )}
            </div>
          </div>
          <SyncStatusBadge status={tool.sync_status} error={tool.sync_error} />
        </div>

        {tool.sync_status === 'error' && tool.sync_error && (
          <div className="mt-3 rounded-lg border border-destructive/20 bg-destructive/5 p-2.5">
            <p className="text-xs text-destructive">{tool.sync_error}</p>
          </div>
        )}

        {tool.github_repo_target && (
          <p className="mt-3 truncate text-[10px] uppercase tracking-[0.16em] text-muted-foreground/70">
            Target: {tool.github_repo_target}
          </p>
        )}

        <div className="mt-3 flex items-center justify-between">
          <span className="text-[10px] text-muted-foreground/60">
            {tool.synced_at
              ? `Synced ${new Date(tool.synced_at).toLocaleDateString()}`
              : `Created ${new Date(tool.created_at).toLocaleDateString()}`}
          </span>
          <div className="flex items-center gap-1">
            <Tooltip contentKey="tools.card.editButton">
              <Button
                variant="ghost"
                size="sm"
                className="h-7 w-7 p-0 hover:bg-primary/10"
                onClick={() => onEdit(tool)}
                aria-label="Edit tool"
              >
                <Pencil className="h-3.5 w-3.5" />
              </Button>
            </Tooltip>
            <Tooltip contentKey="tools.card.resyncButton">
              <Button
                variant="ghost"
                size="sm"
                className="h-7 w-7 p-0 hover:bg-primary/10"
                onClick={() => onSync(tool.id)}
                disabled={isSyncing}
                aria-label="Re-sync to GitHub"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
              </Button>
            </Tooltip>
            <Tooltip contentKey="tools.card.deleteButton">
              <Button
                variant="ghost"
                size="sm"
                className="solar-action-danger h-7 w-7 p-0"
                onClick={() => onDelete(tool.id)}
                disabled={isDeleting}
                aria-label="Delete tool"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            </Tooltip>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
