# Developer Quick Start: Profile Picture Upload

**Feature**: Profile Picture Upload  
**Last Updated**: 2026-02-13  
**Estimated Setup Time**: 10 minutes

## Overview

This guide helps developers quickly set up their environment to work on the profile picture upload feature. Follow these steps to get the feature running locally and start contributing.

---

## Prerequisites

Before starting, ensure you have:

- ✅ Repository cloned: `github-workflows`
- ✅ Docker and Docker Compose installed (recommended) OR:
  - Node.js 18+ (for frontend)
  - Python 3.11+ (for backend)
- ✅ GitHub OAuth credentials configured (see main README.md)
- ✅ Base application running successfully (can authenticate and view projects)

---

## Quick Setup (5 minutes)

### 1. Create Storage Directory

The profile picture feature requires a storage directory for uploaded images:

```bash
# From repository root
mkdir -p backend/storage/profile-pictures
chmod 755 backend/storage/profile-pictures
```

### 2. Update Environment Configuration

Add the storage path to your `.env` file (optional, defaults to `./storage`):

```bash
# Add to .env
STORAGE_PATH=./storage
```

### 3. Add .gitignore Entry

Ensure uploaded profile pictures are not committed to git:

```bash
# Add to .gitignore (if not already present)
echo "backend/storage/" >> .gitignore
```

### 4. Install Python Dependencies

The feature requires Pillow for image processing:

```bash
cd backend
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install Pillow>=10.0.0
```

### 5. Update Docker Volume (if using Docker)

Add volume mount to `docker-compose.yml`:

```yaml
services:
  backend:
    volumes:
      - ./backend:/app
      - ./storage:/app/storage  # Add this line
```

### 6. Restart Services

```bash
# If using Docker
docker compose down
docker compose up -d

# If running locally
# Terminal 1: Backend
cd backend && uvicorn src.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```

---

## Verify Setup

### Test Storage Directory

```bash
# Check storage directory exists and is writable
touch backend/storage/profile-pictures/test.txt
rm backend/storage/profile-pictures/test.txt
echo "✅ Storage directory is ready"
```

### Test Pillow Installation

```bash
cd backend
source .venv/bin/activate
python -c "from PIL import Image; print('✅ Pillow installed:', Image.__version__)"
```

### Test Base Application

1. Navigate to http://localhost:5173
2. Login with GitHub OAuth
3. Select a project
4. Verify chat interface loads correctly

If all tests pass, you're ready to start development! 🎉

---

## Development Workflow

### Backend Development

**Location**: `backend/src/`

**Key Files to Create**:
- `api/profile.py` - Profile picture API endpoints
- `services/file_storage.py` - File storage service
- `models/user.py` - Extend UserSession model

**Running Tests**:
```bash
cd backend
source .venv/bin/activate
pytest tests/unit/test_profile.py -v
```

**API Documentation**:
- Start backend with `DEBUG=true`
- Visit http://localhost:8000/api/docs
- Interactive API documentation with Swagger UI

### Frontend Development

**Location**: `frontend/src/`

**Key Files to Create**:
- `components/profile/ProfilePictureUpload.tsx`
- `components/profile/ProfilePicturePreview.tsx`
- `hooks/useProfilePicture.ts`
- `types/user.ts` - Extend user types

**Running Tests**:
```bash
cd frontend
npm test                  # Unit tests with vitest
npm run test:watch        # Watch mode
npm run test:e2e          # E2E tests with Playwright
```

**Hot Reload**:
- Frontend: Changes auto-reload in browser
- Backend: uvicorn --reload handles auto-restart

---

## Common Development Tasks

### Test File Upload Locally

```bash
# Create a test image
convert -size 100x100 xc:blue backend/storage/test.jpg

# Or download a sample
curl -o backend/storage/test.jpg https://via.placeholder.com/150
```

### Clear Storage Directory

```bash
rm -rf backend/storage/profile-pictures/*
echo "✅ Storage cleared"
```

### Check Storage Size

```bash
du -sh backend/storage/profile-pictures/
```

### Manually Test API Endpoints

**Upload a profile picture**:
```bash
curl -X POST http://localhost:8000/api/v1/profile/picture \
  -H "Cookie: session_id=YOUR_SESSION_ID" \
  -F "file=@/path/to/image.jpg"
```

**Get profile info**:
```bash
curl http://localhost:8000/api/v1/profile/picture \
  -H "Cookie: session_id=YOUR_SESSION_ID"
```

**Remove profile picture**:
```bash
curl -X DELETE http://localhost:8000/api/v1/profile/picture \
  -H "Cookie: session_id=YOUR_SESSION_ID"
```

