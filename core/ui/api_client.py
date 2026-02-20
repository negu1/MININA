"""
MININA v3.0 - API Client (Standalone)
=====================================
Cliente directo para UI Local - conecta directamente con managers
sin pasar por HTTP/FastAPI. UI Local ahora es completamente standalone.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import json
import asyncio

from core.logging_config import get_logger
from core.SkillVault import vault
from core.file_manager import works_manager
from core.AgentLifecycleManager import agent_manager
from core.MemoryCore import memory_core
from core.LLMManager import llm_manager
from core.SystemWatchdog import watchdog
from core.config import get_settings

logger = get_logger("MININA.UI.Client")


class MININAApiClient:
    """
    Cliente directo para UI Local.
    Conecta directamente con los managers del core sin HTTP.
    """
    
    def __init__(self, base_url: str = None):
        # base_url se mantiene por compatibilidad pero no se usa
        self.base_url = base_url or "local"
        logger.info("UI Local Client inicializado (modo standalone)")
        
    def health_check(self) -> bool:
        """Verificar si el sistema está activo"""
        try:
            # Verificar que los managers esenciales estén disponibles
            return (
                vault is not None and 
                works_manager is not None and
                agent_manager is not None
            )
        except:
            return False
            
    def get_skills(self) -> List[Dict[str, Any]]:
        """Obtener lista de skills del usuario directamente del SkillVault"""
        try:
            skills = vault.list_user_skills()
            return [
                {
                    "id": skill.get("id", "unknown"),
                    "name": skill.get("name", "Unknown"),
                    "description": skill.get("description", ""),
                    "level": skill.get("level", "MEDIUM"),
                    "approved": skill.get("approved", False),
                    "created_at": skill.get("installed_at", ""),
                    "version": skill.get("version", "1.0.0")
                }
                for skill in skills
            ]
        except Exception as e:
            logger.error(f"Error obteniendo skills: {e}")
            return []
            
    def save_skill(self, name: str, code: str, skill_id: Optional[str] = None) -> bool:
        """Guardar una skill directamente en el vault"""
        try:
            # Validar código primero
            import ast
            try:
                ast.parse(code)
            except SyntaxError as e:
                logger.error(f"Error de sintaxis en skill: {e}")
                return False
            
            # Verificar que tiene función execute
            tree = ast.parse(code)
            has_execute = any(
                isinstance(node, ast.FunctionDef) and node.name == "execute"
                for node in ast.walk(tree)
            )
            if not has_execute:
                logger.error("Skill debe tener función execute(context)")
                return False
            
            # Guardar en vault
            skill_name = skill_id or name
            result = vault.save_skill(skill_name, code, {"name": name})
            
            return result.get("success", False)
        except Exception as e:
            logger.error(f"Error guardando skill: {e}")
            return False
            
    def execute_skill(self, skill_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar una skill directamente via agent_manager"""
        try:
            # Ejecutar skill
            result = agent_manager.execute_skill(skill_name, context)
            return result
        except Exception as e:
            logger.error(f"Error ejecutando skill: {e}")
            return {"success": False, "error": str(e)}
            
    def get_works(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtener lista de works/archivos directamente del file_manager"""
        try:
            works = works_manager.get_all_works(category=category)
            return works
        except Exception as e:
            logger.error(f"Error obteniendo works: {e}")
            return []
            
    def download_work(self, work_id: str, destination: Path) -> bool:
        """Copiar un work a destino"""
        try:
            work = works_manager.get_work(work_id)
            if not work:
                return False
            
            source_path = Path(work.get("path", ""))
            if not source_path.exists():
                return False
            
            import shutil
            shutil.copy2(source_path, destination)
            return True
        except Exception as e:
            logger.error(f"Error descargando work: {e}")
            return False
            
    def delete_work(self, work_id: str) -> bool:
        """Eliminar un work"""
        try:
            return works_manager.delete_work(work_id)
        except Exception as e:
            logger.error(f"Error eliminando work: {e}")
            return False
            
    def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado del sistema directamente de los managers"""
        try:
            settings = get_settings()
            
            return {
                "status": "healthy",
                "version": "3.0.0",
                "mode": "standalone",
                "skills_count": len(vault.list_skills()),
                "works_count": len(works_manager.list_works()),
                "memory_enabled": True,
                "watchdog_enabled": watchdog is not None,
                "llm_provider": str(llm_manager.default_provider) if llm_manager else "unknown",
                "data_dir": str(settings.DATA_DIR),
                "ui": "PyQt5 Local",
                "webui": "disabled"
            }
        except Exception as e:
            logger.error(f"Error obteniendo status: {e}")
            return {"status": "error", "error": str(e)}
    
    def send_chat_message(self, message: str, session_id: str = "default") -> Dict[str, Any]:
        """Procesar mensaje de chat directamente"""
        try:
            from core.CommandEngine.engine import CommandEngine
            
            ce = CommandEngine()
            parsed = ce.parse(message)
            
            # Guardar en memoria
            memory_core.add_to_stm(session_id, "user", message, {
                "parsed_intent": parsed.intent
            })
            
            # Ejecutar según intent
            if parsed.intent == "list_skills":
                skills = self.get_skills()
                response = f"Skills disponibles: {', '.join([s['name'] for s in skills])}" if skills else "No hay skills"
            elif parsed.intent == "execute_skill":
                skill_name = getattr(parsed, 'skill_name', None)
                if skill_name:
                    result = self.execute_skill(skill_name, {})
                    response = f"Resultado: {result}"
                else:
                    response = "Especifica qué skill ejecutar"
            else:
                response = f"Entendido: {message}"
            
            return {
                "success": True,
                "response": response,
                "parsed_intent": parsed.intent
            }
        except Exception as e:
            logger.error(f"Error en chat: {e}")
            return {"success": False, "error": str(e)}


# Instancia global del cliente (standalone)
api_client = MININAApiClient()
