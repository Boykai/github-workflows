import { describe, expect } from 'vitest';
import { test, fc } from '@fast-check/vitest';
import {
  needsMigration,
  migrateStageToGroupFormat,
  migratePipelineToGroupFormat,
  ensureDefaultGroups,
} from './pipelineMigration';
import type { PipelineStage, PipelineConfig, PipelineAgentNode } from '@/types';

function makeAgent(slug: string): PipelineAgentNode {
  return {
    id: `agent-${slug}`,
    agent_slug: slug,
    agent_display_name: slug,
    model_id: 'gpt-4o',
    model_name: 'GPT-4o',
    tool_ids: [],
    tool_count: 0,
    config: {},
  };
}

function makeStage(overrides: Partial<PipelineStage> = {}): PipelineStage {
  return {
    id: 'stage-1',
    name: 'Test Stage',
    order: 0,
    groups: [],
    agents: [],
    execution_mode: 'sequential',
    ...overrides,
  };
}

function makeConfig(stages: PipelineStage[]): PipelineConfig {
  return {
    id: 'config-1',
    project_id: 'proj-1',
    name: 'Test Pipeline',
    description: 'test',
    stages,
    is_preset: false,
    created_at: '2025-01-01',
    updated_at: '2025-01-01',
  };
}

describe('pipelineMigration property tests', () => {
  test.prop([fc.array(fc.string({ minLength: 1, maxLength: 10 }), { minLength: 1, maxLength: 5 })])(
    'migrateStageToGroupFormat is idempotent',
    (agentSlugs) => {
      const agents = agentSlugs.map(makeAgent);
      const legacyStage = makeStage({ agents, groups: [] });

      const migrated = migrateStageToGroupFormat(legacyStage);
      const migratedTwice = migrateStageToGroupFormat(migrated);

      expect(migratedTwice.groups).toEqual(migrated.groups);
      expect(migratedTwice.agents).toEqual(migrated.agents);
    },
  );

  test.prop([fc.array(fc.string({ minLength: 1, maxLength: 10 }), { minLength: 1, maxLength: 5 })])(
    'migration preserves all agents',
    (agentSlugs) => {
      const agents = agentSlugs.map(makeAgent);
      const legacyStage = makeStage({ agents, groups: [] });

      const migrated = migrateStageToGroupFormat(legacyStage);
      const groupAgents = migrated.groups?.flatMap((g: { agents: PipelineAgentNode[] }) => g.agents) ?? [];

      expect(groupAgents.length).toBe(agents.length);
      for (const agent of agents) {
        expect(groupAgents).toContainEqual(agent);
      }
    },
  );

  test.prop([fc.integer({ min: 0, max: 5 })])(
    'migratePipelineToGroupFormat produces no legacy stages',
    (stageCount) => {
      const stages = Array.from({ length: stageCount }, (_, i) =>
        makeStage({
          id: `stage-${i}`,
          order: i,
          agents: [makeAgent(`agent-${i}`)],
          groups: [],
        }),
      );
      const config = makeConfig(stages);
      const migrated = migratePipelineToGroupFormat(config);

      for (const stage of migrated.stages) {
        if (stage.agents.length > 0) {
          expect(stage.groups!.length).toBeGreaterThan(0);
        }
      }
    },
  );

  test('empty config needs no migration', () => {
    const config = makeConfig([]);
    expect(needsMigration(config)).toBe(false);
  });

  test.prop([fc.integer({ min: 0, max: 5 })])(
    'ensureDefaultGroups gives every stage at least one group',
    (stageCount) => {
      const stages = Array.from({ length: stageCount }, (_, i) =>
        makeStage({ id: `stage-${i}`, order: i, agents: [], groups: [] }),
      );
      const config = makeConfig(stages);
      const result = ensureDefaultGroups(config);

      for (const stage of result.stages) {
        expect(stage.groups!.length).toBeGreaterThanOrEqual(1);
      }
    },
  );
});
