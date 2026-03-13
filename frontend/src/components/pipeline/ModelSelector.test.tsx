import { describe, expect, it, vi, beforeEach } from 'vitest';
import { screen, render } from '@/test/test-utils';
import userEvent from '@testing-library/user-event';
import { ModelSelector } from './ModelSelector';

const mockModels = vi.hoisted(() => [
  { id: 'gpt-4o', name: 'GPT-4o', provider: 'OpenAI', costTier: 'standard', contextWindow: 128000 },
  { id: 'claude-3', name: 'Claude 3', provider: 'Anthropic', costTier: 'premium', contextWindow: 200000 },
]);

vi.mock('@/hooks/useModels', () => ({
  useModels: () => ({
    models: mockModels,
    modelsByProvider: [
      { provider: 'OpenAI', models: [mockModels[0]] },
      { provider: 'Anthropic', models: [mockModels[1]] },
    ],
    isLoading: false,
    isRefreshing: false,
    refreshModels: vi.fn(),
  }),
}));

describe('ModelSelector', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows "Select model" when nothing is selected', () => {
    render(
      <ModelSelector selectedModelId={null} onSelect={vi.fn()} />
    );
    expect(screen.getByText('Select model')).toBeInTheDocument();
  });

  it('shows selected model name', () => {
    render(
      <ModelSelector selectedModelId="gpt-4o" onSelect={vi.fn()} />
    );
    expect(screen.getByText('GPT-4o')).toBeInTheDocument();
  });

  it('shows selectedModelName fallback when model not in list', () => {
    render(
      <ModelSelector
        selectedModelId="unknown-id"
        selectedModelName="Custom Model"
        onSelect={vi.fn()}
      />
    );
    expect(screen.getByText('Custom Model')).toBeInTheDocument();
  });

  it('shows autoLabel when allowAuto and nothing selected', () => {
    render(
      <ModelSelector
        selectedModelId={null}
        onSelect={vi.fn()}
        allowAuto
        autoLabel="Automatic"
      />
    );
    expect(screen.getByText('Automatic')).toBeInTheDocument();
  });

  it('disables button when disabled prop is true', () => {
    render(
      <ModelSelector selectedModelId={null} onSelect={vi.fn()} disabled />
    );
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('opens popover on trigger click', async () => {
    const user = userEvent.setup();
    render(
      <ModelSelector selectedModelId={null} onSelect={vi.fn()} />
    );
    await user.click(screen.getByRole('button'));
    expect(screen.getByPlaceholderText('Search models...')).toBeInTheDocument();
  });

  it('renders custom trigger when provided', () => {
    render(
      <ModelSelector
        selectedModelId={null}
        onSelect={vi.fn()}
        trigger={<span>Custom Trigger</span>}
      />
    );
    expect(screen.getByText('Custom Trigger')).toBeInTheDocument();
  });
});
