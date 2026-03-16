/**
 * Tests for EssentialSettings component.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, userEvent } from '@/test/test-utils';
import { EssentialSettings } from './EssentialSettings';
import type { AIPreferences, UserPreferencesUpdate } from '@/types';

// ── Hoisted mocks ──

const mocks = vi.hoisted(() => ({
  refetchModels: vi.fn(),
}));

vi.mock('@/hooks/useSettings', () => ({
  useModelOptions: () => ({
    data: { status: 'success', models: ['gpt-4', 'gpt-3.5'] },
    isLoading: false,
    refetch: mocks.refetchModels,
  }),
}));

// ── Fixtures ──

const defaultAISettings: AIPreferences = {
  provider: 'copilot',
  model: 'gpt-4',
  agent_model: 'gpt-4',
  temperature: 0.7,
};

describe('EssentialSettings', () => {
  let onSave: ReturnType<typeof vi.fn<(u: UserPreferencesUpdate) => Promise<void>>>;

  beforeEach(() => {
    vi.clearAllMocks();
    onSave = vi.fn().mockResolvedValue(undefined);
  });

  it('renders provider selection', () => {
    render(<EssentialSettings settings={defaultAISettings} onSave={onSave} />);
    expect(screen.getByLabelText('Model Provider')).toBeInTheDocument();
    expect(screen.getByText('GitHub Copilot')).toBeInTheDocument();
  });

  it('renders chat model dropdown', () => {
    render(<EssentialSettings settings={defaultAISettings} onSave={onSave} />);
    expect(screen.getByText('Chat Model')).toBeInTheDocument();
  });

  it('renders agent model dropdown', () => {
    render(<EssentialSettings settings={defaultAISettings} onSave={onSave} />);
    expect(screen.getByText('Agent Model (Auto)')).toBeInTheDocument();
  });

  it('renders temperature slider with current value', () => {
    render(<EssentialSettings settings={defaultAISettings} onSave={onSave} />);
    expect(screen.getByText('Temperature: 0.7')).toBeInTheDocument();
    expect(screen.getByText('Precise (0)')).toBeInTheDocument();
    expect(screen.getByText('Creative (2)')).toBeInTheDocument();
  });

  it('shows AI Configuration title and description', () => {
    render(<EssentialSettings settings={defaultAISettings} onSave={onSave} />);
    expect(screen.getByRole('heading', { name: 'AI Configuration' })).toBeInTheDocument();
    expect(screen.getByText(/Select your AI provider and model/)).toBeInTheDocument();
  });

  it('renders provider options', () => {
    render(<EssentialSettings settings={defaultAISettings} onSave={onSave} />);
    const select = screen.getByLabelText('Model Provider');
    expect(select).toHaveValue('copilot');
  });

  it('changing provider marks form as dirty and enables save', async () => {
    render(<EssentialSettings settings={defaultAISettings} onSave={onSave} />);
    const user = userEvent.setup();

    await user.selectOptions(screen.getByLabelText('Model Provider'), 'azure_openai');

    expect(screen.getByRole('button', { name: 'Save' })).toBeEnabled();
  });

  it('renders agent model description text', () => {
    render(<EssentialSettings settings={defaultAISettings} onSave={onSave} />);
    expect(
      screen.getByText(/Fallback model for all GitHub Copilot Agents/)
    ).toBeInTheDocument();
  });
});
