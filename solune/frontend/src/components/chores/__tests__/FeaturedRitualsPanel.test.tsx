import { describe, expect, it } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { FeaturedRitualsPanel } from '../FeaturedRitualsPanel';
import type { Chore } from '@/types';

function createChore(overrides: Partial<Chore> = {}): Chore {
  return {
    id: 'chore-1',
    project_id: 'PVT_1',
    name: 'Weekly Review',
    template_path: '.github/ISSUE_TEMPLATE/chore-weekly-review.md',
    template_content: 'Review the board',
    schedule_type: 'time',
    schedule_value: 7,
    status: 'active',
    last_triggered_at: null,
    last_triggered_count: 0,
    current_issue_number: null,
    current_issue_node_id: null,
    pr_number: null,
    pr_url: null,
    tracking_issue_number: null,
    execution_count: 0,
    ai_enhance_enabled: true,
    agent_pipeline_id: '',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('FeaturedRitualsPanel', () => {
  it('renders an onboarding empty state when no chores exist', () => {
    render(<FeaturedRitualsPanel chores={[]} parentIssueCount={0} />);

    expect(screen.getByText('No rituals yet')).toBeInTheDocument();
    expect(screen.getByText(/Create your first chore/)).toBeInTheDocument();
  });

  it('prioritizes chores that are ready to trigger for Next Run and keeps all three cards visible', () => {
    render(
      <FeaturedRitualsPanel
        chores={[
          createChore({
            id: 'count-due',
            name: 'Count-based ritual',
            schedule_type: 'count',
            schedule_value: 3,
            last_triggered_count: 2,
            execution_count: 1,
          }),
          createChore({
            id: 'time-not-due',
            name: 'Time-based ritual',
            schedule_type: 'time',
            schedule_value: 7,
            created_at: '2099-01-01T00:00:00Z',
            updated_at: '2099-01-01T00:00:00Z',
            execution_count: 5,
          }),
        ]}
        parentIssueCount={5}
      />
    );

    expect(screen.getByText('Count-based ritual')).toBeInTheDocument();
    expect(screen.getByText('Ready to trigger')).toBeInTheDocument();
    expect(screen.getByText('Next Run')).toBeInTheDocument();
    expect(screen.getByText('Most Recently Run')).toBeInTheDocument();
    expect(screen.getByText('Most Run')).toBeInTheDocument();
  });
});
