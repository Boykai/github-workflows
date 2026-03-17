import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';

const mockSetTheme = vi.fn();
const mockUpdateSettings = vi.fn().mockResolvedValue({});

vi.mock('@/components/ThemeProvider', () => ({
  useTheme: vi.fn(() => ({ theme: 'dark', setTheme: mockSetTheme })),
}));

vi.mock('@/hooks/useSettings', () => ({
  useUserSettings: vi.fn(() => ({
    settings: {
      display: { theme: 'dark' },
    },
    updateSettings: mockUpdateSettings,
  })),
}));

import { useTheme } from '@/components/ThemeProvider';
import { useUserSettings } from '@/hooks/useSettings';
import { useAppTheme } from './useAppTheme';

const mockUseTheme = useTheme as ReturnType<typeof vi.fn>;
const mockUseUserSettings = useUserSettings as ReturnType<typeof vi.fn>;

describe('useAppTheme', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseTheme.mockReturnValue({ theme: 'dark', setTheme: mockSetTheme });
    mockUseUserSettings.mockReturnValue({
      settings: { display: { theme: 'dark' } },
      updateSettings: mockUpdateSettings,
    });
  });

  it('reports isDarkMode=true when theme is dark', () => {
    const { result } = renderHook(() => useAppTheme());
    expect(result.current.isDarkMode).toBe(true);
  });

  it('reports isDarkMode=false when theme is light', () => {
    mockUseTheme.mockReturnValue({ theme: 'light', setTheme: mockSetTheme });

    const { result } = renderHook(() => useAppTheme());
    expect(result.current.isDarkMode).toBe(false);
  });

  it('toggleTheme switches from dark to light', () => {
    const { result } = renderHook(() => useAppTheme());

    act(() => {
      result.current.toggleTheme();
    });

    expect(mockSetTheme).toHaveBeenCalledWith('light');
  });

  it('toggleTheme switches from light to dark', () => {
    mockUseTheme.mockReturnValue({ theme: 'light', setTheme: mockSetTheme });

    const { result } = renderHook(() => useAppTheme());

    act(() => {
      result.current.toggleTheme();
    });

    expect(mockSetTheme).toHaveBeenCalledWith('dark');
  });

  it('persists theme to API when settings are loaded', () => {
    const { result } = renderHook(() => useAppTheme());

    act(() => {
      result.current.toggleTheme();
    });

    expect(mockUpdateSettings).toHaveBeenCalledWith({ display: { theme: 'light' } });
  });

  it('does not call updateSettings when settings is null', () => {
    mockUseUserSettings.mockReturnValue({
      settings: null,
      updateSettings: mockUpdateSettings,
    });

    const { result } = renderHook(() => useAppTheme());

    act(() => {
      result.current.toggleTheme();
    });

    expect(mockUpdateSettings).not.toHaveBeenCalled();
  });

  it('handles system theme preference', () => {
    mockUseTheme.mockReturnValue({ theme: 'system', setTheme: mockSetTheme });

    // Mock matchMedia for dark preference
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: query === '(prefers-color-scheme: dark)',
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      })),
    });

    const { result } = renderHook(() => useAppTheme());
    expect(result.current.isDarkMode).toBe(true);
  });
});
