#!/bin/bash
# Post-create script for GitHub Codespaces / Dev Containers
# This runs once after the container is created

set -e

echo "🚀 Setting up agentic development environment..."

# Navigate to workspace
cd /workspace

# Copy .env.example if .env doesn't exist
if [ ! -f .env ]; then
    echo "📋 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please update .env with your credentials"
fi

# Setup Python virtual environment
echo "🐍 Setting up Python environment..."
cd /workspace/backend
python -m venv /workspace/.venv
source /workspace/.venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd /workspace/frontend
npm install

# Install Playwright browsers for e2e tests
echo "🎭 Installing Playwright browsers..."
npx playwright install --with-deps chromium

echo "✅ Development environment setup complete!"
echo ""
echo "🎯 Quick Start:"
echo "  - Backend:  cd backend && source ../.venv/bin/activate && uvicorn src.main:app --reload"
echo "  - Frontend: cd frontend && npm run dev"
echo "  - Docker:   docker compose up --build"
echo ""
echo "📝 Don't forget to update your .env file with:"
echo "  - GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET"
echo "  - AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY"
echo "  - SESSION_SECRET_KEY"
