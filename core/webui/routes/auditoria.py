"""
API Routes para Auditoría General
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any
from core.auditoria import auditoria_manager
from core.webui.decorators import handle_route_errors

router = APIRouter(prefix="/api/auditoria", tags=["auditoria"])


@router.get("/registros")
@handle_route_errors("MININA.WebUI.Auditoria")
async def get_registros(
    skill_id: Optional[str] = Query(None, description="Filtrar por skill"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    fecha_desde: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    limit: int = Query(1000, description="Límite de resultados")
) -> Dict[str, Any]:
    """Obtener registros de auditoría con filtros"""
    registros = auditoria_manager.obtener_registros(
        skill_id=skill_id,
        status=status,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        limit=limit
    )
    
    return {
        "success": True,
        "registros": registros,
        "count": len(registros),
        "retention_days": 30,
        "filters": {
            "skill_id": skill_id,
            "status": status,
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta
        }
    }


@router.get("/estadisticas")
@handle_route_errors("MININA.WebUI.Auditoria")
async def get_estadisticas() -> Dict[str, Any]:
    """Obtener estadísticas de auditoría"""
    stats = auditoria_manager.obtener_estadisticas()
    
    return {
        "success": True,
        "estadisticas": stats
    }


@router.get("/skill/{skill_id}")
@handle_route_errors("MININA.WebUI.Auditoria")
async def get_registros_skill(skill_id: str) -> Dict[str, Any]:
    """Obtener registros de auditoría para una skill específica"""
    registros = auditoria_manager.obtener_registros(skill_id=skill_id)
    
    return {
        "success": True,
        "skill_id": skill_id,
        "registros": registros,
        "count": len(registros)
    }


@router.get("/registro/{registro_id}")
@handle_route_errors("MININA.WebUI.Auditoria")
async def get_registro_detail(registro_id: str) -> Dict[str, Any]:
    """Obtener detalle de un registro específico"""
    for reg in auditoria_manager.registros:
        if reg.id == registro_id:
            return {
                "success": True,
                "registro": reg.to_dict()
            }
    
    raise HTTPException(status_code=404, detail="Registro no encontrado")
