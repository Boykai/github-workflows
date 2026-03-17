import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const SRC_ROOT = path.resolve(__dirname, '../../');

// Pre-existing violations that are permitted (do not add new ones)
const HOOKS_COMPONENTS_ALLOWLIST = new Set([
  'hooks/useAppTheme.ts → @/components/ThemeProvider',
  'hooks/useCommands.ts → @/components/ThemeProvider',
  'hooks/useConfirmation.tsx → @/components/ui/confirmation-dialog',
  'hooks/useMentionAutocomplete.ts → @/components/chat/MentionInput',
]);

function makeAllowlistKey(file: string, imp: string): string {
  const rel = path.relative(SRC_ROOT, file);
  return `${rel} → ${imp}`;
}

function getFilesRecursive(dir: string, ext: string[]): string[] {
  if (!fs.existsSync(dir)) return [];
  const results: string[] = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...getFilesRecursive(full, ext));
    } else if (ext.some((e) => entry.name.endsWith(e))) {
      results.push(full);
    }
  }
  return results;
}

function extractImports(filePath: string): string[] {
  const content = fs.readFileSync(filePath, 'utf-8');
  const imports: string[] = [];
  // Match ES import statements: import ... from '...'
  const importRegex = /import\s+(?:[\s\S]*?\s+from\s+)?['"]([^'"]+)['"]/g;
  let match: RegExpExecArray | null;
  while ((match = importRegex.exec(content)) !== null) {
    imports.push(match[1]);
  }
  return imports;
}

function relativeToSrc(filePath: string): string {
  return path.relative(SRC_ROOT, filePath);
}

describe('Architecture Import Boundaries', () => {
  it('pages/ does not import from other pages', () => {
    const pagesDir = path.join(SRC_ROOT, 'pages');
    const files = getFilesRecursive(pagesDir, ['.ts', '.tsx']).filter(
      (f) => !f.includes('.test.'),
    );
    const violations: string[] = [];

    for (const file of files) {
      const imports = extractImports(file);
      for (const imp of imports) {
        // Check relative imports that reach into pages/
        if (imp.includes('/pages/') || (imp.startsWith('.') && imp.includes('Page'))) {
          // Allow importing from same file (re-exports)
          const importedBase = path.basename(imp).replace(/\.(ts|tsx)$/, '');
          const fileBase = path.basename(file).replace(/\.(ts|tsx)$/, '');
          if (importedBase !== fileBase) {
            violations.push(`${relativeToSrc(file)} imports ${imp}`);
          }
        }
      }
    }

    expect(violations).toEqual([]);
  });

  it('hooks/ does not import from components', () => {
    const hooksDir = path.join(SRC_ROOT, 'hooks');
    const files = getFilesRecursive(hooksDir, ['.ts', '.tsx']).filter(
      (f) => !f.includes('.test.'),
    );
    const violations: string[] = [];

    for (const file of files) {
      const imports = extractImports(file);
      for (const imp of imports) {
        if (imp.includes('/components/') || imp.includes('/components')) {
          const key = makeAllowlistKey(file, imp);
          if (!HOOKS_COMPONENTS_ALLOWLIST.has(key)) {
            violations.push(`${relativeToSrc(file)} imports ${imp}`);
          }
        }
      }
    }

    expect(violations).toEqual([]);
  });

  it('utils/ does not import from hooks or components', () => {
    const utilsDir = path.join(SRC_ROOT, 'utils');
    const files = getFilesRecursive(utilsDir, ['.ts', '.tsx']).filter(
      (f) => !f.includes('.test.'),
    );
    const violations: string[] = [];

    for (const file of files) {
      const imports = extractImports(file);
      for (const imp of imports) {
        if (imp.includes('/hooks/') || imp.includes('/hooks')) {
          violations.push(`${relativeToSrc(file)} imports ${imp} (hooks)`);
        }
        if (imp.includes('/components/') || imp.includes('/components')) {
          violations.push(`${relativeToSrc(file)} imports ${imp} (components)`);
        }
      }
    }

    expect(violations).toEqual([]);
  });
});
