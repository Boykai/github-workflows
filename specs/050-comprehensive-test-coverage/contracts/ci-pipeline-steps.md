# Contract: CI Pipeline Coverage Steps

**Feature**: `050-comprehensive-test-coverage`
**Date**: 2026-03-17

---

## Coverage Ratchet Step (`.github/workflows/ci.yml`)

### Backend Coverage Check

Added after the existing `pytest --cov` step:

```yaml
- name: Check coverage ratchet
  run: |
    python -c "
    import json, xml.etree.ElementTree as ET, sys
    
    # Read baseline
    with open('../../.coverage-baseline.json') as f:
        baseline = json.load(f)
    
    # Read current coverage from coverage.xml
    tree = ET.parse('coverage.xml')
    root = tree.getroot()
    current_lines = float(root.attrib['line-rate']) * 100
    current_branches = float(root.attrib.get('branch-rate', 0)) * 100
    
    # Compare
    failures = []
    if current_lines < baseline['backend']['lines']:
        failures.append(f'lines: {current_lines:.1f}% < baseline {baseline[\"backend\"][\"lines\"]}%')
    if current_branches < baseline['backend'].get('branches', 0):
        failures.append(f'branches: {current_branches:.1f}% < baseline {baseline[\"backend\"][\"branches\"]}%')
    
    if failures:
        print('COVERAGE REGRESSION DETECTED:')
        for f in failures:
            print(f'  {f}')
        sys.exit(1)
    print('Coverage ratchet: PASSED')
    "
```

### Frontend Coverage Check

Added after the existing `npm run test:coverage` step:

```yaml
- name: Check coverage ratchet
  run: |
    node -e "
    const baseline = require('../../.coverage-baseline.json');
    const summary = require('./coverage/coverage-summary.json');
    const total = summary.total;
    const checks = [
      ['statements', total.statements.pct, baseline.frontend.statements],
      ['branches', total.branches.pct, baseline.frontend.branches],
      ['functions', total.functions.pct, baseline.frontend.functions],
      ['lines', total.lines.pct, baseline.frontend.lines],
    ];
    const failures = checks.filter(([, current, base]) => current < base);
    if (failures.length) {
      console.log('COVERAGE REGRESSION DETECTED:');
      failures.forEach(([name, current, base]) => 
        console.log('  ' + name + ': ' + current + '% < baseline ' + base + '%'));
      process.exit(1);
    }
    console.log('Coverage ratchet: PASSED');
    "
```

---

## Diff-Cover Step

### Backend (after coverage report generation)

```yaml
- name: Diff-cover report
  if: github.event_name == 'pull_request'
  run: |
    pip install diff-cover
    diff-cover coverage.xml --compare-branch=origin/${{ github.base_ref }} --fail-under=0
  continue-on-error: true
```

### Frontend (after coverage report generation)

```yaml
- name: Diff-cover report
  if: github.event_name == 'pull_request'
  run: |
    npx diff-cover --coverage-xml coverage/cobertura-coverage.xml --compare-branch=origin/${{ github.base_ref }}
  continue-on-error: true
```

---

## Flaky Test Detection Job

### Nightly Schedule

```yaml
name: Flaky Test Detection
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
  workflow_dispatch: {}

jobs:
  detect-flaky:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run flaky detection (backend)
        run: |
          cd solune/backend
          pip install -e ".[dev]"
          python scripts/detect_flaky.py --count=5 --output=flaky-report.json
      - name: Run flaky detection (frontend)
        run: |
          cd solune/frontend
          npm ci
          npx vitest run --reporter=json --outputFile=test-results.json --retry=5
```

---

## Mutation Testing Expansion

### Backend Shard Additions (`.github/workflows/mutation.yml`)

Current shards: `auth-and-projects`, `orchestration`, `app-and-data`, `agents-and-integrations`

New shards to add:

```yaml
matrix:
  shard:
    - auth-and-projects
    - orchestration
    - app-and-data
    - agents-and-integrations
    - api-endpoints          # NEW: src/api/*.py
    - middleware              # NEW: src/middleware/*.py
    - models                 # NEW: src/models/*.py
```

### Frontend Stryker Expansion (`solune/frontend/stryker.config.mjs`)

```javascript
mutate: [
  'src/hooks/**/*.ts',
  'src/lib/**/*.ts',
  'src/services/**/*.ts',   // NEW
  'src/utils/**/*.ts',      // NEW
  '!src/**/*.test.ts',
  '!src/**/*.property.test.ts',
],
thresholds: {
  high: 80,
  low: 60,
  break: 60,  // CHANGED: now blocking
},
```
