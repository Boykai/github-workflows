# Frontend Dockerfile - Multi-stage build

# Build stage
FROM node:25-alpine AS builder

WORKDIR /app

# Copy package files (including .npmrc for peer-dep compat)
COPY package.json package-lock.json* .npmrc ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:1.29.7-alpine

# Patch OS-level vulnerabilities
RUN apk update --no-cache && apk upgrade --no-cache

# Create non-root user for nginx
RUN addgroup -S nginx-app && adduser -S -G nginx-app nginx-app \
    && sed -i 's|/run/nginx.pid|/tmp/nginx/nginx.pid|' /etc/nginx/nginx.conf \
    && mkdir -p /var/cache/nginx /var/run /tmp/nginx \
    && chown -R nginx-app:nginx-app /var/cache/nginx /var/run /tmp/nginx \
    && chown -R nginx-app:nginx-app /usr/share/nginx/html \
    && chown -R nginx-app:nginx-app /etc/nginx/conf.d

# Copy built assets
COPY --from=builder --chown=nginx-app:nginx-app /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY --chown=nginx-app:nginx-app nginx.conf /etc/nginx/conf.d/default.conf

# Switch to non-root user
USER nginx-app

# Expose non-privileged port
EXPOSE 8080

# Health check (non-privileged port)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# Run nginx
CMD ["nginx", "-g", "daemon off;"]
