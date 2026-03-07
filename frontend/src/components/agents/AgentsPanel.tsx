/**
 * AgentsPanel — container for the Agents feature on the project board.
 *
 * Renders below ChoresPanel. Shows agent cards, empty state with docs link,
 * and loading / error states. Mirrors ChoresPanel pattern.
 */

import { useDeferredValue, useState } from 'react';
import { Search, Sparkles } from 'lucide-react';
import { useAgentsList, usePendingAgentsList, useClearPendingAgents } from '@/hooks/useAgents';
import { AgentCard } from './AgentCard';
import { AddAgentModal } from './AddAgentModal';
import type { AgentConfig } from '@/services/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';

interface AgentsPanelProps {
  projectId: string;
  owner?: string;
  repo?: string;
  agentUsageCounts?: Record<string, number>;
}

type AgentSortMode = 'name' | 'usage';

export function AgentsPanel({ projectId, owner, repo, agentUsageCounts = {} }: AgentsPanelProps) {
  const { data: agents, isLoading, error } = useAgentsList(projectId);
  const { data: pendingAgents, isLoading: pendingLoading } = usePendingAgentsList(projectId);
  const clearPendingMutation = useClearPendingAgents(projectId);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editAgent, setEditAgent] = useState<AgentConfig | null>(null);
  const [search, setSearch] = useState('');
  const [sortMode, setSortMode] = useState<AgentSortMode>('name');
  const deferredSearch = useDeferredValue(search);

  const handleClearPending = () => {
    const confirmed = window.confirm(
      'Delete all pending agent records from the local database for this project? This only removes stale SQLite rows and does not change the repository.'
    );
    if (!confirmed) return;
    clearPendingMutation.mutate();
  };

  const filteredAgents = (agents ?? [])
    .filter((agent) => {
      const query = deferredSearch.trim().toLowerCase();
      const matchesSearch =
        query.length === 0 ||
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

      return left.name.localeCompare(right.name);
    });

  const spotlightAgents = [...(agents ?? [])]
    .sort((left, right) => {
      const usageDelta = (agentUsageCounts[right.slug] ?? 0) - (agentUsageCounts[left.slug] ?? 0);
      if (usageDelta !== 0) return usageDelta;
      return left.name.localeCompare(right.name);
    })
    .slice(0, 3);

  const totalAgents = agents?.length ?? 0;
  const usedAgents = agents?.filter((agent) => (agentUsageCounts[agent.slug] ?? 0) > 0).length ?? 0;
  const unresolvedPendingAgents = pendingAgents ?? [];

  return (
    <div className="flex min-w-0 flex-col gap-6">
      <div className="ritual-stage flex flex-col gap-4 rounded-[1.55rem] p-4 sm:rounded-[1.8rem] sm:p-6 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-[11px] uppercase tracking-[0.24em] text-primary/80">Agent archive</p>
          <h3 className="mt-2 text-[1.55rem] font-display font-medium leading-tight sm:text-[1.9rem]">Broader space for every active assistant</h3>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
            Search and compare the agents that exist on the repository default branch.
            {owner && repo ? ` Linked repository: ${owner}/${repo}.` : ''}
          </p>
        </div>
        <Button onClick={() => setShowAddModal(true)} size="lg">+ Add Agent</Button>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-56 rounded-[1.4rem] border border-border bg-muted/30 animate-pulse"
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
        <div className="flex flex-col items-center gap-3 rounded-[1.5rem] border-2 border-dashed border-border bg-muted/10 p-8 text-center">
          <span className="text-2xl">🤖</span>
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
              <p className="text-[11px] uppercase tracking-[0.24em] text-primary/80">Pending changes</p>
              <h4 className="mt-2 text-[1.35rem] font-display font-medium leading-tight sm:text-[1.6rem]">Agent PRs waiting on main</h4>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                These entries are local workflow records only. They stay here until the repo default branch reflects the change.
              </p>
            </div>
            <div className="flex flex-wrap items-center justify-end gap-3">
              <div className="rounded-full border border-border/70 bg-background/55 px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                {pendingLoading ? 'Refreshing…' : `${unresolvedPendingAgents.length} pending`}
              </div>
              {!pendingLoading && unresolvedPendingAgents.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleClearPending}
                  disabled={clearPendingMutation.isPending}
                  className="border-destructive/30 text-destructive hover:bg-destructive/10 hover:text-destructive"
                >
                  {clearPendingMutation.isPending ? 'Deleting stale rows…' : 'Delete stale pending'}
                </Button>
              )}
            </div>
          </div>

          {clearPendingMutation.isSuccess && clearPendingMutation.data.deleted_count > 0 && (
            <p className="mt-4 text-sm text-muted-foreground">
              Deleted {clearPendingMutation.data.deleted_count} stale pending agent record{clearPendingMutation.data.deleted_count === 1 ? '' : 's'} from the local database.
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
                <div key={i} className="h-48 rounded-[1.4rem] border border-border bg-muted/30 animate-pulse" />
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
                  onEdit={(currentAgent) => setEditAgent(currentAgent)}
                  variant="default"
                />
              ))}
            </div>
          )}
        </section>
      )}

      {!isLoading && !error && agents && agents.length > 0 && (
        <>
          <section className="ritual-stage rounded-[1.55rem] p-4 sm:rounded-[1.85rem] sm:p-6">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <div className="flex items-center gap-2 text-primary">
                  <Sparkles className="h-4 w-4" />
                  <p className="text-[11px] uppercase tracking-[0.24em]">Featured agents</p>
                </div>
                <h4 className="mt-2 text-[1.35rem] font-display font-medium leading-tight sm:text-[1.6rem]">The agents setting the tone right now</h4>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  Spotlight prioritizes the repo agents most heavily used in the board configuration.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <Card className="moonwell rounded-[1.35rem] border-primary/15 shadow-none">
                  <CardContent className="p-4">
                    <p className="text-[10px] uppercase tracking-[0.22em] text-muted-foreground">Total</p>
                    <p className="mt-2 text-2xl font-semibold text-foreground">{totalAgents}</p>
                  </CardContent>
                </Card>
                <Card className="moonwell rounded-[1.35rem] border-primary/15 shadow-none">
                  <CardContent className="p-4">
                    <p className="text-[10px] uppercase tracking-[0.22em] text-muted-foreground">Used on board</p>
                    <p className="mt-2 text-2xl font-semibold text-foreground">{usedAgents}</p>
                  </CardContent>
                </Card>
                <Card className="moonwell rounded-[1.35rem] border-primary/15 shadow-none">
                  <CardContent className="p-4">
                    <p className="text-[10px] uppercase tracking-[0.22em] text-muted-foreground">Repository</p>
                    <p className="mt-2 truncate text-sm font-semibold text-foreground">{repo ? `${owner}/${repo}` : 'Unlinked'}</p>
                  </CardContent>
                </Card>
                <Card className="moonwell rounded-[1.35rem] border-primary/15 shadow-none">
                  <CardContent className="p-4">
                    <p className="text-[10px] uppercase tracking-[0.22em] text-muted-foreground">Visibility</p>
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
                  onEdit={(a) => setEditAgent(a)}
                  variant="spotlight"
                />
              ))}
            </div>
          </section>

          <section id="agents-catalog" className="ritual-stage scroll-mt-6 rounded-[1.55rem] p-4 sm:rounded-[1.85rem] sm:p-6">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
              <div>
                <p className="text-[11px] uppercase tracking-[0.24em] text-primary/80">Catalog controls</p>
                <h4 className="mt-2 text-[1.35rem] font-display font-medium leading-tight sm:text-[1.6rem]">Filter the constellation</h4>
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
                <div className="flex justify-end">
                  <select
                    className="moonwell h-10 w-full rounded-full border-border/60 px-4 text-sm text-foreground sm:w-auto"
                    value={sortMode}
                    onChange={(event) => setSortMode(event.target.value as AgentSortMode)}
                    aria-label="Sort agents"
                  >
                    <option value="name">Alphabetical</option>
                    <option value="usage">By usage</option>
                  </select>
                </div>
              </div>
            </div>

            {filteredAgents.length === 0 ? (
              <div className="mt-6 rounded-[1.35rem] border border-dashed border-border/80 bg-background/35 p-8 text-center">
                <p className="text-sm text-muted-foreground">No agents match the current filters.</p>
                <Button variant="ghost" className="mt-3" onClick={() => {
                  setSearch('');
                  setSortMode('name');
                }}>
                  Reset filters
                </Button>
              </div>
            ) : (
              <div className="constellation-grid mt-6 grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
                {filteredAgents.map((agent) => (
                  <AgentCard
                    key={agent.id}
                    agent={agent}
                    projectId={projectId}
                    usageCount={agentUsageCounts[agent.slug] ?? 0}
                    onEdit={(a) => setEditAgent(a)}
                  />
                ))}
              </div>
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

      {/* Edit Agent Modal */}
      {editAgent && (
        <AddAgentModal
          projectId={projectId}
          isOpen={true}
          onClose={() => setEditAgent(null)}
          editAgent={editAgent}
        />
      )}
    </div>
  );
}
