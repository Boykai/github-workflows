# Quickstart: Security, Privacy & Vulnerability Audit

**Feature Branch**: `025-security-review`

## Verification Commands

After implementing all security changes, run these commands to verify each finding is remediated. These correspond to the 10 behavior-based verification checks in the audit.

### Check 1: No Credentials in URLs

```bash
# Start the application and complete an OAuth login flow
# Then inspect browser history and network logs

# Automated: Check that the OAuth callback redirect has no query parameters
curl -sI "http://localhost:8000/api/v1/auth/github/callback?code=test&state=test" \
  | grep -i "location"
# Expected: Location header points to frontend with NO session_token parameter
# e.g., Location: http://localhost:5173/auth/callback (no ?session_token=...)
```

### Check 2: Startup Refuses Without Mandatory Secrets

```bash
cd backend

# Test: Missing ENCRYPTION_KEY in non-debug mode
DEBUG=false ENCRYPTION_KEY="" SESSION_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))") \
  python -c "from src.config import Settings; Settings()" 2>&1
# Expected: ValueError mentioning ENCRYPTION_KEY required

# Test: Missing GITHUB_WEBHOOK_SECRET in non-debug mode  
DEBUG=false ENCRYPTION_KEY="test-key-for-validation" GITHUB_WEBHOOK_SECRET="" \
  SESSION_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))") \
  python -c "from src.config import Settings; Settings()" 2>&1
# Expected: ValueError mentioning GITHUB_WEBHOOK_SECRET required

# Test: Short SESSION_SECRET_KEY
SESSION_SECRET_KEY="too-short" \
  python -c "from src.config import Settings; Settings()" 2>&1
# Expected: ValueError mentioning minimum 64 characters
```

### Check 3: Frontend Container Non-Root

```bash
# Build and start containers
docker compose up -d frontend

# Verify non-root user
docker exec $(docker compose ps -q frontend) id
# Expected: uid=101(nginx) gid=101(nginx) — NOT uid=0(root)

# Verify nginx still serves correctly
curl -s http://localhost:5173/ | head -5
# Expected: Valid HTML response
```

### Check 4: Unowned Project Returns 403

```bash
# Authenticate as User A and get their session cookie
# Then attempt to access User B's project

curl -s -b "session_token=USER_A_TOKEN" \
  "http://localhost:8000/api/v1/tasks?project_id=USER_B_PROJECT_ID"
# Expected: HTTP 403 Forbidden
```

### Check 5: WebSocket Rejection for Unowned Project

```bash
# Attempt WebSocket connection with User A's session to User B's project
# Use wscat or similar tool
# Expected: Connection rejected before any data is sent
```

### Check 6: Constant-Time Secret Comparisons (Code Review)

```bash
cd backend

# Search for all secret/token comparisons
grep -rn "webhook_secret\|signal.*secret\|compare_digest" src/
# Expected: ALL comparisons use hmac.compare_digest, NONE use == or !=

# Specifically check signal.py
grep -n "compare_digest" src/api/signal.py
# Expected: At least one match showing hmac.compare_digest usage
```

### Check 7: Security Headers Present

```bash
# Send HEAD request to frontend
curl -sI http://localhost:5173/ | grep -iE "content-security|strict-transport|referrer-policy|permissions-policy|server:|x-xss"
# Expected output includes:
#   Content-Security-Policy: default-src 'self'; ...
#   Strict-Transport-Security: max-age=31536000; includeSubDomains
#   Referrer-Policy: strict-origin-when-cross-origin
#   Permissions-Policy: camera=(), microphone=(), geolocation=()
# Expected ABSENT:
#   X-XSS-Protection (removed)
#   Server: nginx/1.x.x (version hidden by server_tokens off)
```

### Check 8: Rate Limiting Returns 429

```bash
# Send rapid requests to a rate-limited endpoint
for i in $(seq 1 35); do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -b "session_token=VALID_TOKEN" \
    -X POST "http://localhost:8000/api/v1/chat/message" \
    -H "Content-Type: application/json" \
    -d '{"message": "test"}'
done
# Expected: First ~30 return 200, then 429 Too Many Requests
```

### Check 9: localStorage Cleared After Logout

```bash
# In browser devtools after login and sending messages:
# Console: localStorage.getItem('chat-message-history')
# Expected: Contains only message ID references, not full content

# After logout:
# Console: localStorage.getItem('chat-message-history')
# Expected: null (cleared on logout)
```

### Check 10: Database Permissions

```bash
# Check directory permissions
docker exec $(docker compose ps -q backend) stat -c '%a %n' /var/lib/ghchat/data
# Expected: 700 /var/lib/ghchat/data

# Check file permissions
docker exec $(docker compose ps -q backend) stat -c '%a %n' /var/lib/ghchat/data/*.db
# Expected: 600 /var/lib/ghchat/data/ghchat.db
```

### Additional Verification

```bash
# Verify OAuth scopes (inspect authorization URL)
curl -s "http://localhost:8000/api/v1/auth/github/authorize" | grep -o "scope=[^&]*"
# Expected: scope=read:user+read:org+project (no 'repo')

# Verify dev-login is POST-only (not GET)
curl -s -X GET "http://localhost:8000/api/v1/auth/dev-login?github_token=test"
# Expected: 405 Method Not Allowed (or 404 in production)

# Verify webhook signature always required
curl -s -X POST "http://localhost:8000/api/v1/webhooks/github" \
  -H "Content-Type: application/json" -d '{}' 
# Expected: 401 or 503 (not 200, even in debug mode)

# Verify malformed CORS origins rejected
CORS_ORIGINS="not-a-url" python -c "from src.config import Settings; Settings()" 2>&1
# Expected: ValueError mentioning malformed CORS origin

# Verify API docs controlled by ENABLE_DOCS
DEBUG=true ENABLE_DOCS=false python -c "..." 
curl -s http://localhost:8000/api/docs
# Expected: 404 (docs disabled even though debug is on)
```

### Backend Test Suite (Regression Gate)

```bash
cd backend

# Lint
ruff check src/
ruff format --check src/

# Type check
pyright src/

# Run tests (batched to avoid timeout)
ls tests/unit/*.py | head -24 | xargs pytest
ls tests/unit/*.py | tail -24 | xargs pytest
```

### Frontend Test Suite (Regression Gate)

```bash
cd frontend

# Lint
npx eslint .

# Type check
npx tsc --noEmit

# Unit tests
npx vitest run

# Build
npm run build
```