---

## Project Structure

```
backend/
├── src/
│   ├── api/
│   │   └── profile.py              # NEW: Profile endpoints
│   ├── services/
│   │   └── file_storage.py         # NEW: Storage service
│   ├── models/
│   │   └── user.py                 # MODIFIED: Add profile_picture_url
│   └── main.py                     # MODIFIED: Register profile router
├── storage/                        # NEW: Storage directory
│   └── profile-pictures/           # NEW: Profile pictures
└── tests/
    └── unit/
        └── test_profile.py         # NEW: Profile tests

frontend/
├── src/
│   ├── components/
│   │   └── profile/                # NEW: Profile components
│   │       ├── ProfilePictureUpload.tsx
│   │       ├── ProfilePicturePreview.tsx
│   │       └── ProfileAvatar.tsx
│   ├── hooks/
│   │   └── useProfilePicture.ts    # NEW: Profile hook
│   └── types/
│       └── user.ts                 # MODIFIED: Add profile types
└── tests/
    └── unit/
        └── useProfilePicture.test.tsx  # NEW: Hook tests
```

---

## Troubleshooting

### "Permission denied" when uploading files

**Solution**: Check storage directory permissions
```bash
chmod 755 backend/storage/profile-pictures
```

### "Module 'PIL' has no attribute 'Image'"

**Solution**: Reinstall Pillow
```bash
pip uninstall Pillow
pip install Pillow>=10.0.0
```

### "404 Not Found" when accessing uploaded images

**Solution**: Ensure static file serving is configured in FastAPI
- Check `app.mount("/storage", ...)` in main.py
- Verify file exists: `ls backend/storage/profile-pictures/`

### Docker container can't write to storage

**Solution**: Fix volume mount permissions
```bash
# On host
mkdir -p storage/profile-pictures
chmod -R 777 storage  # Development only, use proper permissions in production
```

### Frontend can't upload files

**Solution**: Check CORS configuration
- Ensure `CORS_ORIGINS` includes frontend URL (http://localhost:5173)
- Verify `multipart/form-data` content type is not blocked

---

## Testing Strategy

### Backend Tests (pytest)

**Unit Tests**: Test individual components in isolation
```bash
cd backend
pytest tests/unit/test_file_storage.py -v     # Storage service
pytest tests/unit/test_profile_api.py -v      # API endpoints
pytest tests/unit/test_validators.py -v       # File validation
```

**Integration Tests**: Test full upload flow
```bash
pytest tests/integration/test_profile_flow.py -v
```

**Test Coverage**:
```bash
pytest --cov=src/services/file_storage --cov-report=html
```

### Frontend Tests (vitest + Playwright)

**Unit Tests**: Test React components and hooks
```bash
cd frontend
npm test -- hooks/useProfilePicture.test.tsx
npm test -- components/profile/
```

**E2E Tests**: Test user flows
```bash
npm run test:e2e -- profile-upload.spec.ts
npm run test:e2e:headed  # With visible browser
```

---

## Code Review Checklist

Before submitting your PR, ensure:

- [ ] Storage directory is in .gitignore
- [ ] Pillow is added to backend dependencies
- [ ] All tests pass (backend + frontend)
- [ ] API endpoints follow OpenAPI spec (contracts/openapi.yaml)
- [ ] Error handling covers all edge cases
- [ ] File validation prevents security issues
- [ ] UI components match existing design patterns
- [ ] Documentation is updated (if needed)

---

## Resources

**Design Documents**:
- [Specification](./spec.md) - User stories and requirements
- [Data Model](./data-model.md) - Entity definitions
- [API Contract](./contracts/openapi.yaml) - OpenAPI specification
- [Research](./research.md) - Technical decisions

**External Documentation**:
- [FastAPI File Uploads](https://fastapi.tiangolo.com/tutorial/request-files/)
- [Pillow Documentation](https://pillow.readthedocs.io/)
- [React File Upload](https://developer.mozilla.org/en-US/docs/Web/API/File)
- [TanStack Query](https://tanstack.com/query/latest)

**Need Help?**
- Check existing issues for similar problems
- Review test files for usage examples
- Ask in team chat or create a discussion

---

## Next Steps

1. ✅ Complete setup above
2. 📖 Read [spec.md](./spec.md) for requirements
3. 📋 Check [data-model.md](./data-model.md) for entity definitions
4. 🔌 Review [contracts/openapi.yaml](./contracts/openapi.yaml) for API design
5. 🏗️ Start implementing user stories (P1 → P2 → P3)
6. ✅ Write tests as you go (TDD recommended)
7. 🚀 Submit PR when P1 is complete

Happy coding! 🎨
