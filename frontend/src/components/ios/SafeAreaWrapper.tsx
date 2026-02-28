/**
 * SafeAreaWrapper — applies iOS safe-area inset padding so content
 * is not obscured by the Dynamic Island or the home indicator.
 *
 * On web the CSS env() values resolve to 0 px, so the wrapper is a
 * transparent pass-through outside of a native Capacitor shell.
 */

import type { ReactNode } from 'react';
import { isNativePlatform } from '@/services/capacitor';

interface SafeAreaWrapperProps {
  children: ReactNode;
}

export function SafeAreaWrapper({ children }: SafeAreaWrapperProps) {
  if (!isNativePlatform()) {
    return <>{children}</>;
  }

  return (
    <div
      style={{
        paddingTop: 'var(--safe-area-top)',
        paddingBottom: 'var(--safe-area-bottom)',
        paddingLeft: 'var(--safe-area-left)',
        paddingRight: 'var(--safe-area-right)',
      }}
      className="flex flex-col h-full"
    >
      {children}
    </div>
  );
}
