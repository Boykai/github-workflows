# Quickstart: Full Dependency & Pattern Modernization

**Feature Branch**: `024-deps-modernization`

## Verification Commands

After implementing all changes, run these commands to verify the modernization is complete and correct.

### Backend Verification

```bash
cd backend

# 1. Clean install
rm -rf .venv
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 2. Verify no python-jose
pip list | grep jose  # Should return nothing

# 3. Lint (expanded rules)
ruff check src/       # Zero violations
ruff format --check src/

# 4. Type check
pyright src/          # Zero errors

# 5. Tests
pytest                # All pass

# 6. Quick smoke test
uvicorn src.main:app --host 0.0.0.0 --port 8000 &
sleep 3
curl -s http://localhost:8000/api/health | grep -q ok && echo "Health OK"
kill %1
```

### Frontend Verification

```bash
cd frontend

# 1. Clean install
rm -rf node_modules
npm install           # Zero peer dependency warnings

# 2. Verify removals
npm ls socket.io-client 2>&1 | grep -q "empty" && echo "socket.io-client removed"
npm ls autoprefixer 2>&1 | grep -q "empty" && echo "autoprefixer removed"
npm ls postcss 2>&1 | grep -q "empty" && echo "postcss removed"

# 3. Verify deleted files
test ! -f tailwind.config.js && echo "tailwind.config.js deleted"
test ! -f postcss.config.js && echo "postcss.config.js deleted"

# 4. Type check
npx tsc --noEmit      # Zero errors

# 5. Lint
npm run lint          # Zero errors

# 6. Tests
npm run test          # All pass

# 7. Production build
npm run build         # Completes successfully, outputs to dist/
```

### Docker Verification

```bash
cd ..  # Repository root

# Build both images
docker compose build  # Both succeed

# Start and verify
docker compose up -d
sleep 10

# Health checks
curl -s http://localhost:8000/api/health | grep -q ok && echo "Backend healthy"
curl -s http://localhost:5173/ | grep -q "<div" && echo "Frontend serving"

# Cleanup
docker compose down
```

### Visual Verification Checklist

After starting the app, manually verify:

- [ ] Light mode renders correctly (warm theme colors)
- [ ] Dark mode renders correctly (toggle via class)
- [ ] All buttons, inputs, cards display properly
- [ ] Hover/focus states work (outline, ring, shadow)
- [ ] Drag-and-drop (dnd-kit) works on project boards
- [ ] Animations play (accordion, transitions)
- [ ] No broken layout or missing styles
