import { describe, expect, it } from 'vitest';
import { ZodError } from 'zod';

import { ProjectListResponseSchema } from '@/services/schemas/projects';
import { validateResponse } from '@/services/schemas/validate';

describe('validateResponse', () => {
  it('throws when a required project field is renamed', () => {
    const invalidResponse = {
      projects: [
        {
          projectId: 'PVT_123',
          owner_id: 'owner-1',
          owner_login: 'octocat',
          name: 'Test Project',
          type: 'organization',
          url: 'https://example.test/project',
          status_columns: [],
          cached_at: '2026-03-16T00:00:00Z',
        },
      ],
    };

    expect(() =>
      validateResponse(ProjectListResponseSchema, invalidResponse, 'projectsApi.list')
    ).toThrow(ZodError);
  });
});