"""Guard models for admin/adminlock file protection."""

from pydantic import BaseModel


class GuardResult(BaseModel):
    """Result of evaluating file paths against guard rules."""

    allowed: list[str] = []
    admin_blocked: list[str] = []
    locked: list[str] = []
