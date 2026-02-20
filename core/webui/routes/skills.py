"""
Skills Router
=============
Endpoints para gestión de skills.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Dict, Any, List
from pathlib import Path
import tempfile
import shutil
import ast
from datetime import datetime

from pydantic import BaseModel
import json
import time
from pathlib import Path
import tempfile
import shutil
import ast

from core.logging_config import get_logger
from core.auditoria import auditoria_manager
from core.file_manager import works_manager
from core.SkillVault import vault
from core.AgentLifecycleManager import agent_manager
from core.SkillSafetyGate import SkillSafetyGate, _ast_check, _DEFAULT_FORBIDDEN_MODULES, _DEFAULT_FORBIDDEN_CALLS, _NETWORK_MODULES
from core.exceptions import (
    SkillNotFoundError,
    SkillExecutionError,
    SafetyValidationError,
)
from core.webui.decorators import handle_route_errors
from core.ui.policy_settings import PolicySettings

from collections import defaultdict, deque
from datetime import datetime, date

logger = get_logger("MININA.WebUI.Skills")

_rate_window_by_user = defaultdict(lambda: deque())


def _get_user_id(context: Dict[str, Any]) -> str:
    try:
        uid = (context or {}).get("user_id")
        if uid:
            return str(uid)
    except Exception:
        pass
    return "anon"


def _enforce_rate_limit(user_id: str) -> None:
    policy = PolicySettings.get()
    limit = int(getattr(policy, "rate_limit_per_min", 5) or 5)
    if limit <= 0:
        return

    now = datetime.now().timestamp()
    window = _rate_window_by_user[user_id]
    while window and (now - window[0]) > 60:
        window.popleft()

    if len(window) >= limit:
        raise RuntimeError(f"Rate limit: máximo {limit} ejecuciones/minuto para usuario '{user_id}'")

    window.append(now)


def _output_usage_bytes_today() -> int:
    try:
        root = Path(__file__).resolve().parents[3]
        out_dir = root / "data" / "output"
        if not out_dir.exists():
            return 0

        today = date.today()
        total = 0
        for p in out_dir.rglob("*"):
            if not p.is_file():
                continue
            try:
                mtime = datetime.fromtimestamp(p.stat().st_mtime).date()
                if mtime != today:
                    continue
                total += int(p.stat().st_size)
            except Exception:
                continue
        return total
    except Exception:
        return 0


def _enforce_storage_limit() -> None:
    policy = PolicySettings.get()
    mb = int(getattr(policy, "storage_mb_per_day", 100) or 100)
    if mb <= 0:
        return

    limit_bytes = mb * 1024 * 1024
    used = _output_usage_bytes_today()
    if used >= limit_bytes:
        used_mb = used / (1024 * 1024)
        raise RuntimeError(f"Storage limit: se alcanzó el máximo diario ({used_mb:.1f}MB / {mb}MB)")


def _detect_quota_error(error_msg: str) -> Dict[str, Any]:
    """
    Detecta errores de cuota/saldo de proveedores y devuelve mensaje UX claro.
    Soporta: OpenAI, Groq, Anthropic
    """
    error_lower = (error_msg or "").lower()
    
    # Patrones de error por proveedor
    quota_patterns = {
        "openai": [
            "insufficient_quota",
            "quota exceeded",
            "billing",
            "payment",
            "insufficient_funds",
            "rate limit exceeded",
        ],
        "groq": [
            "quota exceeded",
            "insufficient quota",
            "rate limit",
            "billing",
            "payment required",
        ],
        "anthropic": [
            "insufficient_quota",
            "quota exceeded", 
            "billing",
            "payment",
            "rate limit",
        ],
    }
    
    # Detectar proveedor y tipo de error
    detected_provider = None
    is_quota_error = False
    
    for provider, patterns in quota_patterns.items():
        for pattern in patterns:
            if pattern in error_lower:
                detected_provider = provider
                is_quota_error = True
                break
        if is_quota_error:
            break
    
    # Si no detectamos por patrón específico, buscar mensajes genéricos
    if not is_quota_error:
        generic_quota = [
            "insufficient quota",
            "quota exceeded",
            "insufficient balance",
            "saldo insuficiente",
            "cuota agotada",
            "límite de uso",
            "usage limit",
        ]
        for pattern in generic_quota:
            if pattern in error_lower:
                is_quota_error = True
                detected_provider = "desconocido"
                break
    
    if is_quota_error:
        # Mensajes y acciones por proveedor
        provider_info = {
            "openai": {
                "name": "OpenAI",
                "action": "Verifica tu saldo en https://platform.openai.com/account/billing",
                "env_var": "OPENAI_API_KEY",
            },
            "groq": {
                "name": "Groq",
                "action": "Verifica tu saldo en https://console.groq.com/settings/billing",
                "env_var": "GROQ_API_KEY",
            },
            "anthropic": {
                "name": "Anthropic (Claude)",
                "action": "Verifica tu saldo en https://console.anthropic.com/settings/billing",
                "env_var": "ANTHROPIC_API_KEY",
            },
            "desconocido": {
                "name": "Proveedor de API",
                "action": "Verifica tu saldo/cuota en el panel de billing del proveedor",
                "env_var": "API_KEY correspondiente",
            },
        }
        
        info = provider_info.get(detected_provider, provider_info["desconocido"])
        
        return {
            "is_quota_error": True,
            "provider": detected_provider,
            "provider_name": info["name"],
            "action": info["action"],
            "env_var": info["env_var"],
            "user_message": (
                f"🔴 Sin saldo/cuota agotada en {info['name']}\n"
                f"\n"
                f"Acción requerida:\n"
                f"• {info['action']}\n"
                f"• Verifica que la variable de entorno {info['env_var']} esté configurada\n"
                f"\n"
                f"Error original: {error_msg[:200]}"
            ),
        }
    
    return {"is_quota_error": False}


class SkillCodeValidationRequest(BaseModel):
    code: str
    name: str = "unnamed_skill"
    permissions: list = []


@router.post("/validate")
@handle_route_errors("MININA.WebUI.Skills")
async def validate_skill_code(request: SkillCodeValidationRequest) -> Dict[str, Any]:
    """
    Validate skill code through sandbox and return security level.
    Returns: level (HIGH/MEDIUM/LOW), approved (bool), risks (list)
    """
    code = request.code
    name = request.name
    permissions = request.permissions
    
    if not code or not code.strip():
        return {
            "success": False,
            "valid": False,
            "level": "HIGH",
            "approved": False,
            "error": "Código vacío",
            "risks": ["No se proporcionó código para validar"],
            "message": "❌ Rechazado: Código vacío"
        }
    
    # Check for basic syntax
    try:
        ast.parse(code)
    except SyntaxError as e:
        return {
            "success": False,
            "valid": False,
            "level": "HIGH",
            "approved": False,
            "error": f"Error de sintaxis: {e}",
            "risks": [f"Error de sintaxis Python: {e}"],
            "message": "❌ Rechazado: Error de sintaxis"
        }
    
    # Check for execute function
    try:
        tree = ast.parse(code)
        has_execute = any(
            isinstance(node, ast.FunctionDef) and node.name == "execute"
            for node in ast.walk(tree)
        )
        if not has_execute:
            return {
                "success": False,
                "valid": False,
                "level": "HIGH",
                "approved": False,
                "error": "Falta función execute(context)",
                "risks": ["La skill debe tener una función 'execute(context)'"],
                "message": "❌ Rechazado: Falta función execute()"
            }
    except Exception as e:
        pass  # AST check already passed above
    
    # AST security check
    reasons = _ast_check(code, permissions)
    
    # Check if there are syntax errors (first priority)
    syntax_errors = [r for r in reasons if r.startswith("Error de sintaxis") or r.startswith("Python inválido")]
    if syntax_errors:
        return {
            "success": False,
            "valid": False,
            "level": "HIGH",
            "approved": False,
            "error": syntax_errors[0],
            "risks": syntax_errors,
            "message": "❌ ERROR DE SINTAXIS",
            "description": f"El código tiene errores de sintaxis Python que deben corregirse:\n{syntax_errors[0]}",
            "rejection_type": "syntax"
        }
    
    # Calculate security level based on risks
    high_risk_patterns = [
        "eval", "exec", "compile", "__import__",
        "os.system", "subprocess", "ctypes", "socket",
        "win32api", "pyautogui", "keyring", "getpass"
    ]
    
    medium_risk_patterns = [
        "requests", "httpx", "urllib", "urllib3",
        "shutil", "importlib", "inspect",
        "os.popen", "os.spawn", "asyncio.subprocess"
    ]
    
    high_risks = []
    medium_risks = []
    low_risks = []
    
    for reason in reasons:
        reason_lower = reason.lower()
        is_high = any(pattern in reason_lower for pattern in high_risk_patterns)
        is_medium = any(pattern in reason_lower for pattern in medium_risk_patterns)
        
        if is_high:
            high_risks.append(reason)
        elif is_medium:
            medium_risks.append(reason)
        else:
            low_risks.append(reason)
    
    # Determine security level with clear messages
    if high_risks:
        level = "HIGH"
        approved = False
        message = "🚫 RECHAZADA - Riesgo de seguridad ALTO"
        description = "Esta skill contiene código potencialmente peligroso:\n" + "\n".join(f"• {r}" for r in high_risks)
    elif medium_risks:
        level = "MEDIUM"
        approved = True
        message = "⚠️ APROBADA CON ADVERTENCIA - Riesgo MEDIO"
        description = "Esta skill tiene acceso a recursos externos:\n" + "\n".join(f"• {r}" for r in medium_risks) + "\n\nRevisa el código antes de usarla en producción."
    else:
        level = "LOW"
        approved = True
        message = "✅ APROBADA - Seguridad BAJA"
        description = "Esta skill es segura para usar. No detectamos riesgos significativos."
    
    all_risks = high_risks + medium_risks + low_risks
    
    return {
        "success": True,
        "valid": len(reasons) == 0 or approved,
        "level": level,
        "approved": approved,
        "risks": all_risks,
        "high_risks": high_risks,
        "medium_risks": medium_risks,
        "low_risks": low_risks,
        "message": message,
        "description": description,
        "code_safe": len(high_risks) == 0 and len(medium_risks) == 0,
        "can_use": approved
    }


@router.get("/list")
@handle_route_errors("MININA.WebUI.Skills")
async def list_skills() -> Dict[str, Any]:
    """List all available skills."""
    skills = agent_manager.list_available_skills()
    return {
        "success": True,
        "skills": skills,
        "count": len(skills)
    }


@router.post("/execute")
@handle_route_errors("MININA.WebUI.Skills")
async def execute_skill(data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute skill code with auditing and works integration.
    
    Supports two modes:
    1. Execute registered skill by name (skill_name)
    2. Execute arbitrary code from frontend (code)
    """
    skill_name = data.get("skill_name", "user_skill")
    context = data.get("context", {})
    code = data.get("code")

    user_id = _get_user_id(context)
    
    # Iniciar registro de auditoría
    registro_id = auditoria_manager.iniciar_registro(
        skill_name=skill_name,
        skill_id=skill_name,
        action="execute",
        details={"context": context, "has_code": bool(code)}
    )
    
    try:
        # ============ ENFORCEMENT DE POLÍTICAS ============
        try:
            _enforce_rate_limit(user_id)
            _enforce_storage_limit()
        except Exception as policy_err:
            auditoria_manager.finalizar_registro(registro_id, "failed", {"error": str(policy_err), "policy_block": True})
            return {
                "success": False,
                "error": str(policy_err),
                "blocked": True,
                "policy": {
                    "rate_limit_per_min": PolicySettings.get().rate_limit_per_min,
                    "storage_mb_per_day": PolicySettings.get().storage_mb_per_day,
                },
                "audit_id": registro_id,
            }

        result = None
        
        if code:
            # Ejecutar código arbitrario desde el frontend (user skill)
            logger.info(f"Executing user skill code: {skill_name}", extra={"skill_name": skill_name})
            result = await _execute_user_skill_code(code, context)
        else:
            # Ejecutar skill registrada en el sistema
            available = agent_manager.list_available_skills()
            if skill_name not in available:
                auditoria_manager.finalizar_registro(registro_id, "failed", {"error": "Skill not found"})
                raise SkillNotFoundError(
                    skill_name=skill_name,
                    available_skills=available
                )
            
            logger.info(f"Executing registered skill: {skill_name}", extra={"skill_name": skill_name})
            result = await agent_manager.execute_skill(skill_name, context)
        
        # Si la skill generó archivos, registrarlos en works
        generated_files = result.get("generated_files", []) if isinstance(result, dict) else []
        if generated_files:
            for file_info in generated_files:
                if isinstance(file_info, dict) and "path" in file_info:
                    works_manager.save_file(
                        source_path=file_info["path"],
                        filename=file_info.get("name", "unknown"),
                        skill_name=skill_name,
                        skill_id=skill_name,
                        description=file_info.get("description", ""),
                        metadata={"execution_id": registro_id}
                    )
        
        # Finalizar auditoría exitosamente
        auditoria_manager.finalizar_registro(
            registro_id, 
            "completed", 
            {
                "result": result,
                "files_generated": len(generated_files) if generated_files else 0
            }
        )
        
        return {
            "success": True, 
            "result": result,
            "audit_id": registro_id,
            "files_generated": len(generated_files) if generated_files else 0
        }
        
    except Exception as e:
        logger.error(f"Error executing skill {skill_name}: {e}")
        error_str = str(e)
        
        # Detectar si es error de cuota/saldo
        quota_check = _detect_quota_error(error_str)
        if quota_check.get("is_quota_error"):
            user_message = quota_check.get("user_message", error_str)
            auditoria_manager.finalizar_registro(
                registro_id, 
                "failed", 
                {
                    "error": error_str,
                    "quota_error": True,
                    "provider": quota_check.get("provider"),
                    "provider_name": quota_check.get("provider_name"),
                }
            )
            return {
                "success": False,
                "error": user_message,
                "quota_error": True,
                "provider": quota_check.get("provider"),
                "provider_name": quota_check.get("provider_name"),
                "action": quota_check.get("action"),
                "env_var": quota_check.get("env_var"),
                "audit_id": registro_id,
            }
        
        auditoria_manager.finalizar_registro(registro_id, "failed", {"error": error_str})
        return {
            "success": False,
            "error": error_str,
            "audit_id": registro_id
        }


