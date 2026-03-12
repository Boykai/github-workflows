/**
 * Tests for pipelineMigration — legacy-to-group format migration utilities.
 */

import { describe, expect, it } from 'vitest';
import {
  isLegacyStage,
  needsMigration,
  migrateStageToGroupFormat,
  migratePipelineToGroupFormat,
  ensureDefaultGroups,
} from './pipelineMigration';
import type { PipelineStage, PipelineConfig, PipelineAgentNode } from '@/types';

function createAgentNode(overrides: Partial<PipelineAgentNode> = {}): PipelineAgentNode {
  return {
    id: 'agent-1',
    agent_slug: 'copilot',
    agent_display_name: 'GitHub Copilot',
    model_id: '',
    model_name: '',
    tool_ids: [],
    tool_count: 0,
    config: {},
    ...overrides,
  };
}

function createStage(overrides: Partial<PipelineStage> = {}): PipelineStage {
  return {
    id: 'stage-1',
    name: 'Build',
    order: 0,
    agents: [],
    execution_mode: 'sequential',
    groups: [],
    ...overrides,
  };
}

function createConfig(stages: PipelineStage[]): PipelineConfig {
  return {
    id: 'pipeline-1',
    project_id: 'proj-1',
    name: 'Test Pipeline',
    description: '',
    stages,
    is_preset: false,
    preset_id: '',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  };
}

describe('isLegacyStage', () => {
  it('returns true when stage has agents but no groups', () => {
    const stage = createStage({
      agents: [createAgentNode()],
      groups: [],
    });
    expect(isLegacyStage(stage)).toBe(true);
  });

  it('returns true when groups is undefined and agents exist', () => {
    const stage = createStage({
      agents: [createAgentNode()],
      groups: undefined,
    });
    expect(isLegacyStage(stage)).toBe(true);
  });

  it('returns false when stage already has groups', () => {
    const stage = createStage({
      groups: [{ id: 'g1', order: 0, execution_mode: 'sequential', agents: [createAgentNode()] }],
      agents: [],
    });
    expect(isLegacyStage(stage)).toBe(false);
  });

  it('returns false for empty stage (no agents, no groups)', () => {
    const stage = createStage({ agents: [], groups: [] });
    expect(isLegacyStage(stage)).toBe(false);
  });
});

describe('needsMigration', () => {
  it('returns true if any stage is legacy', () => {
    const config = createConfig([
      createStage({ groups: [{ id: 'g1', order: 0, execution_mode: 'sequential', agents: [] }] }),
      createStage({ agents: [createAgentNode({ id: 'a2' })], groups: [] }),
    ]);
    expect(needsMigration(config)).toBe(true);
  });

  it('returns false if all stages have groups', () => {
    const config = createConfig([
      createStage({ groups: [{ id: 'g1', order: 0, execution_mode: 'sequential', agents: [] }] }),
    ]);
    expect(needsMigration(config)).toBe(false);
  });
});

describe('migrateStageToGroupFormat', () => {
  it('wraps legacy agents into a single group preserving execution_mode', () => {
    const agents = [createAgentNode({ id: 'a1' }), createAgentNode({ id: 'a2' })];
    const stage = createStage({
      agents,
      execution_mode: 'parallel',
      groups: [],
    });

    const migrated = migrateStageToGroupFormat(stage);

    expect(migrated.groups).toHaveLength(1);
    expect(migrated.groups![0].execution_mode).toBe('parallel');
    expect(migrated.groups![0].agents).toHaveLength(2);
    expect(migrated.groups![0].agents[0].id).toBe('a1');
    expect(migrated.groups![0].agents[1].id).toBe('a2');
  });

  it('is idempotent — leaves already-migrated stages untouched', () => {
    const stage = createStage({
      groups: [{ id: 'g1', order: 0, execution_mode: 'parallel', agents: [createAgentNode()] }],
    });
    const migrated = migrateStageToGroupFormat(stage);
    expect(migrated).toBe(stage); // Same reference — no mutation
  });
});

describe('migratePipelineToGroupFormat', () => {
  it('migrates all legacy stages in a pipeline', () => {
    const config = createConfig([
      createStage({
        id: 's1',
        agents: [createAgentNode({ id: 'a1' })],
        execution_mode: 'sequential',
        groups: [],
      }),
      createStage({
        id: 's2',
        agents: [createAgentNode({ id: 'a2' }), createAgentNode({ id: 'a3' })],
        execution_mode: 'parallel',
        groups: [],
      }),
    ]);

    const migrated = migratePipelineToGroupFormat(config);

    expect(migrated.stages[0].groups).toHaveLength(1);
    expect(migrated.stages[0].groups![0].execution_mode).toBe('sequential');
    expect(migrated.stages[1].groups).toHaveLength(1);
    expect(migrated.stages[1].groups![0].execution_mode).toBe('parallel');
    expect(migrated.stages[1].groups![0].agents).toHaveLength(2);
  });
});

describe('ensureDefaultGroups', () => {
  it('adds a default empty group to empty stages', () => {
    const config = createConfig([
      createStage({ agents: [], groups: [] }),
    ]);

    const result = ensureDefaultGroups(config);

    expect(result.stages[0].groups).toHaveLength(1);
    expect(result.stages[0].groups![0].agents).toHaveLength(0);
    expect(result.stages[0].groups![0].execution_mode).toBe('sequential');
  });

  it('migrates legacy stages with agents', () => {
    const config = createConfig([
      createStage({ agents: [createAgentNode()], groups: [] }),
    ]);

    const result = ensureDefaultGroups(config);

    expect(result.stages[0].groups).toHaveLength(1);
    expect(result.stages[0].groups![0].agents).toHaveLength(1);
  });

  it('leaves already-migrated stages untouched', () => {
    const existingGroups = [
      { id: 'g1', order: 0, execution_mode: 'parallel' as const, agents: [createAgentNode()] },
    ];
    const config = createConfig([
      createStage({ groups: existingGroups }),
    ]);

    const result = ensureDefaultGroups(config);

    expect(result.stages[0].groups).toBe(existingGroups);
  });
});
