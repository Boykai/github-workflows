/**
 * ToolCard — displays a single MCP tool configuration with sync status and actions.
 */

import { RefreshCw, Trash2, Wrench } from 'lucide-react';
import type { McpToolConfig } from '@/types';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface ToolCardProps {
  tool: McpToolConfig;
  onSync: (toolId: string) => void;
  onDelete: (toolId: string) => void;
  isSyncing?: boolean;
  isDeleting?: boolean;
}

function SyncStatusBadge({ status, error }: { status: string; error?: string }) {
  const styles: Record<string, string> = {
    synced: 'bg-emerald-100/80 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300',
    pending: 'bg-amber-100/80 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300',
    error: 'bg-red-100/80 text-red-700 dark:bg-red-950/50 dark:text-red-300',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-medium uppercase tracking-[0.12em] ${styles[status] ?? styles.pending}`}
      title={status === 'error' ? error : undefined}
    >
      {status === 'pending' && (
        <span className="h-2.5 w-2.5 rounded-full border-2 border-current border-t-transparent animate-spin" />
      )}
      {status === 'synced' ? 'Synced to GitHub' : status === 'error' ? 'Sync Error' : 'Pending'}
    </span>
  );
}

export function ToolCard({ tool, onSync, onDelete, isSyncing, isDeleting }: ToolCardProps) {
  return (
    <Card className="moonwell rounded-[1.35rem] border-border/75 shadow-none transition-colors hover:border-border">
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
          <SyncStatusBadge status={tool.syncStatus} error={tool.syncError} />
        </div>

        {tool.syncStatus === 'error' && tool.syncError && (
          <div className="mt-3 rounded-lg bg-destructive/5 border border-destructive/20 p-2.5">
            <p className="text-xs text-destructive">{tool.syncError}</p>
          </div>
        )}

        {tool.githubRepoTarget && (
          <p className="mt-3 truncate text-[10px] uppercase tracking-[0.16em] text-muted-foreground/70">
            Target: {tool.githubRepoTarget}
          </p>
        )}

        <div className="mt-3 flex items-center justify-between">
          <span className="text-[10px] text-muted-foreground/60">
            {tool.syncedAt
              ? `Synced ${new Date(tool.syncedAt).toLocaleDateString()}`
              : `Created ${new Date(tool.createdAt).toLocaleDateString()}`}
          </span>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              className="h-7 w-7 p-0"
              onClick={() => onSync(tool.id)}
              disabled={isSyncing}
              title="Re-sync to GitHub"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 w-7 p-0 text-destructive hover:text-destructive"
              onClick={() => onDelete(tool.id)}
              disabled={isDeleting}
              title="Delete tool"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
