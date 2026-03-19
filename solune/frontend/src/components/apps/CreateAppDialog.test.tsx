import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, userEvent } from '@/test/test-utils';
import { CreateAppDialog } from './CreateAppDialog';
import type { AppCreate } from '@/types/apps';

const defaultProps = {
  onClose: vi.fn(),
  onSubmit: vi.fn(),
  isPending: false,
  owners: [{ login: 'test-owner', type: 'User' as const }],
  getErrorMessage: (_err: unknown, fallback: string) => fallback,
  pipelines: [{ id: 'pipe-1', name: 'Default Pipeline', project_id: 'PVT_proj' }],
  isLoadingPipelines: false,
  defaultPipelineId: 'pipe-1',
  projectId: 'PVT_proj123',
};

function renderDialog(overrides: Partial<typeof defaultProps> = {}) {
  return render(<CreateAppDialog {...defaultProps} {...overrides} />);
}

async function fillAndSubmit(
  user: ReturnType<typeof userEvent.setup>,
  { displayName = 'Test App' }: { displayName?: string } = {}
) {
  const input = screen.getByLabelText('Display Name');
  await user.clear(input);
  await user.type(input, displayName);

  const submitBtn = screen.getByRole('button', { name: /^Create App$|^Create Repository/i });
  await user.click(submitBtn);
}

function capturedPayload(): AppCreate | undefined {
  const calls = (defaultProps.onSubmit as ReturnType<typeof vi.fn>).mock.calls;
  return calls.length > 0 ? (calls[0][0] as AppCreate) : undefined;
}

describe('CreateAppDialog — project_id scoping (T015)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('same-repo payload includes project_id when projectId is set', async () => {
    const user = userEvent.setup();
    renderDialog({ initialRepoType: 'same-repo' });
    await fillAndSubmit(user);

    const payload = capturedPayload();
    expect(payload).toBeDefined();
    expect(payload!.repo_type).toBe('same-repo');
    expect(payload!.pipeline_id).toBe('pipe-1');
    expect(payload!.project_id).toBe('PVT_proj123');
  });

  it('new-repo payload omits project_id', async () => {
    const user = userEvent.setup();
    renderDialog({ initialRepoType: 'new-repo' });
    await fillAndSubmit(user);

    const payload = capturedPayload();
    expect(payload).toBeDefined();
    expect(payload!.repo_type).toBe('new-repo');
    expect(payload!.project_id).toBeUndefined();
  });

  it('external-repo payload omits project_id', async () => {
    const user = userEvent.setup();
    renderDialog({ initialRepoType: 'external-repo' });

    const input = screen.getByLabelText('Display Name');
    await user.clear(input);
    await user.type(input, 'Ext App');

    // Fill external repo URL
    const urlInput = screen.getByPlaceholderText(/github\.com/i);
    await user.type(urlInput, 'https://github.com/owner/repo');

    const submitBtn = screen.getByRole('button', { name: /Create App/i });
    await user.click(submitBtn);

    const payload = capturedPayload();
    expect(payload).toBeDefined();
    expect(payload!.repo_type).toBe('external-repo');
    expect(payload!.project_id).toBeUndefined();
  });
});
