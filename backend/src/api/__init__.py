"""API routes for the application."""

from fastapi import APIRouter

from src.api.auth import router as auth_router
from src.api.projects import router as projects_router
from src.api.tasks import router as tasks_router
from src.api.chat import router as chat_router
from src.api.workflow import router as workflow_router
from src.api.webhooks import router as webhooks_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(projects_router, prefix="/projects", tags=["projects"])
router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
router.include_router(chat_router, prefix="/chat", tags=["chat"])
router.include_router(workflow_router, tags=["workflow"])
router.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])


@router.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint for Docker and load balancers."""
    return {"status": "healthy"}
