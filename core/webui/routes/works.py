"""
API Routes para Works (Archivos/Trabajos generados por skills)
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from typing import Dict, List, Optional, Any
from core.file_manager import works_manager, CATEGORY_NAMES
from core.webui.decorators import handle_route_errors

router = APIRouter(prefix="/api/works", tags=["works"])


@router.get("/categories")
@handle_route_errors("MININA.WebUI.Works")
async def get_categories() -> Dict[str, Any]:
    """Obtener todas las categorías de trabajos"""
    categories = works_manager.get_all_categories()
    return {
        "success": True,
        "categories": categories
    }


@router.get("/list")
@handle_route_errors("MININA.WebUI.Works")
async def list_works(
    category: Optional[str] = Query(None, description="Filtrar por categoría"),
    skill_id: Optional[str] = Query(None, description="Filtrar por skill"),
    limit: int = Query(1000, description="Límite de resultados")
) -> Dict[str, Any]:
    """Listar trabajos con filtros opcionales"""
    if skill_id:
        works = [w.to_dict() for w in works_manager.get_works_by_skill(skill_id)]
    elif category:
        works = works_manager.get_all_works(category=category, limit=limit)
    else:
        works = works_manager.get_all_works(limit=limit)
    
    return {
        "success": True,
        "works": works,
        "count": len(works),
        "category": category,
        "skill_id": skill_id
    }


@router.get("/{work_id}")
@handle_route_errors("MININA.WebUI.Works")
async def get_work(work_id: str) -> Dict[str, Any]:
    """Obtener detalles de un trabajo específico"""
    work = works_manager.get_work(work_id)
    if not work:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    
    return {
        "success": True,
        "work": work.to_dict()
    }


@router.get("/{work_id}/download")
@handle_route_errors("MININA.WebUI.Works")
async def download_work(work_id: str):
    """Descargar un archivo de trabajo"""
    try:
        file_path = works_manager.get_file_path(work_id)
        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
        
        work = works_manager.get_work(work_id)
        if not work:
            raise HTTPException(status_code=404, detail="Trabajo no encontrado en el índice")
        
        return FileResponse(
            path=str(file_path),
            filename=work.original_name,
            media_type="application/octet-stream"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en download_work: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.delete("/{work_id}")
@handle_route_errors("MININA.WebUI.Works")
async def delete_work(work_id: str) -> Dict[str, Any]:
    """Eliminar un trabajo"""
    success = works_manager.delete_work(work_id)
    if not success:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    
    return {
        "success": True,
        "message": "Trabajo eliminado correctamente"
    }


@router.get("/stats/overview")
@handle_route_errors("MININA.WebUI.Works")
async def get_stats() -> Dict[str, Any]:
    """Obtener estadísticas de trabajos"""
    categories = works_manager.get_all_categories()
    total_works = len(works_manager.works)
    total_size = sum(cat["total_size"] for cat in categories)
    
    # Trabajos recientes (últimos 10)
    recent = works_manager.get_all_works(limit=10)
    
    return {
        "success": True,
        "total_works": total_works,
        "total_size": total_size,
        "categories": categories,
        "recent_works": recent
    }
