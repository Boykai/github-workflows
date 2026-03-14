/**
 * PipelineFlowGraph — constellation-style visualization of pipeline execution order.
 * Uses themed agent icons connected in stage order for Saved Pipelines and Recent Activity cards.
 */

import { memo, useEffect, useMemo, useRef, useState } from 'react';
import { ThemedAgentIcon } from '@/components/common/ThemedAgentIcon';
import { cn } from '@/lib/utils';
import type { PipelineStage } from '@/types';
import { formatAgentName } from '@/utils/formatAgentName';

interface PipelineFlowGraphProps {
  stages: PipelineStage[];
  width?: number;
  height?: number;
  className?: string;
  responsive?: boolean;
}

type FlowGraphIconSize = 'sm' | 'md';

export const PipelineFlowGraph = memo(function PipelineFlowGraph({
  stages,
  width = 220,
  height = 112,
  className = '',
  responsive = false,
}: PipelineFlowGraphProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [responsiveWidth, setResponsiveWidth] = useState<number>(width);

  useEffect(() => {
    if (!responsive || !containerRef.current) {
      return undefined;
    }

    const updateWidth = () => {
      const nextWidth = Math.round(containerRef.current?.clientWidth ?? width);
      if (nextWidth > 0) {
        setResponsiveWidth(nextWidth);
      }
    };

    updateWidth();

    if (typeof ResizeObserver === 'undefined') {
      window.addEventListener('resize', updateWidth);
      return () => window.removeEventListener('resize', updateWidth);
    }

    const observer = new ResizeObserver(() => updateWidth());
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, [responsive, width]);

  const graphWidth = responsive ? responsiveWidth : width;

  const layout = useMemo(() => {
    if (stages.length === 0) {
      return {
        stageAnchors: [],
        nodes: [],
        edges: [],
        stars: [],
        iconSize: 'sm' as FlowGraphIconSize,
      };
    }

    const paddingX = Math.max(16, Math.round(graphWidth * 0.07));
    // Collect agents from groups (preferred) with fallback to legacy agents field
    const agentsPerStage = stages.map((stage) => {
      const fromGroups = (stage.groups ?? []).flatMap((g) => g.agents);
      return fromGroups.length > 0 ? fromGroups : stage.agents;
    });
    const maxAgentsInStage = Math.max(...agentsPerStage.map((a) => a.length), 1);
    const iconSize: FlowGraphIconSize =
      graphWidth >= 220 && height >= 112 && maxAgentsInStage <= 2 ? 'md' : 'sm';
    const nodeDiameter = iconSize === 'md' ? 36 : 28;
    const nodeRadius = nodeDiameter / 2;
    const topInset = Math.max(14, nodeRadius + 4);
    const bottomInset = Math.max(14, nodeRadius + 4);
    const stageCount = stages.length;
    const usableHeight = Math.max(height - topInset - bottomInset, nodeDiameter + 4);

    const stageAnchors = stages.map((stage, stageIndex) => {
      const x =
        stageCount === 1
          ? graphWidth / 2
          : paddingX + (stageIndex * (graphWidth - paddingX * 2)) / (stageCount - 1);

      return {
        id: stage.id,
        label: stage.name,
        x,
      };
    });

    const nodes = stages.flatMap((stage, stageIndex) => {
      const stageAgents = agentsPerStage[stageIndex];
      if (stageAgents.length === 0) {
        return [];
      }

      const rowPositions =
        stageAgents.length === 1
          ? [topInset + usableHeight / 2]
          : stageAgents.map(
              (_, agentIndex) => topInset + (agentIndex * usableHeight) / (stageAgents.length - 1)
            );

      return stageAgents.map((agent, agentIndex) => ({
        id: agent.id,
        slug: agent.agent_slug,
        displayName: formatAgentName(agent.agent_slug, agent.agent_display_name),
        stageLabel: stage.name,
        x: stageAnchors[stageIndex].x,
        y: rowPositions[agentIndex],
      }));
    });

    const edges = nodes.slice(0, -1).map((node, index) => {
      const next = nodes[index + 1];
      const controlX = (node.x + next.x) / 2;
      const controlY = Math.min(node.y, next.y) - (node.x === next.x ? 0 : 10);

      return {
        id: `${node.id}-${next.id}`,
        path: `M ${node.x} ${node.y} Q ${controlX} ${controlY} ${next.x} ${next.y}`,
      };
    });

    const stars = [
      { id: 's1', x: Math.max(10, paddingX - 10), y: topInset - 4, r: 1.2 },
      { id: 's2', x: graphWidth * 0.31, y: height - 16, r: 1.4 },
      { id: 's3', x: graphWidth * 0.56, y: Math.max(8, topInset - 10), r: 1.1 },
      { id: 's4', x: graphWidth * 0.84, y: height * 0.42, r: 1.3 },
      { id: 's5', x: graphWidth - paddingX + 8, y: height - 28, r: 1.1 },
    ];

    return { stageAnchors, nodes, edges, stars, iconSize };
  }, [stages, graphWidth, height]);

  if (stages.length === 0) {
    return (
      <div
        ref={containerRef}
        className={cn(
          'flex items-center justify-center rounded-[1.1rem] border border-dashed border-border/60 bg-background/20 text-[11px] text-muted-foreground',
          className
        )}
        style={responsive ? { width: '100%', height } : { width: graphWidth, height }}
      >
        No stages
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={cn(
        'relative overflow-hidden rounded-[1.25rem] border border-border/60 bg-[radial-gradient(circle_at_50%_50%,hsl(var(--primary)/0.08),transparent_58%),linear-gradient(180deg,hsl(var(--background)/0.72)_0%,hsl(var(--background)/0.92)_100%)]',
        className
      )}
      style={responsive ? { width: '100%', height } : { width: graphWidth, height }}
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_18%,hsl(var(--glow)/0.16),transparent_18%),radial-gradient(circle_at_82%_24%,hsl(var(--star)/0.08),transparent_16%),radial-gradient(circle_at_50%_78%,hsl(var(--gold)/0.08),transparent_18%)] opacity-90" />

      <svg
        width={graphWidth}
        height={height}
        className="absolute inset-0 h-full w-full"
        aria-hidden="true"
      >
        {layout.stageAnchors.map((anchor) => (
          <g key={`guide-${anchor.id}`}>
            <line
              x1={anchor.x}
              y1={14}
              x2={anchor.x}
              y2={height - 14}
              stroke="hsl(var(--border) / 0.24)"
              strokeWidth="1"
              strokeDasharray="2 6"
            />
            <circle cx={anchor.x} cy={height - 12} r="1.8" fill="hsl(var(--gold) / 0.78)" />
          </g>
        ))}

        {layout.edges.map((edge, index) => (
          <g key={edge.id}>
            <path
              d={edge.path}
              fill="none"
              stroke="hsl(var(--border) / 0.35)"
              strokeWidth="3"
              strokeLinecap="round"
            />
            <path
              d={edge.path}
              fill="none"
              stroke={index % 2 === 0 ? 'hsl(var(--gold) / 0.62)' : 'hsl(var(--primary) / 0.58)'}
              strokeWidth="1.35"
              strokeLinecap="round"
            />
          </g>
        ))}

        {layout.stars.map((star) => (
          <circle key={star.id} cx={star.x} cy={star.y} r={star.r} fill="hsl(var(--star) / 0.85)" />
        ))}
      </svg>

      {layout.nodes.map((node) => (
        <div
          key={node.id}
          className="absolute -translate-x-1/2 -translate-y-1/2"
          style={{ left: node.x, top: node.y }}
          aria-label={`${node.stageLabel}: ${node.displayName}`}
          title={`${node.stageLabel}: ${node.displayName}`}
        >
          <span className="relative inline-flex rounded-full p-[2px] shadow-[0_0_22px_hsl(var(--gold)/0.18)]">
            <span className="absolute inset-0 rounded-full border border-primary/20 bg-background/18 backdrop-blur-sm" />
            <ThemedAgentIcon
              slug={node.slug}
              name={node.displayName}
              size={layout.iconSize}
              className="relative border-border/50 shadow-[0_0_0_1px_hsl(var(--background)/0.75)]"
            />
          </span>
        </div>
      ))}
    </div>
  );
});
