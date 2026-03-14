#!/usr/bin/env node
/**
 * audit-theme-colors.mjs
 *
 * Scans frontend component, page, and layout files for hardcoded colour
 * literals that bypass the Celestial design-system token pipeline.
 *
 * Exit 0 — no un-approved violations found
 * Exit 1 — un-approved hardcoded colour violations detected
 *
 * Usage:
 *   node frontend/scripts/audit-theme-colors.mjs
 */

import { readFileSync, readdirSync } from 'node:fs';
import { join, relative, extname, sep } from 'node:path';

/* ── Configuration ── */

const ROOT = new URL('..', import.meta.url).pathname.replace(/\/$/, '');

const SCAN_DIRS = [
  join(ROOT, 'src/components'),
  join(ROOT, 'src/pages'),
  join(ROOT, 'src/layout'),
];

const APPROVED_EXCEPTIONS = new Set([
  'src/components/agents/AgentAvatar.tsx',
  'src/components/board/colorUtils.ts',
  'src/components/board/IssueCard.tsx',
]);

/** Patterns that indicate a hardcoded colour value. */
const COLOUR_PATTERNS = [
  // Hex (#abc, #aabbcc, #aabbccdd)
  { re: /#[0-9a-fA-F]{3,8}\b/g, label: 'hex' },
  // rgb()/rgba() with literal numbers (not using var())
  { re: /rgba?\(\s*\d/g, label: 'rgb/rgba' },
  // hsl()/hsla() with literal numbers (not using var())
  { re: /hsla?\(\s*\d/g, label: 'hsl/hsla' },
];

/* ── Helpers ── */

function collectFiles(dir) {
  const results = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...collectFiles(full));
    } else if (['.tsx', '.ts'].includes(extname(entry.name)) && !entry.name.includes('.test.')) {
      results.push(full);
    }
  }
  return results;
}

/* ── Main scan ── */

let violations = 0;
let exceptionHits = 0;

for (const dir of SCAN_DIRS) {
  for (const file of collectFiles(dir)) {
    const rel = relative(ROOT, file).split(sep).join('/');
    const isException = APPROVED_EXCEPTIONS.has(rel);
    const lines = readFileSync(file, 'utf8').split('\n');

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      // Determine whether this line contains any hardcoded colour pattern.
      let hasHardcodedColour = false;
      for (const { re } of COLOUR_PATTERNS) {
        re.lastIndex = 0;
        if (re.exec(line)) {
          hasHardcodedColour = true;
          break;
        }
      }
      // Skip lines that only reference CSS custom properties (valid usage)
      if (/hsl\(\s*var\(--/.test(line) && !hasHardcodedColour) continue;

      for (const { re, label } of COLOUR_PATTERNS) {
        re.lastIndex = 0;
        const match = re.exec(line);
        if (match) {
          if (isException) {
            exceptionHits++;
          } else {
            violations++;
            console.log(`VIOLATION [${label}] ${rel}:${i + 1} → ${line.trim()}`);
          }
          break; // one report per line
        }
      }
    }
  }
}

console.log('');
console.log(`Scan complete — ${violations} violation(s), ${exceptionHits} approved exception hit(s).`);

process.exit(violations > 0 ? 1 : 0);