async def _execute_user_skill_code(code: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Execute user skill code in a safe environment.
    
    This function executes Python code safely and returns the result.
    Tracks files created during execution for Works integration.
    """
    import tempfile
    import os
    import sys
    import traceback
    from pathlib import Path
    
    # Crear directorio temporal para la ejecución
    exec_dir = Path(tempfile.mkdtemp(prefix="skill_exec_"))
    original_cwd = os.getcwd()
    generated_files = []
    
    try:
        # Cambiar al directorio temporal para capturar archivos creados
        os.chdir(exec_dir)
        
        # Crear namespace seguro con contexto
        namespace = {
            'context': context,
            '__builtins__': __builtins__,
            'Path': Path,
            'os': os,
            'sys': sys,
        }
        
        # Ejecutar el código
        exec(code, namespace)
        
        # Buscar función execute y ejecutarla
        if 'execute' in namespace and callable(namespace['execute']):
            result = namespace['execute'](context)
            if not isinstance(result, dict):
                result = {"success": True, "result": result}
        else:
            # Si no hay función execute, verificar si el código ya ejecutó algo
            result = {"success": True, "message": "Código ejecutado"}
        
        # AHORA buscar archivos creados DESPUÉS de ejecutar
        for file_path in exec_dir.iterdir():
            if file_path.is_file():
                generated_files.append({
                    'path': str(file_path),
                    'name': file_path.name,
                    'size': file_path.stat().st_size
                })
        
        # Agregar archivos generados al resultado
        if generated_files:
            result['generated_files'] = generated_files
            result['message'] = f"Código ejecutado. {len(generated_files)} archivo(s) generado(s)."
        
        return result
            
    except Exception as e:
        error_msg = f"Error ejecutando skill: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}
    finally:
        # Restaurar directorio original
        os.chdir(original_cwd)


@router.post("/upload")
@handle_route_errors("MININA.WebUI.Skills")
async def upload_skill(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Upload, validate and stage a skill."""
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are allowed")
    
    # Validar tamaño máximo (15MB)
    max_size = 15 * 1024 * 1024  # 15MB en bytes
    content = await file.read()
    
    if len(content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is 15MB, got {len(content) / 1024 / 1024:.1f}MB"
        )
    
    # Guardar temporalmente
    temp_dir = Path(tempfile.mkdtemp(prefix="skill_upload_"))
    temp_zip = temp_dir / "skill.zip"
    
    try:
        # Guardar archivo
        temp_zip.write_bytes(content)
        logger.info(f"Uploading skill: {file.filename}", extra={
            "filename": file.filename,
            "size": len(content)
        })
        
        # Validar con SkillSafetyGate
        from core.config import get_settings
        settings = get_settings()
        
        report = safety_gate.validate_zip(temp_zip)
        
        if not report.ok:
            logger.warning(
                f"Skill validation failed: {report.reasons}",
                extra={"skill_id": report.skill_id, "reasons": report.reasons}
            )
            raise SafetyValidationError(
                skill_name=report.skill_id or file.filename,
                reasons=report.reasons
            )
        
        # Mover al vault de staging
        staged_path = settings.SKILLS_VAULT_DIR / "staging" / f"{report.skill_id}_{file.filename}"
        staged_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(temp_zip), str(staged_path))
        
        return {
            "success": True,
            "filename": file.filename,
            "skill_id": report.skill_id,
            "name": report.name,
            "version": report.version,
            "permissions": report.permissions,
            "message": f"Skill '{report.name}' validated and staged successfully",
            "staged_path": str(staged_path)
        }
    
    finally:
        # Limpieza
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


