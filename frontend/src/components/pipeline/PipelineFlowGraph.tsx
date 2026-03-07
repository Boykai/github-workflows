/**
 * PipelineFlowGraph — compact SVG visualization of pipeline stage execution order.
 * Renders a horizontal node-edge diagram for use on Saved Workflows and Recent Activity cards.
 */

import { memo, useMemo } from 'react';
import type { PipelineStage } from '@/types';

interface PipelineFlowGraphProps {
  stages: PipelineStage[];
  width?: number;
  height?: number;
  className?: string;
}

export const PipelineFlowGraph = memo(function PipelineFlowGraph({
  stages,
  width = 200,
  height = 48,
  className = '',
}: PipelineFlowGraphProps) {
  const nodes = useMemo(() => {
    if (stages.length === 0) return [];

    const padding = 8;
    const nodeHeight = 20;
    const usableWidth = width - padding * 2;
    const nodeWidth = Math.min(
      Math.max(usableWidth / stages.length - 8, 24),
      60
    );
    const totalNodesWidth = stages.length * nodeWidth + (stages.length - 1) * 8;
    const startX = (width - totalNodesWidth) / 2;
    const y = (height - nodeHeight) / 2;

    return stages.map((stage, i) => ({
      id: stage.id,
      label: stage.name,
      agentCount: stage.agents.length,
      x: startX + i * (nodeWidth + 8),
      y,
      w: nodeWidth,
      h: nodeHeight,
    }));
  }, [stages, width, height]);

  if (stages.length === 0) {
    return (
      <svg width={width} height={height} className={className}>
        <text
          x={width / 2}
          y={height / 2}
          textAnchor="middle"
          dominantBaseline="central"
          className="fill-muted-foreground text-[9px]"
        >
          No stages
        </text>
      </svg>
    );
  }

  return (
    <svg width={width} height={height} className={className}>
      {/* Edges */}
      {nodes.map((node, i) => {
        if (i === nodes.length - 1) return null;
        const next = nodes[i + 1];
        return (
          <line
            key={`edge-${node.id}`}
            x1={node.x + node.w}
            y1={node.y + node.h / 2}
            x2={next.x}
            y2={next.y + next.h / 2}
            className="stroke-border"
            strokeWidth={1.5}
          />
        );
      })}

      {/* Nodes */}
      {nodes.map((node) => (
        <g key={node.id}>
          <rect
            x={node.x}
            y={node.y}
            width={node.w}
            height={node.h}
            rx={4}
            className="fill-primary/10 stroke-primary/40"
            strokeWidth={1}
          />
          <text
            x={node.x + node.w / 2}
            y={node.y + node.h / 2}
            textAnchor="middle"
            dominantBaseline="central"
            className="fill-foreground text-[7px] font-medium"
          >
            {node.agentCount}
          </text>
        </g>
      ))}
    </svg>
  );
});
