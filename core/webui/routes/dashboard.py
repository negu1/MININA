"""
Dashboard Router
================
Endpoints para el panel principal.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import Dict, Any
from pathlib import Path

from core.logging_config import get_logger
from core.CortexBus import bus
from core.webui.decorators import handle_route_errors
from core.AgentLifecycleManager import agent_manager
from core.LLMManager import LLMManager

logger = get_logger("MININA.WebUI.Dashboard")
router = APIRouter()
llm_manager = LLMManager()


@router.get("/")
async def dashboard_index():
    """Serve dashboard HTML."""
    index_file = Path(__file__).parent.parent / "static" / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "MININA Dashboard - Use /api/docs for API documentation"}


@router.get("/api/dashboard/stats")
@handle_route_errors("MININA.WebUI.Dashboard")
async def get_dashboard_stats() -> Dict[str, Any]:
    """Get dashboard statistics with real data."""
    skills = agent_manager.list_available_skills()
    active = agent_manager.active_agents
    
    # Determinar estado del LLM
    llm_status = "disconnected"
    if llm_manager.active_provider:
        llm_status = llm_manager.active_provider.value
    
    return {
        "success": True,
        "stats": {
            "system_status": "online",
            "skills_count": len(skills),
            "skills_names": skills[:10],  # Primeras 10 skills
            "active_agents": len(active),
            "running_skills": [
                {"name": info.skill_name, "pid": info.pid}
                for pid, info in list(active.items())[:5]  # Max 5
            ],
            "llm_status": llm_status,
            "llm_provider": llm_manager.active_provider.value if llm_manager.active_provider else None,
        }
    }


@router.post("/api/dashboard/action")
@handle_route_errors("MININA.WebUI.Dashboard")
async def dashboard_action(action: Dict[str, Any]):
    """Handle dashboard action."""
    action_type = action.get("type")
    logger.info(f"Dashboard action: {action_type}", extra={"action_type": action_type})
    
    # Broadcast action via CortexBus
    await bus.publish("ui.ACTION", action, sender="WebUI")
    
    return {"success": True, "action": action_type}
