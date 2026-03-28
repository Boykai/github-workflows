import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

// NOTE: The "vitest/suite" deprecation warning printed during test runs
// originates from @fast-check/vitest@0.3.0 and cannot be fixed in project
// code.  It will be resolved once fast-check publishes an updated release.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      include: ['src/**/*.{ts,tsx}'],
      exclude: ['src/test/**', 'src/main.tsx', 'src/vite-env.d.ts'],
      all: true,
      thresholds: {
        statements: 50,
        branches: 44,
        functions: 41,
        lines: 50,
      },
    },
  },
});
