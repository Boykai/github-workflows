import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import reactHooks from 'eslint-plugin-react-hooks';
import jsxA11y from 'eslint-plugin-jsx-a11y';
import security from 'eslint-plugin-security';

export default tseslint.config(
  { ignores: ['dist', 'node_modules', 'coverage', 'test-results', 'e2e-report'] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ['**/*.{ts,tsx}'],
    plugins: {
      'react-hooks': reactHooks,
      'jsx-a11y': jsxA11y,
      security,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      ...jsxA11y.configs.recommended.rules,
      ...security.configs.recommended.rules,
      'security/detect-object-injection': 'off',
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
      'jsx-a11y/label-has-associated-control': ['error', {
        assert: 'either',
        depth: 3,
      }],
    },
  },
  {
    files: ['**/*.test.{ts,tsx}'],
    rules: {
      'security/detect-non-literal-fs-filename': 'off',
      'security/detect-unsafe-regex': 'off',
    },
  }
);
