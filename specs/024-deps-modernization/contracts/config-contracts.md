# Config Contracts: Full Dependency & Pattern Modernization

This directory defines the target state of configuration files after the modernization.

## backend/pyproject.toml

### Target Dependencies
```toml
[project]
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.135.0",
    "uvicorn[standard]>=0.41.0",
    "githubkit>=0.14.6",
    "httpx>=0.28.0",
    "pydantic>=2.12.0",
    "pydantic-settings>=2.13.0",
    "python-multipart>=0.0.22",
    "pyyaml>=6.0.3",
    "github-copilot-sdk>=0.1.30",
    "openai>=2.26.0",
    "azure-ai-inference>=1.0.0b9",
    "aiosqlite>=0.22.0",
    "tenacity>=9.1.0",
    "websockets>=16.0",
    # REMOVED: python-jose[cryptography] (unused)
]

[project.optional-dependencies]
dev = [
    "pytest>=9.0.0",
    "pytest-asyncio>=1.3.0",
    "pytest-cov>=7.0.0",
    "ruff>=0.15.0",
    "pyright>=1.1.408",
]
```

### Target Tool Config
```toml
[tool.ruff]
target-version = "py313"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "FURB", "PTH", "PERF", "RUF"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"

[tool.pyright]
pythonVersion = "3.13"
```

## frontend/package.json

### Target Dependencies
```json
{
  "dependencies": {
    "@dnd-kit/core": "^6.3.1",
    "@dnd-kit/modifiers": "^9.0.0",
    "@dnd-kit/sortable": "^10.0.0",
    "@dnd-kit/utilities": "^3.2.2",
    "@radix-ui/react-slot": "^1.2.4",
    "@tanstack/react-query": "^5.90.0",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "lucide-react": "^0.577.0",
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "tailwind-merge": "^3.5.0"
  },
  "devDependencies": {
    "@eslint/js": "^10.0.0",
    "@playwright/test": "^1.58.2",
    "@tailwindcss/vite": "^4.2.0",
    "@testing-library/jest-dom": "^6.9.1",
    "@testing-library/react": "^16.3.2",
    "@testing-library/user-event": "^14.6.1",
    "@types/jest-axe": "^3.5.9",
    "@types/node": "^25.3.0",
    "@types/react": "^19.2.0",
    "@types/react-dom": "^19.2.0",
    "@vitejs/plugin-react": "^5.1.0",
    "@vitest/coverage-v8": "^4.0.18",
    "eslint": "^10.0.0",
    "eslint-plugin-jsx-a11y": "^6.10.2",
    "eslint-plugin-react-hooks": "^7.0.0",
    "happy-dom": "^20.8.0",
    "jest-axe": "^10.0.0",
    "jsdom": "^28.1.0",
    "prettier": "^3.8.0",
    "tailwindcss": "^4.2.0",
    "typescript": "~5.9.0",
    "typescript-eslint": "^8.56.0",
    "vite": "^7.3.0",
    "vitest": "^4.0.18"
  }
}
```

### Removed Dependencies
- `socket.io-client` (unused — native WebSocket API used)
- `autoprefixer` (built into Tailwind v4)
- `postcss` (replaced by @tailwindcss/vite)
- `tailwindcss-animate` (built into Tailwind v4)

### Added Dependencies
- `@tailwindcss/vite` (Vite plugin for Tailwind v4)

## frontend/vite.config.ts

### Target Config
```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import path from 'path';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});
```

## Files to Delete

- `frontend/postcss.config.js` — PostCSS no longer needed with @tailwindcss/vite
- `frontend/tailwind.config.js` — Replaced by CSS-first @theme in index.css

## backend/Dockerfile

### Target Base Image
```dockerfile
FROM python:3.13-slim AS base
```

## frontend/Dockerfile

### Target Base Image
```dockerfile
FROM node:22-alpine AS builder
```
