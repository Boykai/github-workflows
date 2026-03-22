/**
 * PipelineAnalytics — Dashboard of computed insights from saved pipelines.
 * Derives stats, agent frequency, model distribution, and complexity metrics
 * from the available PipelineConfigSummary data.
 */

import { useMemo } from 'react';
import { Layers, Bot, Wrench, BarChart3, Cpu, Zap, TrendingUp, GitBranch } from '@/lib/icons';
import { Tooltip } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import { formatAgentName } from '@/utils/formatAgentName';
import type { PipelineConfigSummary, PipelineAgentNode } from '@/types';

interface PipelineAnalyticsProps {
  pipelines: PipelineConfigSummary[];
}

/** Extract all agent nodes from a pipeline (groups-first, fallback to legacy). */
function allAgents(pipeline: PipelineConfigSummary): PipelineAgentNode[] {
  return (pipeline.stages ?? []).flatMap((stage) => {
    const grouped = (stage.groups ?? []).flatMap((g) => g.agents);
    return grouped.length > 0 ? grouped : stage.agents;
  });
}

export function PipelineAnalytics({ pipelines }: PipelineAnalyticsProps) {
  const analytics = useMemo(() => {
    if (pipelines.length === 0) return null;

    const totalPipelines = pipelines.length;
    const totalStages = pipelines.reduce((s, p) => s + p.stage_count, 0);
    const totalAgents = pipelines.reduce((s, p) => s + p.agent_count, 0);
    const totalTools = pipelines.reduce((s, p) => s + p.total_tool_count, 0);

    const avgStagesPerPipeline = totalStages / totalPipelines;
    const avgAgentsPerPipeline = totalAgents / totalPipelines;

    // Agent frequency across all pipelines
    const agentCounts = new Map<string, { slug: string; displayName: string; count: number }>();
    for (const p of pipelines) {
      for (const agent of allAgents(p)) {
        const existing = agentCounts.get(agent.agent_slug);
        if (existing) {
          existing.count++;
        } else {
          agentCounts.set(agent.agent_slug, {
            slug: agent.agent_slug,
            displayName: agent.agent_display_name,
            count: 1,
          });
        }
      }
    }
    const topAgents = [...agentCounts.values()].sort((a, b) => b.count - a.count).slice(0, 5);

    // Model distribution
    const modelCounts = new Map<string, number>();
    for (const p of pipelines) {
      for (const agent of allAgents(p)) {
        if (agent.model_name) {
          modelCounts.set(agent.model_name, (modelCounts.get(agent.model_name) ?? 0) + 1);
        }
      }
    }
    const topModels = [...modelCounts.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 4)
      .map(([name, count]) => ({ name, count }));

    // Execution mode breakdown
    let parallelGroups = 0;
    let sequentialGroups = 0;
    for (const p of pipelines) {
      for (const stage of p.stages ?? []) {
        for (const group of stage.groups ?? []) {
          if (group.execution_mode === 'parallel') parallelGroups++;
          else sequentialGroups++;
        }
      }
    }

    // Complexity: pipeline with the most agents
    const mostComplex = [...pipelines].sort((a, b) => b.agent_count - a.agent_count)[0];
    const leastComplex = [...pipelines].sort((a, b) => a.agent_count - b.agent_count)[0];

    return {
      totalPipelines,
      totalStages,
      totalAgents,
      totalTools,
      avgStagesPerPipeline,
      avgAgentsPerPipeline,
      topAgents,
      topModels,
      parallelGroups,
      sequentialGroups,
      mostComplex,
      leastComplex,
    };
  }, [pipelines]);

  if (!analytics) {
    return (
      <div>
        <h3 className="text-lg font-semibold mb-3">Pipeline Analytics</h3>
        <div className="celestial-panel rounded-[1.2rem] border border-border/75 p-4">
          <p className="text-sm text-muted-foreground text-center py-4">
            Analytics will appear once pipelines are created
          </p>
        </div>
      </div>
    );
  }

  const statCards = [
    { label: 'Pipelines', value: analytics.totalPipelines, icon: GitBranch },
    { label: 'Total Stages', value: analytics.totalStages, icon: Layers },
    { label: 'Total Agents', value: analytics.totalAgents, icon: Bot },
    { label: 'Total Tools', value: analytics.totalTools, icon: Wrench },
    { label: 'Avg Stages / Pipeline', value: analytics.avgStagesPerPipeline.toFixed(1), icon: BarChart3 },
    { label: 'Avg Agents / Pipeline', value: analytics.avgAgentsPerPipeline.toFixed(1), icon: TrendingUp },
  ];

  const totalExecGroups = analytics.parallelGroups + analytics.sequentialGroups;

  return (
    <div>
      <h3 className="text-lg font-semibold mb-3">Pipeline Analytics</h3>
      <div className="celestial-panel rounded-[1.2rem] border border-border/75 p-5 space-y-6">
        {/* Summary Stats Grid */}
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {statCards.map((stat) => (
            <div
              key={stat.label}
              className="flex flex-col items-center gap-1.5 rounded-[1rem] border border-border/40 bg-background/20 p-3 text-center"
            >
              <stat.icon className="h-4 w-4 text-primary/70" />
              <span className="text-lg font-bold text-foreground">{stat.value}</span>
              <span className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                {stat.label}
              </span>
            </div>
          ))}
        </div>

        <div className="grid gap-5 md:grid-cols-2">
          {/* Top Agents */}
          <div className="space-y-2.5">
            <h4 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              <Bot className="h-3.5 w-3.5" />
              Most Used Agents
            </h4>
            <div className="space-y-1.5">
              {analytics.topAgents.map((agent) => {
                const pct = Math.round((agent.count / (analytics.totalAgents || 1)) * 100);
                return (
                  <div key={agent.slug} className="flex items-center gap-2">
                    <Tooltip content={`${agent.count} assignments across pipelines`}>
                      <span className="w-28 truncate text-xs font-medium text-foreground">
                        {formatAgentName(agent.slug, agent.displayName)}
                      </span>
                    </Tooltip>
                    <div className="relative h-2.5 flex-1 overflow-hidden rounded-full bg-border/30">
                      <div
                        className="absolute inset-y-0 left-0 rounded-full bg-primary/60 transition-all"
                        style={{ width: `${Math.max(pct, 4)}%` }}
                      />
                    </div>
                    <span className="w-8 text-right text-[10px] tabular-nums text-muted-foreground">
                      {pct}%
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Model Distribution */}
          <div className="space-y-2.5">
            <h4 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              <Cpu className="h-3.5 w-3.5" />
              Model Distribution
            </h4>
            {analytics.topModels.length > 0 ? (
              <div className="space-y-1.5">
                {analytics.topModels.map((model) => {
                  const pct = Math.round((model.count / (analytics.totalAgents || 1)) * 100);
                  return (
                    <div key={model.name} className="flex items-center gap-2">
                      <Tooltip content={`${model.count} agent nodes using this model`}>
                        <span className="w-28 truncate text-xs font-medium text-foreground">
                          {model.name}
                        </span>
                      </Tooltip>
                      <div className="relative h-2.5 flex-1 overflow-hidden rounded-full bg-border/30">
                        <div
                          className="absolute inset-y-0 left-0 rounded-full bg-[hsl(var(--sync-connected))]/60 transition-all"
                          style={{ width: `${Math.max(pct, 4)}%` }}
                        />
                      </div>
                      <span className="w-8 text-right text-[10px] tabular-nums text-muted-foreground">
                        {pct}%
                      </span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground/60">No models configured</p>
            )}
          </div>
        </div>

        {/* Bottom row: Execution Mode + Complexity */}
        <div className="grid gap-5 md:grid-cols-2">
          {/* Execution Mode Breakdown */}
          {totalExecGroups > 0 && (
            <div className="space-y-2.5">
              <h4 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                <Zap className="h-3.5 w-3.5" />
                Execution Modes
              </h4>
              <div className="flex items-center gap-3">
                <div className="relative h-3 flex-1 overflow-hidden rounded-full bg-border/30">
                  {analytics.sequentialGroups > 0 && (
                    <div
                      className="absolute inset-y-0 left-0 rounded-l-full bg-primary/50"
                      style={{
                        width: `${(analytics.sequentialGroups / totalExecGroups) * 100}%`,
                      }}
                    />
                  )}
                  {analytics.parallelGroups > 0 && (
                    <div
                      className="absolute inset-y-0 right-0 rounded-r-full bg-[hsl(var(--sync-connected))]/50"
                      style={{
                        width: `${(analytics.parallelGroups / totalExecGroups) * 100}%`,
                      }}
                    />
                  )}
                </div>
              </div>
              <div className="flex justify-between text-[10px] text-muted-foreground">
                <span>
                  Sequential:{' '}
                  <span className="font-semibold text-foreground">{analytics.sequentialGroups}</span>
                </span>
                <span>
                  Parallel:{' '}
                  <span className="font-semibold text-foreground">{analytics.parallelGroups}</span>
                </span>
              </div>
            </div>
          )}

          {/* Complexity Spotlight */}
          <div className="space-y-2.5">
            <h4 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              <BarChart3 className="h-3.5 w-3.5" />
              Complexity Spotlight
            </h4>
            <div className="grid grid-cols-2 gap-2">
              <div className="rounded-[0.75rem] border border-border/40 bg-background/20 px-3 py-2">
                <p className="text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
                  Most complex
                </p>
                <Tooltip content={`${analytics.mostComplex.stage_count} stages · ${analytics.mostComplex.agent_count} agents`}>
                  <p className={cn('mt-0.5 truncate text-xs font-semibold text-foreground')}>
                    {analytics.mostComplex.name}
                  </p>
                </Tooltip>
                <p className="text-[10px] text-muted-foreground">
                  {analytics.mostComplex.agent_count} agents
                </p>
              </div>
              <div className="rounded-[0.75rem] border border-border/40 bg-background/20 px-3 py-2">
                <p className="text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
                  Most minimal
                </p>
                <Tooltip content={`${analytics.leastComplex.stage_count} stages · ${analytics.leastComplex.agent_count} agents`}>
                  <p className={cn('mt-0.5 truncate text-xs font-semibold text-foreground')}>
                    {analytics.leastComplex.name}
                  </p>
                </Tooltip>
                <p className="text-[10px] text-muted-foreground">
                  {analytics.leastComplex.agent_count} agents
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
