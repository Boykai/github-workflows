#!/usr/bin/env node
/**
 * check-theme-contrast.mjs
 *
 * Evaluates WCAG 2.1 AA contrast ratios for the Celestial design-system
 * token pairs and token inventory derived from data-model.md and index.css.
 *
 * NOTE: The token pairs and inventory defined below are a snapshot generated
 * from data-model.md and index.css. If those source files change, this
 * script must be updated to keep the snapshot in sync.
 *
 * Exit 0 — all pairs pass
 * Exit 1 — one or more pairs fail
 *
 * Usage:
 *   node frontend/scripts/check-theme-contrast.mjs
 */

/* ── Inline colour helpers (ESM-compatible, no TS import needed) ── */

function parseHsl(raw) {
  const parts = raw.replace(/%/g, '').trim().split(/\s+/).map(Number);
  if (parts.length !== 3 || parts.some(Number.isNaN)) throw new Error(`Bad HSL: "${raw}"`);
  return parts;
}

function hslToRgb(h, s, l) {
  const sN = s / 100, lN = l / 100;
  const c = (1 - Math.abs(2 * lN - 1)) * sN;
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
  const m = lN - c / 2;
  let r1, g1, b1;
  if (h < 60)       [r1, g1, b1] = [c, x, 0];
  else if (h < 120) [r1, g1, b1] = [x, c, 0];
  else if (h < 180) [r1, g1, b1] = [0, c, x];
  else if (h < 240) [r1, g1, b1] = [0, x, c];
  else if (h < 300) [r1, g1, b1] = [x, 0, c];
  else              [r1, g1, b1] = [c, 0, x];
  return [Math.round((r1 + m) * 255), Math.round((g1 + m) * 255), Math.round((b1 + m) * 255)];
}

function linearize(ch) {
  const c = ch / 255;
  return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
}

function relLum(r, g, b) {
  return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b);
}

function cr(l1, l2) {
  return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
}

function ratio(fgHsl, bgHsl) {
  const [fh, fs, fl] = parseHsl(fgHsl);
  const [bh, bs, bl] = parseHsl(bgHsl);
  const fgL = relLum(...hslToRgb(fh, fs, fl));
  const bgL = relLum(...hslToRgb(bh, bs, bl));
  return Math.round(cr(fgL, bgL) * 100) / 100;
}

/* ── Token inventory (from index.css :root + .dark) ── */

const LIGHT = {
  '--background':              '40 6% 98%',
  '--foreground':              '0 0% 9%',
  '--card':                    '0 0% 100%',
  '--card-foreground':         '0 0% 9%',
  '--popover':                 '0 0% 100%',
  '--popover-foreground':      '0 0% 9%',
  '--primary':                 '42 82% 40%',
  '--primary-foreground':      '0 0% 9%',
  '--secondary':               '40 6% 94%',
  '--secondary-foreground':    '0 0% 14%',
  '--muted':                   '40 4% 94%',
  '--muted-foreground':        '0 0% 40%',
  '--accent':                  '220 8% 12%',
  '--accent-foreground':       '0 0% 100%',
  '--destructive':             '0 72% 51%',
  '--destructive-foreground':  '0 0% 100%',
  '--border':                  '42 10% 54%',
  '--input':                   '40 4% 96%',
  '--ring':                    '42 82% 40%',
  '--panel':                   '40 6% 98%',
  '--panel-foreground':        '0 0% 9%',
  '--priority-p0':             '0 72% 51%',
  '--priority-p1':             '25 95% 47%',
  '--priority-p2':             '217 91% 60%',
  '--priority-p3':             '142 71% 36%',
  '--sync-connected':          '160 84% 33%',
};

