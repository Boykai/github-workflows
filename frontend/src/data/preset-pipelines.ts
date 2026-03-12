/**
 * Static preset pipeline definitions for "Spec Kit" and "GitHub Copilot".
 * These are seeded into the backend on first load and displayed as
 * read-only system presets in the Saved Workflows list.
 */

import type { PresetPipelineDefinition } from '@/types';

export const PRESET_PIPELINES: PresetPipelineDefinition[] = [
  {
    presetId: 'spec-kit',
    name: 'Spec Kit',
    description: 'Full specification workflow: specify → plan → tasks → implement → analyze',
    stages: [
      {
        id: 'preset-sk-stage-1',
        name: 'Specify',
        order: 0,
        groups: [
          {
            id: 'preset-sk-group-1',
            order: 0,
            execution_mode: 'sequential',
            agents: [
              {
                id: 'preset-sk-agent-1',
                agent_slug: 'speckit-specify',
                agent_display_name: 'Spec Writer',
                model_id: '',
                model_name: '',
                tool_ids: [],
                tool_count: 0,
                config: {},
              },
            ],
          },
        ],
        agents: [],
        execution_mode: 'sequential',
      },
      {
        id: 'preset-sk-stage-2',
        name: 'Plan',
        order: 1,
        groups: [
          {
            id: 'preset-sk-group-2',
            order: 0,
            execution_mode: 'sequential',
            agents: [
              {
                id: 'preset-sk-agent-2',
                agent_slug: 'speckit-plan',
                agent_display_name: 'Planner',
                model_id: '',
                model_name: '',
                tool_ids: [],
                tool_count: 0,
                config: {},
              },
            ],
          },
        ],
        agents: [],
        execution_mode: 'sequential',
      },
      {
        id: 'preset-sk-stage-3',
        name: 'Tasks',
        order: 2,
        groups: [
          {
            id: 'preset-sk-group-3',
            order: 0,
            execution_mode: 'sequential',
            agents: [
              {
                id: 'preset-sk-agent-3',
                agent_slug: 'speckit-tasks',
                agent_display_name: 'Task Generator',
                model_id: '',
                model_name: '',
                tool_ids: [],
                tool_count: 0,
                config: {},
              },
            ],
          },
        ],
        agents: [],
        execution_mode: 'sequential',
      },
      {
        id: 'preset-sk-stage-4',
        name: 'Implement',
        order: 3,
        groups: [
          {
            id: 'preset-sk-group-4',
            order: 0,
            execution_mode: 'sequential',
            agents: [
              {
                id: 'preset-sk-agent-4',
                agent_slug: 'speckit-implement',
                agent_display_name: 'Implementer',
                model_id: '',
                model_name: '',
                tool_ids: [],
                tool_count: 0,
                config: {},
              },
            ],
          },
        ],
        agents: [],
        execution_mode: 'sequential',
      },
      {
        id: 'preset-sk-stage-5',
        name: 'Analyze',
        order: 4,
        groups: [
          {
            id: 'preset-sk-group-5',
            order: 0,
            execution_mode: 'sequential',
            agents: [
              {
                id: 'preset-sk-agent-5',
                agent_slug: 'speckit-analyze',
                agent_display_name: 'Analyzer',
                model_id: '',
                model_name: '',
                tool_ids: [],
                tool_count: 0,
                config: {},
              },
            ],
          },
        ],
        agents: [],
        execution_mode: 'sequential',
      },
    ],
  },
  {
    presetId: 'github-copilot',
    name: 'GitHub Copilot',
    description: 'Single-stage pipeline powered by GitHub Copilot',
    stages: [
      {
        id: 'preset-gc-stage-1',
        name: 'Execute',
        order: 0,
        groups: [
          {
            id: 'preset-gc-group-1',
            order: 0,
            execution_mode: 'sequential',
            agents: [
              {
                id: 'preset-gc-agent-1',
                agent_slug: 'copilot',
                agent_display_name: 'GitHub Copilot',
                model_id: 'gpt-4o',
                model_name: 'GPT-4o',
                tool_ids: [],
                tool_count: 0,
                config: {},
              },
            ],
          },
        ],
        agents: [],
        execution_mode: 'sequential',
      },
    ],
  },
];
