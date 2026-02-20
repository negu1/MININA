"""
WebUI Dependencies Injection
============================
Inyección de dependencias para los routers.
"""
from fastapi import Request
from .state import StateManager, get_state_manager


def get_state_from_request(request: Request) -> StateManager:
    """Get state manager from request app state."""
    return request.app.state.manager