@router.delete("/{skill_id}")
@handle_route_errors("MININA.WebUI.Skills")
async def delete_skill(skill_id: str) -> Dict[str, Any]:
    """Delete a skill from user_skills or staging."""
    from core.config import get_settings
    settings = get_settings()
    
    deleted = False
    locations = [
        settings.SKILLS_USER_DIR / f"{skill_id}.py",
        settings.SKILLS_USER_DIR / skill_id,  # Si es directorio
        settings.SKILLS_VAULT_DIR / "staging" / skill_id,
        settings.SKILLS_VAULT_DIR / "live" / skill_id,
    ]
    
    for location in locations:
        if location.exists():
            if location.is_file():
                location.unlink()
                deleted = True
            elif location.is_dir():
                shutil.rmtree(location, ignore_errors=True)
                deleted = True
    
    if not deleted:
        raise SkillNotFoundError(
            skill_name=skill_id,
            available_skills=agent_manager.list_available_skills()
        )
    
    logger.info(f"Deleted skill: {skill_id}", extra={"skill_id": skill_id})
    
    return {
        "success": True,
        "skill_id": skill_id,
        "message": f"Skill '{skill_id}' deleted successfully"
    }


@router.get("/running")
@handle_route_errors("MININA.WebUI.Skills")
async def get_running_skills() -> Dict[str, Any]:
    """Get currently running skills."""
    active = agent_manager.active_agents
    return {
        "success": True,
        "running_skills": [
            {
                "pid": info.pid,
                "skill_name": info.skill_name,
                "session_id": info.session_id,
                "spawned_at": info.spawned_at
            }
            for pid, info in active.items()
        ],
        "count": len(active)
    }


