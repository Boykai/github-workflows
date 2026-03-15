/**
 * Integration tests for DynamicDropdown loading/empty/error/success states.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, userEvent } from '@/test/test-utils';
import { DynamicDropdown } from './DynamicDropdown';
import type { ModelsResponse } from '@/types';

const defaultProps = {
  value: '',
  onChange: vi.fn(),
  provider: 'copilot',
  supportsDynamic: true,
  modelsResponse: undefined as ModelsResponse | undefined,
  isLoading: false,
  onRetry: vi.fn(),
  label: 'Model',
  id: 'model-select',
};

describe('DynamicDropdown', () => {
  it('renders loading state with spinner', () => {
    render(<DynamicDropdown {...defaultProps} isLoading={true} />);
    expect(screen.getByText('Loading models...')).toBeInTheDocument();
    expect(screen.getByLabelText('Loading Model')).toBeInTheDocument();
  });

  it('renders error state with retry button', () => {
    const modelsResponse: ModelsResponse = {
      status: 'error',
      models: [],
      fetched_at: null,
      cache_hit: false,
      rate_limit_warning: false,
      message: 'Connection failed',
    };
    render(<DynamicDropdown {...defaultProps} modelsResponse={modelsResponse} />);
    expect(screen.getByText('Connection failed')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
  });

  it('calls onRetry when retry button is clicked', async () => {
    const onRetry = vi.fn();
    const modelsResponse: ModelsResponse = {
      status: 'error',
      models: [],
      fetched_at: null,
      cache_hit: false,
      rate_limit_warning: false,
      message: 'Error',
    };
    render(<DynamicDropdown {...defaultProps} modelsResponse={modelsResponse} onRetry={onRetry} />);
    await userEvent.setup().click(screen.getByRole('button', { name: 'Retry' }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('renders success state with model options', () => {
    const modelsResponse: ModelsResponse = {
      status: 'success',
      models: [
        { id: 'gpt-4o', name: 'GPT-4o', provider: 'copilot' },
        { id: 'gpt-3.5', name: 'GPT-3.5', provider: 'copilot' },
      ],
      fetched_at: new Date().toISOString(),
      cache_hit: false,
      rate_limit_warning: false,
      message: null,
    };
    render(<DynamicDropdown {...defaultProps} modelsResponse={modelsResponse} />);
    const select = screen.getByLabelText('Model');
    expect(select).toBeInTheDocument();
    expect(screen.getByText('GPT-4o')).toBeInTheDocument();
    expect(screen.getByText('GPT-3.5')).toBeInTheDocument();
  });

  it('renders empty state when no models available', () => {
    const modelsResponse: ModelsResponse = {
      status: 'success',
      models: [],
      fetched_at: new Date().toISOString(),
      cache_hit: false,
      rate_limit_warning: false,
      message: null,
    };
    render(<DynamicDropdown {...defaultProps} modelsResponse={modelsResponse} />);
    expect(screen.getByText('No models available for this provider')).toBeInTheDocument();
  });

  it('renders auth_required state', () => {
    const modelsResponse: ModelsResponse = {
      status: 'auth_required',
      models: [],
      fetched_at: null,
      cache_hit: false,
      rate_limit_warning: false,
      message: 'Please authenticate first',
    };
    render(<DynamicDropdown {...defaultProps} modelsResponse={modelsResponse} />);
    expect(screen.getByText('Please authenticate first')).toBeInTheDocument();
  });

  it('renders static fallback for non-dynamic providers', () => {
    render(
      <DynamicDropdown
        {...defaultProps}
        supportsDynamic={false}
        staticOptions={[{ id: 'model-1', name: 'Model One' }]}
      />
    );
    expect(screen.getByText('Model One')).toBeInTheDocument();
  });
});
