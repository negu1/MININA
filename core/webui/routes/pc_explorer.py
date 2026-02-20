"""
PC Explorer Router
==================
Endpoints para exploración de archivos del PC.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from pathlib import Path

from core.logging_config import get_logger
from core.webui.decorators import handle_route_errors
from core.config import get_settings

logger = get_logger("MININA.WebUI.PC")
router = APIRouter()


def _get_allowed_roots() -> List[Path]:
    """Get list of allowed root directories for browsing."""
    settings = get_settings()
    return [
        Path.home(),
        settings.DATA_DIR.resolve(),
        settings.SKILLS_DIR.resolve(),
        settings.OUTPUT_DIR.resolve(),
    ]


def _validate_path(path_str: str) -> Path:
    """
    Validate and sanitize a path.
    
    Prevents path traversal attacks by ensuring the resolved path
    is within allowed directories.
    """
    if not path_str:
        return Path.home()
    
    target = Path(path_str).resolve()
    allowed_roots = _get_allowed_roots()
    
    for allowed in allowed_roots:
        try:
            target.relative_to(allowed)
            if target.exists():
                return target
            else:
                raise HTTPException(status_code=404, detail=f"Path not found: {path_str}")
        except ValueError:
            continue
    
    logger.warning(f"Path access denied: {path_str}", extra={"path": path_str})
    raise HTTPException(
        status_code=403,
        detail=f"Access denied: {path_str}. Path is outside allowed directories."
    )


@router.get("/list")
@handle_route_errors("MININA.WebUI.PC")
async def list_directory(path: str = "") -> Dict[str, Any]:
    """List directory contents."""
    target_path = _validate_path(path) if path else Path.home()
    
    items = []
    try:
        for item in target_path.iterdir():
            try:
                stat = item.stat()
                items.append({
                    "name": item.name,
                    "path": str(item),
                    "is_dir": item.is_dir(),
                    "size": stat.st_size if item.is_file() else 0,
                    "modified": stat.st_mtime
                })
            except (OSError, PermissionError):
                continue
    except PermissionError:
        raise HTTPException(status_code=403, detail=f"Permission denied: {path}")
    
    return {
        "success": True,
        "path": str(target_path),
        "items": items,
        "count": len(items)
    }


@router.get("/search")
@handle_route_errors("MININA.WebUI.PC")
async def search_files(query: str, path: str = "") -> Dict[str, Any]:
    """Search files by name within allowed directories."""
    if not query or len(query) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")
    
    search_path = _validate_path(path) if path else Path.home()
    
    results = []
    count = 0
    max_results = 100
    
    try:
        for item in search_path.rglob(f"*{query}*"):
            if count >= max_results:
                break
            
            try:
                _validate_path(str(item))
                results.append({
                    "name": item.name,
                    "path": str(item),
                    "is_dir": item.is_dir()
                })
                count += 1
            except HTTPException:
                continue
            except (OSError, PermissionError):
                continue
    except PermissionError:
        raise HTTPException(status_code=403, detail=f"Permission denied searching: {path}")
    
    return {
        "success": True,
        "query": query,
        "path": str(search_path),
        "results": results,
        "count": len(results),
        "truncated": count >= max_results
    }
