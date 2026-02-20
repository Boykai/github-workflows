"""
Shared dependency imports for copilot_polling sub-modules.

All sub-modules import shared services from this module so that tests
can patch them in a single location:
    @patch("src.services.copilot_polling._deps.github_projects_service")
"""

from src.services.github_projects import github_projects_service
from src.services.websocket import connection_manager
