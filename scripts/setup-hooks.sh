#!/bin/bash
# Setup git hooks for the repository
# Run this script once after cloning the repo

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"
SCRIPTS_DIR="$REPO_ROOT/scripts"

echo "🔧 Setting up git hooks..."

# Create hooks directory if it doesn't exist
mkdir -p "$HOOKS_DIR"

# Install pre-commit hook
if [ -f "$SCRIPTS_DIR/pre-commit" ]; then
    cp "$SCRIPTS_DIR/pre-commit" "$HOOKS_DIR/pre-commit"
    chmod +x "$HOOKS_DIR/pre-commit"
    echo "✅ Installed pre-commit hook"
else
    echo "❌ pre-commit script not found at $SCRIPTS_DIR/pre-commit"
    exit 1
fi

# Install pre-push hook (runs tests)
cat > "$HOOKS_DIR/pre-push" << 'EOF'
#!/bin/bash
# Git pre-push hook - runs tests before pushing
# This ensures tests pass before code is pushed to remote

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"

echo "🧪 Running tests before push..."

# Backend tests
echo ""
echo "📦 Backend tests..."
cd "$REPO_ROOT/backend"
if [ -d ".venv" ]; then
    source .venv/bin/activate 2>/dev/null || true
fi
python -m pytest tests/ -q --tb=short

# Frontend tests
echo ""
echo "🌐 Frontend tests..."
cd "$REPO_ROOT/frontend"
npm test

echo ""
echo "✅ All tests passed! Pushing..."
EOF

chmod +x "$HOOKS_DIR/pre-push"
echo "✅ Installed pre-push hook"

echo ""
echo "🎉 Git hooks installed successfully!"
echo ""
echo "Hooks installed:"
echo "  • pre-commit: Runs linting and format checks"
echo "  • pre-push: Runs all tests"
echo ""
echo "To skip hooks temporarily, use: git commit --no-verify"
