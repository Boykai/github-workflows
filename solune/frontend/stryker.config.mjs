/** @type {import('@stryker-mutator/api/core').PartialStrykerOptions} */
export default {
  testRunner: 'vitest',
  mutate: [
    'src/hooks/**/*.ts',
    'src/lib/**/*.ts',
    '!src/**/*.test.ts',
    '!src/**/*.property.test.ts',
  ],
  reporters: ['html', 'clear-text', 'progress'],
  htmlReporter: {
    fileName: 'reports/mutation/mutation-report.html',
  },
  thresholds: {
    high: 80,
    low: 60,
    break: null,
  },
  timeoutMS: 30000,
  timeoutFactor: 2.5,
  concurrency: 4,
};
