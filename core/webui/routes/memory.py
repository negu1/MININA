"""
Memory Router
=============
Endpoints para gestión del sistema de memoria MININA.
Permite consultar, almacenar y gestionar memoria STM, MTM y LTM.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional

from core.logging_config import get_logger
from core.MemoryCore import memory_core
from core.webui.decorators import handle_route_errors

logger = get_logger("MININA.WebUI.Memory")
router = APIRouter()


@router.get("/stats")
@handle_route_errors("MININA.WebUI.Memory")
async def get_memory_stats() -> Dict[str, Any]:
    """Get memory system statistics."""
    stats = memory_core.get_stats()
    return {
        "success": True,
        "stats": stats
    }


@router.get("/stm/{session_id}")
@handle_route_errors("MININA.WebUI.Memory")
async def get_stm_context(session_id: str, limit: int = 10) -> Dict[str, Any]:
    """Get Short-Term Memory context for a session."""
    context = memory_core.get_stm_context(session_id, limit)
    return {
        "success": True,
        "session_id": session_id,
        "context": context,
        "count": len(context)
    }


@router.get("/mtm/{session_id}")
@handle_route_errors("MININA.WebUI.Memory")
async def get_mtm_context(session_id: str, limit: int = 20) -> Dict[str, Any]:
    """Get Medium-Term Memory context for a session."""
    context = memory_core.get_mtm_context(session_id, limit)
    return {
        "success": True,
        "session_id": session_id,
        "context": context,
        "count": len(context)
    }


@router.post("/stm/add")
@handle_route_errors("MININA.WebUI.Memory")
async def add_to_stm(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add interaction to Short-Term Memory.
    
    Body:
        session_id: Session identifier
        role: 'user', 'assistant', or 'system'
        content: Message content
        metadata: Optional metadata
    """
    session_id = data.get("session_id")
    role = data.get("role")
    content = data.get("content")
    metadata = data.get("metadata", {})
    
    if not all([session_id, role, content]):
        raise HTTPException(
            status_code=400,
            detail="session_id, role, and content are required"
        )
    
    if role not in ["user", "assistant", "system"]:
        raise HTTPException(status_code=400, detail="role must be 'user', 'assistant', or 'system'")
    
    memory_core.add_to_stm(session_id, role, content, metadata)
    
    return {
        "success": True,
        "message": f"Added to STM for session {session_id}"
    }


