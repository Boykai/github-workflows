import { describe, expect, it, vi } from 'vitest';
import { screen, render } from '@/test/test-utils';
import { SettingsPage } from './SettingsPage';

vi.mock('@/components/common/CelestialLoader', () => ({
  CelestialLoader: ({ label }: { label?: string }) => <div data-testid="loader">{label}</div>,
}));

vi.mock('@/components/settings/PrimarySettings', () => ({
  PrimarySettings: () => <div data-testid="primary-settings">Primary Settings</div>,
}));

vi.mock('@/components/settings/AdvancedSettings', () => ({
  AdvancedSettings: () => <div data-testid="advanced-settings">Advanced Settings</div>,
}));

const mockUserSettings = vi.hoisted(() => ({
  settings: null as { ai: { model: string } } | null,
  isLoading: false,
  updateSettings: vi.fn(),
  isUpdating: false,
}));

const mockGlobalSettings = vi.hoisted(() => ({
  settings: null as Record<string, unknown> | null,
  isLoading: false,
  updateSettings: vi.fn(),
  isUpdating: false,
}));

vi.mock('@/hooks/useSettings', () => ({
  useUserSettings: () => mockUserSettings,
  useGlobalSettings: () => mockGlobalSettings,
}));

describe('SettingsPage', () => {
  it('shows loader when user settings are loading', () => {
    mockUserSettings.isLoading = true;
    mockUserSettings.settings = null;
    render(<SettingsPage />);
    expect(screen.getByTestId('loader')).toHaveTextContent('Loading settings');
    mockUserSettings.isLoading = false;
  });

  it('renders primary and advanced settings when loaded', () => {
    mockUserSettings.settings = { ai: { model: 'gpt-4' } };
    render(<SettingsPage />);
    expect(screen.getByTestId('primary-settings')).toBeInTheDocument();
    expect(screen.getByTestId('advanced-settings')).toBeInTheDocument();
    mockUserSettings.settings = null;
  });

  it('renders the section heading', () => {
    mockUserSettings.settings = { ai: { model: 'gpt-4' } };
    render(<SettingsPage />);
    expect(screen.getByText('Settings')).toBeInTheDocument();
    expect(screen.getByText('Configure your preferences for Solune.')).toBeInTheDocument();
    mockUserSettings.settings = null;
  });
});
