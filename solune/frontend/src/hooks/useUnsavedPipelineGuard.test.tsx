import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';

vi.mock('@/hooks/useUnsavedChanges', () => ({
  useUnsavedChanges: vi.fn(),
}));

vi.mock('@/hooks/useUndoableDelete', () => ({
  useUndoableDelete: vi.fn(),
}));

vi.mock('@/hooks/usePipelineConfig', () => ({
  pipelineKeys: {
    all: ['pipelines'] as const,
    list: (projectId: string) => ['pipelines', 'list', projectId],
    detail: (projectId: string, pipelineId: string) => [
      'pipelines',
      'detail',
      projectId,
      pipelineId,
    ],
    assignment: (projectId: string) => ['pipelines', 'assignment', projectId],
  },
}));

import { useUnsavedPipelineGuard } from './useUnsavedPipelineGuard';
import { useUnsavedChanges } from '@/hooks/useUnsavedChanges';
import { useUndoableDelete } from '@/hooks/useUndoableDelete';

const mockUseUnsavedChanges = useUnsavedChanges as ReturnType<typeof vi.fn>;
const mockUseUndoableDelete = useUndoableDelete as ReturnType<typeof vi.fn>;

function createMockPipelineConfig(overrides: Record<string, unknown> = {}) {
  return {
    isDirty: false,
    editingPipelineId: 'pipe-1',
    pipeline: { name: 'My Pipeline' },
    loadPipeline: vi.fn().mockResolvedValue(undefined),
    duplicatePipeline: vi.fn().mockResolvedValue(undefined),
    newPipeline: vi.fn(),
    deletePipeline: vi.fn().mockResolvedValue(undefined),
    savePipeline: vi.fn().mockResolvedValue(true),
    discardChanges: vi.fn(),
    ...overrides,
  };
}

function createDefaultOptions(overrides: Record<string, unknown> = {}) {
  return {
    pipelineConfig: createMockPipelineConfig(overrides),
    projectId: 'proj-1',
    confirm: vi.fn().mockResolvedValue(true),
    focusPipelineEditor: vi.fn(),
    columns: [{ status: { name: 'Todo' } }, { status: { name: 'Done' } }],
  };
}

describe('useUnsavedPipelineGuard', () => {
  const mockUndoableDelete = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseUnsavedChanges.mockReturnValue({ blocker: { state: 'idle' }, isBlocked: false });
    mockUseUndoableDelete.mockReturnValue({ undoableDelete: mockUndoableDelete });
  });

  it('handleWorkflowSelect opens dialog when dirty', () => {
    const options = createDefaultOptions({ isDirty: true });

    const { result } = renderHook(() => useUnsavedPipelineGuard(options));

    act(() => {
      result.current.handleWorkflowSelect('pipe-2');
    });

    expect(result.current.unsavedDialog.isOpen).toBe(true);
    expect(result.current.unsavedDialog.description).toContain('discard');
    expect(options.pipelineConfig.loadPipeline).not.toHaveBeenCalled();
  });

  it('handleWorkflowSelect loads directly when not dirty', () => {
    const options = createDefaultOptions({ isDirty: false });

    const { result } = renderHook(() => useUnsavedPipelineGuard(options));

    act(() => {
      result.current.handleWorkflowSelect('pipe-2');
    });

    expect(result.current.unsavedDialog.isOpen).toBe(false);
    expect(options.pipelineConfig.loadPipeline).toHaveBeenCalledWith('pipe-2');
  });

  it('handleDelete confirms before deleting', async () => {
    const options = createDefaultOptions();

    const { result } = renderHook(() => useUnsavedPipelineGuard(options));

    await act(async () => {
      await result.current.handleDelete();
    });

    expect(options.confirm).toHaveBeenCalledWith(
      expect.objectContaining({
        title: 'Delete Pipeline',
        variant: 'danger',
      }),
    );
    expect(mockUndoableDelete).toHaveBeenCalledWith(
      expect.objectContaining({
        id: 'pipe-1',
        entityLabel: 'Pipeline: My Pipeline',
      }),
    );
  });

  it('handleDelete does nothing when confirm is rejected', async () => {
    const options = createDefaultOptions();
    (options.confirm as ReturnType<typeof vi.fn>).mockResolvedValue(false);

    const { result } = renderHook(() => useUnsavedPipelineGuard(options));

    await act(async () => {
      await result.current.handleDelete();
    });

    expect(mockUndoableDelete).not.toHaveBeenCalled();
  });

  it('handleUnsavedSave saves and runs pending action', async () => {
    const options = createDefaultOptions({ isDirty: true });

    const { result } = renderHook(() => useUnsavedPipelineGuard(options));

    // First, trigger the dialog by selecting a workflow while dirty
    act(() => {
      result.current.handleWorkflowSelect('pipe-2');
    });
    expect(result.current.unsavedDialog.isOpen).toBe(true);

    // Now save
    await act(async () => {
      await result.current.handleUnsavedSave();
    });

    expect(options.pipelineConfig.savePipeline).toHaveBeenCalled();
    expect(result.current.unsavedDialog.isOpen).toBe(false);
  });

  it('handleUnsavedCancel closes dialog without action', () => {
    const options = createDefaultOptions({ isDirty: true });

    const { result } = renderHook(() => useUnsavedPipelineGuard(options));

    act(() => {
      result.current.handleWorkflowSelect('pipe-2');
    });
    expect(result.current.unsavedDialog.isOpen).toBe(true);

    act(() => {
      result.current.handleUnsavedCancel();
    });

    expect(result.current.unsavedDialog.isOpen).toBe(false);
    expect(options.pipelineConfig.loadPipeline).not.toHaveBeenCalled();
    expect(options.pipelineConfig.savePipeline).not.toHaveBeenCalled();
  });

  it('handleUnsavedDiscard discards changes and runs pending action', () => {
    const options = createDefaultOptions({ isDirty: true });

    const { result } = renderHook(() => useUnsavedPipelineGuard(options));

    act(() => {
      result.current.handleWorkflowSelect('pipe-2');
    });

    act(() => {
      result.current.handleUnsavedDiscard();
    });

    expect(options.pipelineConfig.discardChanges).toHaveBeenCalled();
    expect(result.current.unsavedDialog.isOpen).toBe(false);
  });

  it('handleDelete does nothing when projectId is null', async () => {
    const options = createDefaultOptions();
    options.projectId = null as unknown as string;

    const { result } = renderHook(() => useUnsavedPipelineGuard(options));

    await act(async () => {
      await result.current.handleDelete();
    });

    expect(options.confirm).not.toHaveBeenCalled();
    expect(mockUndoableDelete).not.toHaveBeenCalled();
  });
});