@router.post("/ltm/search")
@handle_route_errors("MININA.WebUI.Memory")
async def search_ltm(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search Long-Term Memory.
    
    Body:
        query: Search query
        category: Optional category filter
        limit: Maximum results (default 5)
    """
    query = data.get("query")
    category = data.get("category")
    limit = data.get("limit", 5)
    
    if not query:
        raise HTTPException(status_code=400, detail="query is required")
    
    results = memory_core.search_ltm(query, category, limit)
    
    return {
        "success": True,
        "query": query,
        "results": results,
        "count": len(results)
    }


@router.post("/ltm/store")
@handle_route_errors("MININA.WebUI.Memory")
async def store_in_ltm(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Store knowledge in Long-Term Memory.
    
    Body:
        content: Content to store
        category: Category (default 'general')
        source: Source of knowledge
        confidence: Confidence score (0.0-1.0)
        metadata: Optional metadata
    """
    content = data.get("content")
    if not content:
        raise HTTPException(status_code=400, detail="content is required")
    
    result = memory_core.store_in_ltm(
        content=content,
        category=data.get("category", "general"),
        source=data.get("source", "api"),
        confidence=data.get("confidence", 0.5),
        metadata=data.get("metadata", {})
    )
    
    return result


@router.post("/facts/store")
@handle_route_errors("MININA.WebUI.Memory")
async def store_fact(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Store a structured fact (triple).
    
    Body:
        subject: Subject of the fact
        predicate: Relationship
        object: Object/value
        confidence: Confidence (0.0-1.0)
    """
    subject = data.get("subject")
    predicate = data.get("predicate")
    object_ = data.get("object")
    
    if not all([subject, predicate, object_]):
        raise HTTPException(
            status_code=400,
            detail="subject, predicate, and object are required"
        )
    
    success = memory_core.store_fact(
        subject=subject,
        predicate=predicate,
        object_=object_,
        confidence=data.get("confidence", 1.0)
    )
    
    return {
        "success": success,
        "fact": {"subject": subject, "predicate": predicate, "object": object_}
    }


@router.post("/facts/query")
@handle_route_errors("MININA.WebUI.Memory")
async def query_facts(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Query structured facts.
    
    Body:
        subject: Optional subject filter
        predicate: Optional predicate filter
        object: Optional object filter
    """
    results = memory_core.query_facts(
        subject=data.get("subject"),
        predicate=data.get("predicate"),
        object_=data.get("object")
    )
    
    return {
        "success": True,
        "results": results,
        "count": len(results)
    }


@router.get("/quarantine")
@handle_route_errors("MININA.WebUI.Memory")
async def get_quarantine() -> Dict[str, Any]:
    """Get quarantined content."""
    quarantine = memory_core.get_quarantine()
    return {
        "success": True,
        "quarantine": quarantine,
        "count": len(quarantine)
    }


@router.post("/quarantine/release")
@handle_route_errors("MININA.WebUI.Memory")
async def release_from_quarantine(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Release content from quarantine to LTM.
    
    Body:
        entry_id: ID of quarantined entry to release
    """
    entry_id = data.get("entry_id")
    if not entry_id:
        raise HTTPException(status_code=400, detail="entry_id is required")
    
    success = memory_core.release_from_quarantine(entry_id)
    
    return {
        "success": success,
        "message": "Released from quarantine" if success else "Failed to release"
    }


@router.post("/session/consolidate")
@handle_route_errors("MININA.WebUI.Memory")
async def consolidate_session(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Consolidate a session from STM to LTM.
    
    Body:
        session_id: Session to consolidate
    """
    session_id = data.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    
    memory_core.consolidate_session(session_id)
    
    return {
        "success": True,
        "message": f"Session {session_id} consolidated to LTM"
    }


@router.post("/session/clear")
@handle_route_errors("MININA.WebUI.Memory")
async def clear_session(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clear a session from STM (consolidates to MTM first).
    
    Body:
        session_id: Session to clear
    """
    session_id = data.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    
    memory_core.clear_session(session_id)
    
    return {
        "success": True,
        "message": f"Session {session_id} cleared"
    }


@router.post("/backup")
@handle_route_errors("MININA.WebUI.Memory")
async def backup_memory() -> Dict[str, Any]:
    """Create memory backup."""
    result = memory_core.backup_memory()
    return result


@router.post("/maintenance/cleanup")
@handle_route_errors("MININA.WebUI.Memory")
async def cleanup_memory() -> Dict[str, Any]:
    """Run memory maintenance (cleanup expired MTM)."""
    memory_core.cleanup_expired_mtm()
    return {
        "success": True,
        "message": "Memory maintenance completed"
    }


@router.get("/context/{session_id}")
@handle_route_errors("MININA.WebUI.Memory")
async def get_full_context(session_id: str) -> Dict[str, Any]:
    """
    Get full context for a session (STM + MTM + relevant LTM).
    
    Returns combined context from all memory tiers.
    """
    stm = memory_core.get_stm_context(session_id, limit=10)
    mtm = memory_core.get_mtm_context(session_id, limit=20)
    
    # Buscar conocimiento relevante en LTM basado en contenido reciente
    ltm_results = []
    for interaction in stm[-3:]:  # Últimas 3 interacciones
        results = memory_core.search_ltm(interaction['content'], limit=2)
        ltm_results.extend(results)
    
    return {
        "success": True,
        "session_id": session_id,
        "context": {
            "stm": {
                "interactions": stm,
                "count": len(stm)
            },
            "mtm": {
                "interactions": mtm,
                "count": len(mtm)
            },
            "ltm_relevant": {
                "entries": ltm_results,
                "count": len(ltm_results)
            }
        }
    }
