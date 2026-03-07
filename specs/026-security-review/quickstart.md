# Quickstart: Security, Privacy & Vulnerability Audit

**Feature Branch**: `026-security-review`

## Verification Commands

After implementing all security changes, run these commands to verify each finding is resolved. These map to the behavior-based verification checks in the specification.

### Phase 1 — Critical Verification

```bash
# Check 1: No credentials in URLs after login
# Start the application, complete OAuth login, then:
# - Browser URL bar should show /auth/callback with NO query parameters
# - Browser history should contain NO session_token entries
# - Server access logs should contain NO session_token values
grep -r "session_token" /var/log/nginx/access.log  # Should return nothing

# Check 2: Backend refuses to start without ENCRYPTION_KEY
cd backend
ENCRYPTION_KEY= GITHUB_WEBHOOK_SECRET=test SESSION_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))") \
  DEBUG=false python -c "from src.config import get_settings; get_settings()"
# Expected: ValueError with "ENCRYPTION_KEY is required in production mode"

# Check 2b: Backend refuses to start without GITHUB_WEBHOOK_SECRET
ENCRYPTION_KEY=test GITHUB_WEBHOOK_SECRET= SESSION_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))") \
  DEBUG=false python -c "from src.config import get_settings; get_settings()"
# Expected: ValueError with "GITHUB_WEBHOOK_SECRET is required in production mode"

# Check 2c: Backend refuses short SESSION_SECRET_KEY
ENCRYPTION_KEY=test GITHUB_WEBHOOK_SECRET=test SESSION_SECRET_KEY=tooshort \
  DEBUG=false python -c "from src.config import get_settings; get_settings()"
# Expected: ValueError with "SESSION_SECRET_KEY must be at least 64 characters"

# Check 3: Frontend container runs as non-root
docker exec ghchat-frontend id
# Expected: uid=100(nginx-app) gid=101(nginx-app)
# Must NOT show uid=0(root)
```

### Phase 2 — High Verification

```bash
# Check 4: Unowned project returns 403
# Authenticate as User A, then request User B's project:
curl -s -o /dev/null -w "%{http_code}" \
  -H "Cookie: session_id=<user_a_session>" \
  http://localhost:8000/api/v1/projects/<user_b_project_id>/tasks
# Expected: 403

# Check 5: WebSocket to unowned project rejected
# Attempt WebSocket connection to another user's project:
# Expected: Connection closed with code 4403 before any data

# Check 6: Constant-time comparisons (code review)
grep -n "!=" backend/src/api/signal.py | grep -i "secret"
# Expected: No results (all comparisons use hmac.compare_digest)

# Check 7: Security headers present
curl -sI http://localhost:5173/ | grep -iE "content-security-policy|strict-transport|referrer-policy|permissions-policy|server:"
# Expected output includes:
#   Content-Security-Policy: default-src 'self'; ...
#   Strict-Transport-Security: max-age=31536000; includeSubDomains
#   Referrer-Policy: strict-origin-when-cross-origin
#   Permissions-Policy: camera=(), microphone=(), geolocation=()
#   Server: nginx  (no version number)

# Verify deprecated header removed:
curl -sI http://localhost:5173/ | grep -i "x-xss-protection"
# Expected: No results
```

### Phase 3 — Medium Verification

```bash
# Check 8: Rate limiting returns 429
# Send requests above rate limit:
for i in $(seq 1 15); do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -H "Cookie: session_id=<valid_session>" \
    -X POST http://localhost:8000/api/v1/chat/send \
    -d '{"message": "test"}'
done
# Expected: First 10 return 200, remaining return 429

# Check 9: localStorage cleared on logout
# In browser devtools after logout:
# localStorage.getItem('chat-message-history')  → null

# Check 10: Database directory permissions
docker exec ghchat-backend stat -c "%a" /var/lib/ghchat/data
# Expected: 700
docker exec ghchat-backend stat -c "%a" /var/lib/ghchat/data/settings.db
# Expected: 600
```

### Phase 4 — Low Verification

```bash
# Check: GitHub Actions permissions have comments
grep -A2 "issues: write" .github/workflows/branch-issue-link.yml
# Expected: Comment explaining why write permission is needed

# Check: Avatar URL validation
# In browser devtools, verify avatar images only load from https://avatars.githubusercontent.com
# Any non-GitHub avatar URL should show a placeholder
```

### Full Stack Verification

```bash
# Build and start all containers
docker compose build
docker compose up -d
sleep 15

# Verify health
curl -s http://localhost:8000/api/v1/health | grep -q ok && echo "Backend healthy"
curl -s http://localhost:5173/health | grep -q OK && echo "Frontend healthy"

# Verify non-root containers
docker exec ghchat-frontend id | grep -v "uid=0" && echo "Frontend non-root OK"
docker exec ghchat-backend id | grep -v "uid=0" && echo "Backend non-root OK"

# Verify security headers
curl -sI http://localhost:5173/ | head -20

# Verify port binding (localhost only)
ss -tlnp | grep -E "8000|5173"
# Expected: 127.0.0.1:8000 and 127.0.0.1:5173 (not 0.0.0.0)

# Cleanup
docker compose down
```

### Backend Unit Test Regression

```bash
cd backend
source .venv/bin/activate

# Run existing tests to verify no regressions
# Note: Tests should be run in batches due to known timeout with full suite
ls tests/unit/*.py | head -24 | xargs pytest -x -q
ls tests/unit/*.py | tail -n +25 | xargs pytest -x -q
```

### Frontend Test Regression

```bash
cd frontend

# Type check
npx tsc --noEmit

# Lint
npm run lint

# Unit tests
npm run test

# Production build
npm run build
```
