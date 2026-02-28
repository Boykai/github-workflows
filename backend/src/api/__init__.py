"""API routes for the application."""

from fastapi import APIRouter

from src.api.auth import router as auth_router
from src.api.board import router as board_router
from src.api.chat import router as chat_router
from src.api.health import router as health_router
from src.api.mcp import router as mcp_router
from src.api.projects import router as projects_router
from src.api.settings import router as settings_router
from src.api.signal import router as signal_router
from src.api.tasks import router as tasks_router
from src.api.webhooks import router as webhooks_router
from src.api.workflow import router as workflow_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(projects_router, prefix="/projects", tags=["projects"])
router.include_router(board_router, prefix="/board", tags=["board"])
router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
router.include_router(chat_router, prefix="/chat", tags=["chat"])
router.include_router(workflow_router, tags=["workflow"])
router.include_router(settings_router, prefix="/settings", tags=["settings"])
router.include_router(mcp_router, prefix="/settings", tags=["mcp"])
router.include_router(signal_router, prefix="/signal", tags=["signal"])
router.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])
router.include_router(health_router, tags=["health"])
