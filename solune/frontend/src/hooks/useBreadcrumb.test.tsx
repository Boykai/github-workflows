import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import type { ReactNode } from 'react';
import { BreadcrumbProvider, useBreadcrumb, useBreadcrumbLabels } from './useBreadcrumb';

function wrapper({ children }: { children: ReactNode }) {
  return <BreadcrumbProvider>{children}</BreadcrumbProvider>;
}

describe('useBreadcrumb', () => {
  it('throws when used outside BreadcrumbProvider', () => {
    expect(() => {
      renderHook(() => useBreadcrumb());
    }).toThrow('useBreadcrumb must be used within BreadcrumbProvider');
  });

  it('setLabel adds a label to the map', () => {
    const { result } = renderHook(
      () => ({ breadcrumb: useBreadcrumb(), labels: useBreadcrumbLabels() }),
      { wrapper },
    );

    act(() => {
      result.current.breadcrumb.setLabel('/apps/my-app', 'My App');
    });

    expect(result.current.labels.get('/apps/my-app')).toBe('My App');
  });

  it('removeLabel removes a label from the map', () => {
    const { result } = renderHook(
      () => ({ breadcrumb: useBreadcrumb(), labels: useBreadcrumbLabels() }),
      { wrapper },
    );

    act(() => {
      result.current.breadcrumb.setLabel('/apps/my-app', 'My App');
    });
    expect(result.current.labels.has('/apps/my-app')).toBe(true);

    act(() => {
      result.current.breadcrumb.removeLabel('/apps/my-app');
    });
    expect(result.current.labels.has('/apps/my-app')).toBe(false);
  });

  it('setLabel overwrites existing label for same path', () => {
    const { result } = renderHook(
      () => ({ breadcrumb: useBreadcrumb(), labels: useBreadcrumbLabels() }),
      { wrapper },
    );

    act(() => {
      result.current.breadcrumb.setLabel('/apps/my-app', 'Old Name');
    });
    act(() => {
      result.current.breadcrumb.setLabel('/apps/my-app', 'New Name');
    });

    expect(result.current.labels.get('/apps/my-app')).toBe('New Name');
  });

  it('supports multiple labels simultaneously', () => {
    const { result } = renderHook(
      () => ({ breadcrumb: useBreadcrumb(), labels: useBreadcrumbLabels() }),
      { wrapper },
    );

    act(() => {
      result.current.breadcrumb.setLabel('/apps/app-a', 'App A');
      result.current.breadcrumb.setLabel('/apps/app-b', 'App B');
    });

    expect(result.current.labels.size).toBe(2);
    expect(result.current.labels.get('/apps/app-a')).toBe('App A');
    expect(result.current.labels.get('/apps/app-b')).toBe('App B');
  });
});

describe('useBreadcrumbLabels', () => {
  it('throws when used outside BreadcrumbProvider', () => {
    expect(() => {
      renderHook(() => useBreadcrumbLabels());
    }).toThrow('useBreadcrumbLabels must be used within BreadcrumbProvider');
  });

  it('returns an empty map initially', () => {
    const { result } = renderHook(() => useBreadcrumbLabels(), { wrapper });
    expect(result.current.size).toBe(0);
  });
});
