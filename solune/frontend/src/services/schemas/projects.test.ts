import { describe, it, expect } from 'vitest';
import { ProjectListResponseSchema } from './projects';

const validProject = {
  project_id: 'PVT_abc',
  owner_id: 'owner-1',
  owner_login: 'test-org',
  name: 'My Project',
  type: 'organization' as const,
  url: 'https://github.com/orgs/test-org/projects/1',
  status_columns: [
    { field_id: 'f-1', name: 'Todo', option_id: 'opt-1', color: 'GRAY' },
  ],
  cached_at: '2024-01-01T00:00:00Z',
};

describe('ProjectListResponseSchema', () => {
  it('parses valid project list', () => {
    const result = ProjectListResponseSchema.parse({ projects: [validProject] });
    expect(result.projects).toHaveLength(1);
    expect(result.projects[0].name).toBe('My Project');
  });

  it('parses empty projects array', () => {
    const result = ProjectListResponseSchema.parse({ projects: [] });
    expect(result.projects).toEqual([]);
  });

  it('accepts all project type values', () => {
    for (const type of ['organization', 'user', 'repository'] as const) {
      const data = { projects: [{ ...validProject, type }] };
      expect(ProjectListResponseSchema.parse(data).projects[0].type).toBe(type);
    }
  });

  it('parses project with optional description', () => {
    const data = { projects: [{ ...validProject, description: 'A project' }] };
    expect(ProjectListResponseSchema.parse(data).projects[0].description).toBe('A project');
  });

  it('parses project with optional item_count', () => {
    const data = { projects: [{ ...validProject, item_count: 25 }] };
    expect(ProjectListResponseSchema.parse(data).projects[0].item_count).toBe(25);
  });

  it('parses multiple status columns', () => {
    const data = {
      projects: [
        {
          ...validProject,
          status_columns: [
            { field_id: 'f-1', name: 'Todo', option_id: 'opt-1' },
            { field_id: 'f-1', name: 'Done', option_id: 'opt-2', color: 'GREEN' },
          ],
        },
      ],
    };
    const result = ProjectListResponseSchema.parse(data);
    expect(result.projects[0].status_columns).toHaveLength(2);
  });

  it('rejects invalid project type', () => {
    const data = { projects: [{ ...validProject, type: 'team' }] };
    expect(() => ProjectListResponseSchema.parse(data)).toThrow();
  });

  it('rejects missing required fields', () => {
    const { name: _, ...incomplete } = validProject;
    expect(() => ProjectListResponseSchema.parse({ projects: [incomplete] })).toThrow();
  });

  it('parses status column without optional color', () => {
    const data = {
      projects: [
        {
          ...validProject,
          status_columns: [{ field_id: 'f-1', name: 'Todo', option_id: 'opt-1' }],
        },
      ],
    };
    const result = ProjectListResponseSchema.parse(data);
    expect(result.projects[0].status_columns[0].color).toBeUndefined();
  });
});
