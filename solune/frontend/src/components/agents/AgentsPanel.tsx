/**
 * AgentsPanel — container for the Agents feature on the project board.
 *
 * Renders below ChoresPanel. Shows agent cards, empty state with docs link,
 * and loading / error states. Mirrors ChoresPanel pattern.
 */

import { useCallback, useDeferredValue, useMemo, useRef, useState } from 'react';
import { Search, Sparkles, RefreshCw } from '@/lib/icons';
import { useAgentsListPaginated, usePendingAgentsList, useClearPendingAgents } from '@/hooks/useAgents';
import { useModels } from '@/hooks/useModels';
import { useConfirmation } from '@/hooks/useConfirmation';
import { AgentCard } from './AgentCard';
import { AddAgentModal } from './AddAgentModal';
import { BulkModelUpdateDialog } from './BulkModelUpdateDialog';
import { AgentInlineEditor, type AgentInlineEditorHandle } from './AgentInlineEditor';
import type { AgentConfig } from '@/services/api';
import { Button } from '@/components/ui/button';
import { Tooltip } from '@/components/ui/tooltip';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { InfiniteScrollContainer } from '@/components/common/InfiniteScrollContainer';
import { useUnsavedChanges } from '@/hooks/useUnsavedChanges';
import { UnsavedChangesDialog } from '@/components/pipeline/UnsavedChangesDialog';
import { ThemedAgentIcon } from '@/components/common/ThemedAgentIcon';
import { formatAgentName } from '@/utils/formatAgentName';

interface AgentsPanelProps {
  projectId: string;
  owner?: string;
  repo?: string;
  agentUsageCounts?: Record<string, number>;
  pipelineConfigCounts?: Record<string, number>;
  pendingSubIssueCounts?: Record<string, number>;
}

type AgentSortMode = 'name' | 'usage';

function getCatalogAgentName(agent: AgentConfig): string {
  return formatAgentName(agent.slug, agent.name, { specKitStyle: 'suffix' });
}

