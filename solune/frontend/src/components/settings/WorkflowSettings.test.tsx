import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { WorkflowSettings } from './WorkflowSettings';
import type { UseFormReturn } from 'react-hook-form';
import type { GlobalFormState } from './globalSettingsSchema';

// ── Helpers ──

function createMockForm(): UseFormReturn<GlobalFormState> {
  const register = vi.fn((name: string) => ({
    name,
    onChange: vi.fn(),
    onBlur: vi.fn(),
    ref: vi.fn(),
  }));

  return {
    register,
    handleSubmit: vi.fn(),
    formState: { errors: {}, isDirty: false, isValid: true },
    watch: vi.fn(),
    setValue: vi.fn(),
    getValues: vi.fn(),
    reset: vi.fn(),
    trigger: vi.fn(),
    control: {} as UseFormReturn<GlobalFormState>['control'],
    unregister: vi.fn(),
    setError: vi.fn(),
    clearErrors: vi.fn(),
    setFocus: vi.fn(),
    getFieldState: vi.fn(),
    resetField: vi.fn(),
  } as unknown as UseFormReturn<GlobalFormState>;
}

// ── Tests ──

describe('WorkflowSettings', () => {
  it('renders all three form fields', () => {
    const form = createMockForm();
    render(<WorkflowSettings form={form} />);

    expect(screen.getByLabelText('Default Repository')).toBeInTheDocument();
    expect(screen.getByLabelText('Default Assignee')).toBeInTheDocument();
    expect(screen.getByLabelText('Polling Interval (seconds)')).toBeInTheDocument();
  });

  it('registers fields with correct names', () => {
    const form = createMockForm();
    render(<WorkflowSettings form={form} />);

    expect(form.register).toHaveBeenCalledWith('default_repository');
    expect(form.register).toHaveBeenCalledWith('default_assignee');
    expect(form.register).toHaveBeenCalledWith('copilot_polling_interval', { valueAsNumber: true });
  });

  it('renders the Workflow section heading', () => {
    const form = createMockForm();
    render(<WorkflowSettings form={form} />);

    expect(screen.getByText('Workflow')).toBeInTheDocument();
  });
});