const DARK = {
  '--background':              '236 28% 7%',
  '--foreground':              '38 45% 89%',
  '--card':                    '238 22% 11%',
  '--card-foreground':         '38 45% 89%',
  '--popover':                 '238 23% 9%',
  '--popover-foreground':      '38 45% 89%',
  '--primary':                 '45 90% 68%',
  '--primary-foreground':      '236 28% 9%',
  '--secondary':               '237 14% 17%',
  '--secondary-foreground':    '38 45% 89%',
  '--muted':                   '237 16% 13%',
  '--muted-foreground':        '35 24% 72%',
  '--accent':                  '242 28% 25%',
  '--accent-foreground':       '38 45% 89%',
  '--destructive':             '0 65% 53%',
  '--destructive-foreground':  '0 0% 98%',
  '--border':                  '239 18% 46%',
  '--input':                   '238 18% 15%',
  '--ring':                    '45 90% 68%',
  '--panel':                   '238 19% 11%',
  '--panel-foreground':        '38 45% 89%',
  '--priority-p0':             '0 72% 51%',
  '--priority-p1':             '25 95% 53%',
  '--priority-p2':             '217 91% 60%',
  '--priority-p3':             '142 71% 45%',
  '--sync-connected':          '160 84% 47%',
};

/* ── Contrast pairs from data-model.md ── */

const PAIRS = [
  { fg: '--foreground',             bg: '--background',  ctx: 'Page body text',         thr: 4.5 },
  { fg: '--card-foreground',        bg: '--card',        ctx: 'Card body text',         thr: 4.5 },
  { fg: '--popover-foreground',     bg: '--popover',     ctx: 'Popover text',           thr: 4.5 },
  { fg: '--primary-foreground',     bg: '--primary',     ctx: 'Primary btn text',       thr: 4.5 },
  { fg: '--secondary-foreground',   bg: '--secondary',   ctx: 'Secondary btn text',     thr: 4.5 },
  { fg: '--muted-foreground',       bg: '--muted',       ctx: 'Muted text',             thr: 4.5 },
  { fg: '--accent-foreground',      bg: '--accent',      ctx: 'Accent text',            thr: 4.5 },
  { fg: '--destructive-foreground', bg: '--destructive', ctx: 'Destructive btn text',   thr: 4.5 },
  { fg: '--panel-foreground',       bg: '--panel',       ctx: 'Panel body text',        thr: 4.5 },
  { fg: '--muted-foreground',       bg: '--background',  ctx: 'Subtle text on page',    thr: 4.5 },
  { fg: '--primary',                bg: '--background',  ctx: 'Primary links/headings', thr: 3.0 },
  { fg: '--border',                 bg: '--background',  ctx: 'Input/card borders',     thr: 3.0 },
  { fg: '--border',                 bg: '--card',        ctx: 'Card borders',           thr: 3.0 },
  { fg: '--ring',                   bg: '--background',  ctx: 'Focus ring',             thr: 3.0 },
  { fg: '--destructive',            bg: '--background',  ctx: 'Error text',             thr: 3.0 },
  { fg: '--priority-p0',            bg: '--card',        ctx: 'P0 badge',               thr: 3.0 },
  { fg: '--priority-p1',            bg: '--card',        ctx: 'P1 badge',               thr: 3.0 },
  { fg: '--priority-p2',            bg: '--card',        ctx: 'P2 badge',               thr: 3.0 },
  { fg: '--priority-p3',            bg: '--card',        ctx: 'P3 badge',               thr: 3.0 },
  { fg: '--sync-connected',         bg: '--background',  ctx: 'Sync status',            thr: 3.0 },
];

/* ── Evaluate ── */

let failures = 0;

console.log('WCAG 2.1 AA Contrast Audit — Celestial Design System\n');
console.log('| Context                 | Theme | Ratio  | Threshold | Result |');
console.log('|-------------------------|-------|--------|-----------|--------|');

for (const { fg, bg, ctx, thr } of PAIRS) {
  for (const [label, tokens] of [['Light', LIGHT], ['Dark', DARK]]) {
    const fgVal = tokens[fg];
    const bgVal = tokens[bg];
    if (!fgVal || !bgVal) {
      console.log(`| ${ctx.padEnd(24)}| ${label.padEnd(6)}| -      | ${thr}:1      | SKIP   |`);
      continue;
    }
    const r = ratio(fgVal, bgVal);
    const pass = r >= thr;
    if (!pass) failures++;
    const mark = pass ? 'PASS' : 'FAIL';
    console.log(
      `| ${ctx.padEnd(24)}| ${label.padEnd(6)}| ${r.toFixed(2).padStart(6)} | ${thr}:1      | ${mark.padEnd(6)} |`,
    );
  }
}

console.log('');
console.log(failures === 0 ? '✅ All pairs pass.' : `❌ ${failures} pair(s) failed.`);
process.exit(failures > 0 ? 1 : 0);
