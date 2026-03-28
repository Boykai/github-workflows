#!/bin/bash
# Post-create script for GitHub Codespaces / Dev Containers
# This runs once after the container is created

set -e

echo "🚀 Setting up Solune development environment..."

# Navigate to workspace
cd /workspace

# Copy .env.example if .env doesn't exist
if [ ! -f solune/.env ]; then
    echo "📋 Creating .env from .env.example..."
    cp solune/.env.example solune/.env
    echo "⚠️  Please update solune/.env with your credentials"
fi

# Setup Python environment with uv
echo "🐍 Setting up Python environment..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
cd /workspace/solune/backend
uv sync --extra dev

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd /workspace/solune/frontend
npm install

# Install Playwright browsers for e2e tests
echo "🎭 Installing Playwright browsers..."
npx playwright install --with-deps chromium

echo "✅ Development environment setup complete!"
echo ""
echo "🎯 Quick Start:"
echo "  - Backend:  cd solune/backend && source .venv/bin/activate && uvicorn src.main:app --reload"
echo "  - Frontend: cd solune/frontend && npm run dev"
echo "  - Docker:   docker compose up --build"
echo ""
echo "📝 Don't forget to update your solune/.env file with:"
echo "  - GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET"
echo "  - AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY"
echo "  - SESSION_SECRET_KEY"