export function AgentsPanel({
  projectId,
  owner,
  repo,
  agentUsageCounts = {},
  pipelineConfigCounts = {},
  pendingSubIssueCounts = {},
}: AgentsPanelProps) {
  const {
    allItems: agents,
    isLoading,
    isError: hasError,
    hasNextPage: agentsHasNextPage,
    isFetchingNextPage: agentsIsFetchingNextPage,
    fetchNextPage: agentsFetchNextPage,
  } = useAgentsListPaginated(projectId);
  const error = hasError ? new Error('Failed to load agents') : null;
  const { data: pendingAgents, isLoading: pendingLoading } = usePendingAgentsList(projectId);
  const { refreshModels, isRefreshing: isRefreshingModels } = useModels();
  const clearPendingMutation = useClearPendingAgents(projectId);
  const { confirm } = useConfirmation();
  const [showAddModal, setShowAddModal] = useState(false);
  const [editAgent, setEditAgent] = useState<AgentConfig | null>(null);
  const [isEditorDirty, setIsEditorDirty] = useState(false);
  const [unsavedDialog, setUnsavedDialog] = useState<{
    isOpen: boolean;
    pendingAction: (() => void) | null;
    description: string;
  }>({ isOpen: false, pendingAction: null, description: '' });
  const [saveResult, setSaveResult] = useState<{ agentName: string; prUrl: string } | null>(null);
  const [search, setSearch] = useState('');
  const [sortMode, setSortMode] = useState<AgentSortMode>('name');
  const [bulkUpdateOpen, setBulkUpdateOpen] = useState(false);
  const deferredSearch = useDeferredValue(search);
  const editorRef = useRef<AgentInlineEditorHandle | null>(null);
  const { blocker, isBlocked } = useUnsavedChanges({
    isDirty: isEditorDirty,
    message: 'You have unsaved agent changes. Save or discard them before leaving this page.',
  });

  const handleClearPending = async () => {
    const confirmed = await confirm({
      title: 'Clear Pending Records',
      description:
        'Delete all pending agent records from the local database for this project? This only removes stale SQLite rows and does not change the repository.',
      variant: 'warning',
      confirmLabel: 'Clear Records',
    });
    if (!confirmed) return;
    clearPendingMutation.mutate();
  };

  const queueUnsavedAction = useCallback((pendingAction: () => void, description: string) => {
    setUnsavedDialog({ isOpen: true, pendingAction, description });
  }, []);

  const [prevIsBlocked, setPrevIsBlocked] = useState(isBlocked);
  if (isBlocked && !prevIsBlocked) {
    setPrevIsBlocked(true);
    setUnsavedDialog({
      isOpen: true,
      pendingAction: () => blocker.proceed?.(),
      description: 'Leave the Agents page',
    });
  } else if (isBlocked !== prevIsBlocked) {
    setPrevIsBlocked(isBlocked);
  }

  const handleEditRequest = useCallback(
    (agent: AgentConfig) => {
      setSaveResult(null);
      if (!isEditorDirty) {
        setEditAgent(agent);
        return;
      }

      queueUnsavedAction(() => setEditAgent(agent), 'Switch to another agent definition');
    },
    [isEditorDirty, queueUnsavedAction]
  );

  const handleCloseEditor = useCallback(() => {
    if (!isEditorDirty) {
      setEditAgent(null);
      return;
    }

    queueUnsavedAction(() => setEditAgent(null), 'Close the current agent editor');
  }, [isEditorDirty, queueUnsavedAction]);

  const handleOpenAddModal = useCallback(() => {
    setSaveResult(null);
    if (!isEditorDirty) {
      setShowAddModal(true);
      return;
    }

    queueUnsavedAction(() => setShowAddModal(true), 'Open the add-agent flow');
  }, [isEditorDirty, queueUnsavedAction]);

  const handleUnsavedSave = useCallback(async () => {
    const action = unsavedDialog.pendingAction;
    const saved = await editorRef.current?.save();
    if (!saved) return;
    setUnsavedDialog({ isOpen: false, pendingAction: null, description: '' });
    action?.();
  }, [unsavedDialog.pendingAction]);

  const handleUnsavedDiscard = useCallback(() => {
    const action = unsavedDialog.pendingAction;
    editorRef.current?.discard();
    setUnsavedDialog({ isOpen: false, pendingAction: null, description: '' });
    setIsEditorDirty(false);
    action?.();
  }, [unsavedDialog.pendingAction]);

  const handleUnsavedCancel = useCallback(() => {
    if (isBlocked) {
      blocker.reset?.();
    }
    setUnsavedDialog({ isOpen: false, pendingAction: null, description: '' });
  }, [blocker, isBlocked]);

  const filteredAgents = (agents ?? [])
    .filter((agent) => {
      const query = deferredSearch.trim().toLowerCase();
      const catalogName = getCatalogAgentName(agent).toLowerCase();
      const matchesSearch =
        query.length === 0 ||
        catalogName.includes(query) ||
        agent.name.toLowerCase().includes(query) ||
        agent.slug.toLowerCase().includes(query) ||
        agent.description.toLowerCase().includes(query) ||
        agent.tools.some((tool) => tool.toLowerCase().includes(query));

      return matchesSearch;
    })
    .sort((left, right) => {
      if (sortMode === 'usage') {
        return (agentUsageCounts[right.slug] ?? 0) - (agentUsageCounts[left.slug] ?? 0);
      }

      return getCatalogAgentName(left).localeCompare(getCatalogAgentName(right));
    });

  // Two-pass Featured Agents algorithm:
  // Pass 1: agents with usage > 0, sorted descending, up to 3
  // Pass 2: supplement with agents created within past 3 days
  // Capture stable time reference to keep render pure
  const [stableNow] = useState(() => Date.now());
  const spotlightAgents = useMemo(() => {
    const allAgents = agents ?? [];
    const usageAgents = allAgents
      .filter((a) => (agentUsageCounts[a.slug] ?? 0) > 0)
      .sort((a, b) => (agentUsageCounts[b.slug] ?? 0) - (agentUsageCounts[a.slug] ?? 0))
      .slice(0, 3);

    if (usageAgents.length >= 3) return usageAgents;

    const threeDaysAgo = stableNow - 3 * 24 * 60 * 60 * 1000;
    const usageSlugs = new Set(usageAgents.map((a) => a.slug));
    const recentAgents = allAgents
      .filter(
        (a) =>
          a.created_at && new Date(a.created_at).getTime() > threeDaysAgo && !usageSlugs.has(a.slug)
      )
      .sort((a, b) => new Date(b.created_at!).getTime() - new Date(a.created_at!).getTime());

    return [...usageAgents, ...recentAgents].slice(0, 3);
  }, [agents, agentUsageCounts, stableNow]);

  const totalAgents = agents?.length ?? 0;
  const usedAgents = agents?.filter((agent) => (agentUsageCounts[agent.slug] ?? 0) > 0).length ?? 0;
  const unresolvedPendingAgents = pendingAgents ?? [];
  const bulkTargetAgents = [
    ...(agents ?? []),
    ...unresolvedPendingAgents.filter((agent) => agent.status !== 'pending_deletion'),
  ];
  const repositoryLabel = repo || 'Unlinked';
  const repositoryValueClass =
    repositoryLabel.length > 18
      ? 'mt-2 break-all text-xs font-semibold leading-5 text-foreground'
      : 'mt-2 text-sm font-semibold text-foreground';

  return (
    <div className="celestial-fade-in flex min-w-0 flex-col gap-6">
      <div className="ritual-stage flex flex-col gap-4 rounded-[1.55rem] p-4 sm:rounded-[1.8rem] sm:p-6 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-[11px] uppercase tracking-[0.24em] text-primary/80">Agent archive</p>
          <h3 className="mt-2 text-[1.55rem] font-display font-medium leading-tight sm:text-[1.9rem]">
            Broader space for every active assistant
          </h3>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
            Search and compare the agents that exist on the repository default branch.
            {owner && repo ? ` Linked repository: ${owner}/${repo}.` : ''}
          </p>
        </div>
        <div className="flex flex-wrap justify-end gap-3">
          <Button
            variant="outline"
            size="lg"
            onClick={() => void refreshModels()}
            disabled={isRefreshingModels}
          >
            {isRefreshingModels ? 'Refreshing models…' : 'Refresh models'}
          </Button>
          <Button
            onClick={handleOpenAddModal}
            size="lg"
          >
            + Add Agent
          </Button>
        </div>
      </div>

      {saveResult && (
        <div className="solar-chip-success rounded-[1.25rem] p-4 text-sm">
          Saved changes for <span className="font-semibold">{saveResult.agentName}</span>. A pull
          request was opened with the updated agent files.{' '}
          <a
            href={saveResult.prUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium underline underline-offset-4"
          >
            View Pull Request
          </a>
        </div>
      )}

      {editAgent && (
        <AgentInlineEditor
          ref={editorRef}
          agent={editAgent}
          projectId={projectId}
          onDirtyChange={setIsEditorDirty}
          onCancel={handleCloseEditor}
          onSaved={(prUrl, agentName) => {
            setSaveResult({ agentName, prUrl });
            setEditAgent(null);
            setIsEditorDirty(false);
          }}
        />
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-56 rounded-[1.4rem] border border-border bg-background/40 animate-pulse"
            />
          ))}
        </div>
      )}

      {/* Error state */}
      {error && !isLoading && (
        <div className="flex flex-col items-center gap-2 rounded-[1.4rem] border border-destructive/30 bg-destructive/5 p-6 text-center">
          <span className="text-sm text-destructive">Failed to load agents</span>
          <p className="text-xs text-muted-foreground">{error.message}</p>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !error && agents && agents.length === 0 && (
        <div className="celestial-panel flex flex-col items-center gap-3 rounded-[1.5rem] border-2 border-dashed border-border bg-background/28 p-8 text-center">
          <ThemedAgentIcon name="Agents" iconName="constellation" size="lg" className="h-12 w-12" />
          <p className="text-lg font-medium text-foreground">No agents yet</p>
          <p className="max-w-md text-sm text-muted-foreground">
            No agent files are currently present in .github/agents on the repository default branch.
          </p>
          <p className="text-xs text-muted-foreground/70">
            Open a PR to add an agent. It will appear here after that PR is merged into main.
          </p>
          <Button onClick={() => setShowAddModal(true)}>Create the first agent</Button>
        </div>
      )}

      {!error && (pendingLoading || unresolvedPendingAgents.length > 0) && (
        <section className="ritual-stage rounded-[1.55rem] p-4 sm:rounded-[1.85rem] sm:p-6">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-[11px] uppercase tracking-[0.24em] text-primary/80">
                Pending changes
              </p>
              <h4 className="mt-2 text-[1.35rem] font-display font-medium leading-tight sm:text-[1.6rem]">
                Agent PRs waiting on main
              </h4>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                These entries are local workflow records only. They stay here until the repo default
                branch reflects the change.
              </p>
            </div>
            <div className="flex flex-wrap items-center justify-end gap-3">
              <div className="solar-chip-soft rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em]">
                {pendingLoading ? 'Refreshing…' : `${unresolvedPendingAgents.length} pending`}
              </div>
              {!pendingLoading && unresolvedPendingAgents.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleClearPending}
                  disabled={clearPendingMutation.isPending}
                  className="solar-action-danger"
                >
                  {clearPendingMutation.isPending ? 'Deleting stale rows…' : 'Delete stale pending'}
                </Button>
              )}
            </div>
          </div>

          {clearPendingMutation.isSuccess && clearPendingMutation.data.deleted_count > 0 && (
            <p className="mt-4 text-sm text-muted-foreground">
              Deleted {clearPendingMutation.data.deleted_count} stale pending agent record
              {clearPendingMutation.data.deleted_count === 1 ? '' : 's'} from the local database.
            </p>
          )}

          {clearPendingMutation.isError && (
            <p className="mt-4 text-sm text-destructive">
              {clearPendingMutation.error?.message || 'Failed to delete stale pending agents.'}
            </p>
          )}

          {pendingLoading ? (
            <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {[1, 2].map((i) => (
                <div
                  key={i}
                  className="h-48 rounded-[1.4rem] border border-border bg-background/40 animate-pulse"
                />
              ))}
            </div>
          ) : (
            <div className="constellation-grid mt-6 grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
              {unresolvedPendingAgents.map((agent) => (
                <AgentCard
                  key={agent.id}
                  agent={agent}
                  projectId={projectId}
                  usageCount={agentUsageCounts[agent.slug] ?? 0}
                  pipelineConfigCount={pipelineConfigCounts[agent.slug] ?? 0}
                  pendingSubIssueCount={pendingSubIssueCounts[agent.slug.toLowerCase()] ?? 0}
                  onEdit={handleEditRequest}
                  variant="default"
                />
              ))}
            </div>
          )}
        </section>
      )}

      {!isLoading && !error && agents && agents.length > 0 && (
        <>
          {spotlightAgents.length > 0 && (
            <section className="ritual-stage rounded-[1.55rem] p-4 sm:rounded-[1.85rem] sm:p-6">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
                <div>
                  <div className="flex items-center gap-2 text-primary">
                    <Sparkles className="h-4 w-4" />
                    <p className="text-[11px] uppercase tracking-[0.24em]">Featured agents</p>
                  </div>
                  <h4 className="mt-2 text-[1.35rem] font-display font-medium leading-tight sm:text-[1.6rem]">
                    The agents setting the tone right now
                  </h4>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">
                    Spotlight prioritizes the most-used agents and recently created ones.
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  <Card className="moonwell rounded-[1.35rem] border-primary/15 shadow-none">
                    <CardContent className="p-4">
                      <p className="text-[10px] uppercase tracking-[0.22em] text-muted-foreground">
                        Total
                      </p>
                      <p className="mt-2 text-2xl font-semibold text-foreground">{totalAgents}</p>
                    </CardContent>
                  </Card>
                  <Card className="moonwell rounded-[1.35rem] border-primary/15 shadow-none">
                    <CardContent className="p-4">
                      <p className="text-[10px] uppercase tracking-[0.22em] text-muted-foreground">
                        Used on board
                      </p>
                      <p className="mt-2 text-2xl font-semibold text-foreground">{usedAgents}</p>
                    </CardContent>
                  </Card>
                  <Card className="moonwell rounded-[1.35rem] border-primary/15 shadow-none">
                    <CardContent className="p-4">
                      <p className="text-[10px] uppercase tracking-[0.22em] text-muted-foreground">
                        Repository
                      </p>
                      <p
                        className={repositoryValueClass}
                        title={owner && repo ? `${owner}/${repo}` : repositoryLabel}
                      >
                        {repositoryLabel}
                      </p>
                    </CardContent>
                  </Card>
                  <Card className="moonwell rounded-[1.35rem] border-primary/15 shadow-none">
                    <CardContent className="p-4">
                      <p className="text-[10px] uppercase tracking-[0.22em] text-muted-foreground">
                        Visibility
                      </p>
                      <p className="mt-2 text-sm font-semibold text-foreground">Merged to main</p>
                    </CardContent>
                  </Card>
                </div>
              </div>

              <div className="constellation-grid mt-6 grid gap-4 lg:grid-cols-3">
                {spotlightAgents.map((agent) => (
                  <AgentCard
                    key={agent.id}
                    agent={agent}
                    projectId={projectId}
                    usageCount={agentUsageCounts[agent.slug] ?? 0}
                    pipelineConfigCount={pipelineConfigCounts[agent.slug] ?? 0}
                    pendingSubIssueCount={pendingSubIssueCounts[agent.slug.toLowerCase()] ?? 0}
                    onEdit={handleEditRequest}
                    variant="spotlight"
                  />
                ))}
              </div>
            </section>
          )}

          <section
            id="agents-catalog"
            className="ritual-stage scroll-mt-6 rounded-[1.55rem] p-4 sm:rounded-[1.85rem] sm:p-6"
          >
            <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
              <div>
                <p className="text-[11px] uppercase tracking-[0.24em] text-primary/80">
                  Catalog controls
                </p>
                <h4 className="mt-2 text-[1.35rem] font-display font-medium leading-tight sm:text-[1.6rem]">
                  Filter the constellation
                </h4>
              </div>

              <div className="flex flex-col gap-3 xl:min-w-[28rem]">
                <div className="relative">
                  <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder="Search by name, slug, description, or tool"
                    aria-label="Search agents catalog"
                    className="moonwell h-12 rounded-full border-border/60 pl-10"
                  />
                </div>
                <div className="flex flex-wrap items-center justify-end gap-2">
                  <select
                    className="moonwell h-10 w-full rounded-full border-border/60 px-4 text-sm text-foreground sm:w-auto"
                    value={sortMode}
                    onChange={(event) => setSortMode(event.target.value as AgentSortMode)}
                    aria-label="Sort agents"
                  >
                    <option value="name">Alphabetical</option>
                    <option value="usage">By usage</option>
                  </select>
                  <Tooltip contentKey="agents.panel.bulkUpdateButton">
                    <Button variant="outline" size="sm" onClick={() => setBulkUpdateOpen(true)}>
                      <RefreshCw className="mr-2 h-4 w-4" />
                      Update All Models
                    </Button>
                  </Tooltip>
                </div>
              </div>
            </div>

            {filteredAgents.length === 0 ? (
              <div className="mt-6 rounded-[1.35rem] border border-dashed border-border/80 bg-background/42 p-8 text-center">
                <p className="text-sm text-muted-foreground">
                  No agents match the current filters.
                </p>
                <Button
                  variant="ghost"
                  className="mt-3"
                  onClick={() => {
                    setSearch('');
                    setSortMode('name');
                  }}
                >
                  Reset filters
                </Button>
              </div>
            ) : (
              <InfiniteScrollContainer
                hasNextPage={agentsHasNextPage ?? false}
                isFetchingNextPage={agentsIsFetchingNextPage}
                fetchNextPage={agentsFetchNextPage}
                isError={hasError}
                onRetry={agentsFetchNextPage}
              >
                <div className="constellation-grid mt-6 grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
                  {filteredAgents.map((agent) => (
                    <AgentCard
                      key={agent.id}
                      agent={agent}
                      projectId={projectId}
                      usageCount={agentUsageCounts[agent.slug] ?? 0}
                      pipelineConfigCount={pipelineConfigCounts[agent.slug] ?? 0}
                      pendingSubIssueCount={pendingSubIssueCounts[agent.slug.toLowerCase()] ?? 0}
                      onEdit={handleEditRequest}
                    />
                  ))}
                </div>
              </InfiniteScrollContainer>
            )}
          </section>
        </>
      )}

      {/* Add Agent Modal */}
      <AddAgentModal
        projectId={projectId}
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
      />

      {/* Bulk Model Update Dialog */}
      <BulkModelUpdateDialog
        open={bulkUpdateOpen}
        onOpenChange={setBulkUpdateOpen}
        agents={bulkTargetAgents}
        projectId={projectId}
        onSuccess={() => setBulkUpdateOpen(false)}
      />

      <UnsavedChangesDialog
        isOpen={unsavedDialog.isOpen}
        onSave={handleUnsavedSave}
        onDiscard={handleUnsavedDiscard}
        onCancel={handleUnsavedCancel}
        actionDescription={unsavedDialog.description}
      />
    </div>
  );
}
