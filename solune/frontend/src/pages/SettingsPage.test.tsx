import { describe, it, expect, vi } from 'vitest';
import { render } from '@/test/test-utils';
import { expectNoA11yViolations } from '@/test/a11y-helpers';
import { SettingsPage } from './SettingsPage';

vi.mock('@/hooks/useSettings', () => ({
  useUserSettings: () => ({
    settings: undefined,
    isLoading: false,
    error: null,
    updateSettings: vi.fn(),
    isUpdating: false,
  }),
  useGlobalSettings: () => ({
    settings: undefined,
    isLoading: false,
    error: null,
    updateSettings: vi.fn(),
    isUpdating: false,
  }),
}));

describe('SettingsPage', () => {
  it('renders without crashing', () => {
    render(<SettingsPage />);
    expect(document.body).toBeDefined();
  });

  it('has no accessibility violations', async () => {
    const { container } = render(<SettingsPage />);
    await expectNoA11yViolations(container);
  });
});