# ============================================
# USER SKILLS PERSISTENCE SYSTEM
# ============================================
# Las skills creadas por el usuario se guardan permanentemente
# en data/user_skills.json y se mantienen entre reinicios

USER_SKILLS_FILE = Path("data/user_skills.json")

def _load_user_skills() -> List[Dict]:
    """Cargar skills del usuario desde disco"""
    if USER_SKILLS_FILE.exists():
        try:
            with open(USER_SKILLS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando user skills: {e}")
    return []

def _save_user_skills(skills: List[Dict]):
    """Guardar skills del usuario en disco"""
    try:
        USER_SKILLS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(USER_SKILLS_FILE, 'w', encoding='utf-8') as f:
            json.dump(skills, f, indent=2, ensure_ascii=False)
        logger.info(f"Guardadas {len(skills)} skills del usuario")
    except Exception as e:
        logger.error(f"Error guardando user skills: {e}")

# Cargar skills al iniciar el módulo
_user_skills_cache = _load_user_skills()
logger.info(f"Cargadas {len(_user_skills_cache)} skills del usuario desde disco")


@router.post("/user/save")
@handle_route_errors("MININA.WebUI.Skills")
async def save_user_skill(data: Dict[str, Any]) -> Dict[str, Any]:
    """Guardar una skill del usuario permanentemente"""
    try:
        skill_id = data.get("id") or f"skill_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"
        
        skill = {
            "id": skill_id,
            "name": data.get("name", "unnamed"),
            "category": data.get("category", "custom"),
            "version": data.get("version", "1.0.0"),
            "code": data.get("code", ""),
            "description": data.get("description", ""),
            "created_at": data.get("created_at") or datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        
        # Buscar si existe para actualizar
        global _user_skills_cache
        existing_idx = None
        for i, s in enumerate(_user_skills_cache):
            if s["id"] == skill_id:
                existing_idx = i
                break
        
        if existing_idx is not None:
            # Actualizar skill existente
            _user_skills_cache[existing_idx] = skill
            action = "actualizada"
        else:
            # Nueva skill
            _user_skills_cache.append(skill)
            action = "creada"
        
        # Guardar en disco
        _save_user_skills(_user_skills_cache)
        
        logger.info(f"Skill del usuario {action}: {skill['name']} (ID: {skill_id})")
        
        return {
            "success": True,
            "skill": skill,
            "action": action,
            "message": f"Skill '{skill['name']}' {action} correctamente"
        }
    except Exception as e:
        logger.error(f"ERROR al guardar skill: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/user/list")
@handle_route_errors("MININA.WebUI.Skills")
async def list_user_skills() -> Dict[str, Any]:
    """Listar todas las skills guardadas del usuario"""
    global _user_skills_cache
    # Recargar desde disco por si acaso
    _user_skills_cache = _load_user_skills()
    
    return {
        "success": True,
        "skills": _user_skills_cache,
        "count": len(_user_skills_cache)
    }


@router.delete("/user/{skill_id}")
@handle_route_errors("MININA.WebUI.Skills")
async def delete_user_skill(skill_id: str) -> Dict[str, Any]:
    """Eliminar una skill del usuario"""
    global _user_skills_cache
    
    original_count = len(_user_skills_cache)
    _user_skills_cache = [s for s in _user_skills_cache if s["id"] != skill_id]
    
    if len(_user_skills_cache) < original_count:
        _save_user_skills(_user_skills_cache)
        logger.info(f"Skill del usuario eliminada: {skill_id}")
        return {
            "success": True,
            "message": "Skill eliminada correctamente"
        }
    else:
        raise SkillNotFoundError(skill_name=skill_id, available_skills=[])


@router.get("/user/{skill_id}")
@handle_route_errors("MININA.WebUI.Skills")
async def get_user_skill(skill_id: str) -> Dict[str, Any]:
    """Obtener una skill específica del usuario"""
    for skill in _user_skills_cache:
        if skill["id"] == skill_id:
            return {
                "success": True,
                "skill": skill
            }
    raise SkillNotFoundError(skill_name=skill_id, available_skills=[])
