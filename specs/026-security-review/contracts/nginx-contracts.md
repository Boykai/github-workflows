# Nginx & Docker Contracts: Security, Privacy & Vulnerability Audit

## frontend/nginx.conf — Target Configuration

```nginx
server_tokens off;

server {
    listen 8080;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json application/xml;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' https://avatars.githubusercontent.com; connect-src 'self' wss:; frame-ancestors 'none'" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
    # REMOVED: X-XSS-Protection (deprecated in modern browsers)

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "OK";
        add_header Content-Type text/plain;
    }

    # API proxy (WebSocket support)
    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # Serve static files with caching
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### Header Changes Summary

| Header | Before | After |
|--------|--------|-------|
| X-Frame-Options | SAMEORIGIN | SAMEORIGIN (unchanged) |
| X-Content-Type-Options | nosniff | nosniff (unchanged) |
| X-XSS-Protection | 1; mode=block | **REMOVED** (deprecated) |
| Content-Security-Policy | (missing) | **ADDED** |
| Strict-Transport-Security | (missing) | **ADDED** |
| Referrer-Policy | (missing) | **ADDED** |
| Permissions-Policy | (missing) | **ADDED** |
| server_tokens | (default: on) | **off** |
| listen port | 80 | **8080** (non-root compatible) |

## frontend/Dockerfile — Non-Root Target

```dockerfile
# Build stage
FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Create non-root user and prepare directories
RUN addgroup -S nginx-app && adduser -S -G nginx-app nginx-app \
    && mkdir -p /var/cache/nginx /var/run /tmp/nginx \
    && chown -R nginx-app:nginx-app /var/cache/nginx /var/run /tmp/nginx \
    && chown -R nginx-app:nginx-app /usr/share/nginx/html \
    && chown -R nginx-app:nginx-app /etc/nginx/conf.d

# Copy built assets
COPY --from=builder --chown=nginx-app:nginx-app /app/dist /usr/share/nginx/html

# Copy nginx configuration (listens on 8080, non-privileged port)
COPY --chown=nginx-app:nginx-app nginx.conf /etc/nginx/conf.d/default.conf

# Switch to non-root user
USER nginx-app

# Expose non-privileged port
EXPOSE 8080

# Health check (updated port)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

## docker-compose.yml — Target Configuration

```yaml
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: ghchat-backend
    restart: unless-stopped
    ports:
      - "127.0.0.1:8000:8000"    # Localhost only (not 0.0.0.0)
    environment:
      - GITHUB_CLIENT_ID=${GITHUB_CLIENT_ID}
      - GITHUB_CLIENT_SECRET=${GITHUB_CLIENT_SECRET}
      - SESSION_SECRET_KEY=${SESSION_SECRET_KEY}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}               # Now required in production
      - GITHUB_WEBHOOK_SECRET=${GITHUB_WEBHOOK_SECRET} # Now required in production
      - DEBUG=${DEBUG:-false}
      - ENABLE_DOCS=${ENABLE_DOCS:-false}              # New: independent docs toggle
      - DATABASE_PATH=/var/lib/ghchat/data/settings.db
    volumes:
      - ghchat-data:/var/lib/ghchat/data   # Outside app root (/app)
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"]
    depends_on:
      signal-api:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: ghchat-frontend
    ports:
      - "127.0.0.1:5173:8080"    # Localhost only; nginx on 8080 (non-root)
    depends_on:
      backend:
        condition: service_healthy

volumes:
  ghchat-data:
```

### docker-compose.yml Changes Summary

| Setting | Before | After |
|---------|--------|-------|
| Backend port | `8000:8000` | `127.0.0.1:8000:8000` |
| Frontend port | `5173:80` | `127.0.0.1:5173:8080` |
| Backend volume | `ghchat-data:/app/data` | `ghchat-data:/var/lib/ghchat/data` |
| ENCRYPTION_KEY | `${ENCRYPTION_KEY:-}` (optional) | `${ENCRYPTION_KEY}` (required) |
| ENABLE_DOCS | (missing) | `${ENABLE_DOCS:-false}` (new) |
| DATABASE_PATH | (missing) | `/var/lib/ghchat/data/settings.db` (new) |

## .github/workflows/branch-issue-link.yml — Target Permissions

```yaml
permissions: {}  # Default: no permissions

jobs:
  link-branch:
    permissions:
      issues: write    # Required: add branch-linked comment to issue
      contents: read   # Required: read branch ref for issue number extraction
```
