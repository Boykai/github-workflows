#!/bin/bash
# Post-start script for GitHub Codespaces / Dev Containers
# This runs every time the container starts

set -e

echo "🔄 Starting development services..."

# Activate virtual environment
source /workspace/.venv/bin/activate 2>/dev/null || true

# Update GitHub OAuth callback URL for Codespaces
if [ -n "$CODESPACE_NAME" ]; then
    echo "☁️  Running in GitHub Codespaces: $CODESPACE_NAME"
    
    # Get the Codespaces forwarded URL for port 3003
    FRONTEND_URL="https://${CODESPACE_NAME}-3003.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
    CALLBACK_URL="${FRONTEND_URL}/api/v1/auth/github/callback"
    
    echo "📍 Frontend URL: $FRONTEND_URL"
    echo "🔗 OAuth Callback URL: $CALLBACK_URL"
    echo ""
    echo "⚠️  Update your GitHub OAuth App settings:"
    echo "   Authorization callback URL: $CALLBACK_URL"
    echo ""
    
    # Update .env if it exists
    if [ -f /workspace/.env ]; then
        sed -i "s|GITHUB_REDIRECT_URI=.*|GITHUB_REDIRECT_URI=$CALLBACK_URL|g" /workspace/.env
        sed -i "s|FRONTEND_URL=.*|FRONTEND_URL=$FRONTEND_URL|g" /workspace/.env
        echo "✅ Updated .env with Codespaces URLs"
    fi
fi

echo "✅ Ready for development!"
