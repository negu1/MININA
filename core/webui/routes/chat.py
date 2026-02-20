"""
Chat Router
===========
Endpoints para el chat y comunicación con LLM.
Integrado con sistema de memoria MININA.
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path
import json

from core.logging_config import get_logger
from core.CortexBus import bus
from core.CommandEngine.engine import CommandEngine
from core.AgentLifecycleManager import agent_manager
from core.MemoryCore import memory_core
from core.LLMManager import llm_manager, ProviderType
from core.exceptions import SkillNotFoundError, SkillExecutionError
from core.webui.decorators import handle_route_errors

logger = get_logger("MININA.WebUI.Chat")
router = APIRouter()
ce = CommandEngine()


@router.post("/send")
@handle_route_errors("MININA.WebUI.Chat")
async def send_message(data: Dict[str, Any]) -> Dict[str, Any]:
    """Send chat message and get response."""
    message = data.get("message", "")
    user_id = data.get("user_id", "web_user")
    session_id = data.get("session_id", f"default_{user_id}")
    
    if not message:
        raise HTTPException(status_code=400, detail="message is required")
    
    # Guardar mensaje del usuario en STM
    memory_core.add_to_stm(session_id, "user", message, {
        "user_id": user_id,
        "intent": None  # Se actualizará después del parsing
    })
    
    # Parse command
    parsed = ce.parse(message)
    
    # Actualizar metadata con intent detectado
    memory_core.add_to_stm(session_id, "system", f"Intent detectado: {parsed.intent}", {
        "parsed_intent": parsed.intent,
        "skill_name": getattr(parsed, 'skill_name', None)
    })
    
    if parsed.intent == "list_skills":
        skills = agent_manager.list_available_skills()
        response_text = f"Skills disponibles: {', '.join(skills)}" if skills else "No hay skills instaladas"
        
        # Guardar respuesta en STM
        memory_core.add_to_stm(session_id, "assistant", response_text, {
            "type": "skills_list",
            "skills_count": len(skills)
        })
        
        return {
            "success": True,
            "response": response_text,
            "type": "skills_list"
        }
    
    elif parsed.intent == "status":
        response_text = "Sistema operativo. MININA está funcionando correctamente."
        memory_core.add_to_stm(session_id, "assistant", response_text, {"type": "status"})
        
        return {
            "success": True,
            "response": response_text,
            "type": "status"
        }
    
    elif parsed.intent == "use_skill":
        # Verificar que la skill existe
        available = agent_manager.list_available_skills()
        if parsed.skill_name not in available:
            raise SkillNotFoundError(
                skill_name=parsed.skill_name,
                available_skills=available
            )
        
        # Buscar conocimiento relevante en LTM antes de ejecutar
        relevant_knowledge = memory_core.search_ltm(
            f"skill {parsed.skill_name}", 
            category="skill_execution",
            limit=3
        )
        
        context = ce.to_context(parsed, user_id)
        
        # Añadir contexto de memoria si existe
        if relevant_knowledge:
            context['memory_context'] = [k['content'] for k in relevant_knowledge]
        
        result = await agent_manager.execute_skill(parsed.skill_name, context)
        
        response_text = json.dumps(result) if isinstance(result, dict) else str(result)
        
        # Guardar ejecución en memoria
        memory_core.add_to_stm(session_id, "assistant", response_text, {
            "type": "skill_result",
            "skill": parsed.skill_name,
            "result": result
        })
        
        # Almacenar en LTM para aprendizaje (si fue exitoso)
        if isinstance(result, dict) and result.get('success'):
            memory_core.store_in_ltm(
                content=f"Skill '{parsed.skill_name}' ejecutada exitosamente con contexto: {context.get('task', 'N/A')}",
                category="skill_execution",
                source="session_consolidation",
                confidence=0.7,
                metadata={
                    "skill_name": parsed.skill_name,
                    "user_id": user_id,
                    "session_id": session_id
                }
            )
        
        return {
            "success": True,
            "response": result,
            "type": "skill_result",
            "skill": parsed.skill_name,
            "memory_references": len(relevant_knowledge)
        }
    
    elif parsed.intent == "remember":
        # Almacenar información explícitamente
        fact_content = parsed.task if hasattr(parsed, 'task') else message.replace("recuerda", "").strip()
        
        result = memory_core.store_in_ltm(
            content=fact_content,
            category="user_preference",
            source="user_direct",
            confidence=0.9,
            metadata={"user_id": user_id, "session_id": session_id}
        )
        
        if result['success']:
            response_text = f"Guardado en memoria: {fact_content}"
        else:
            response_text = f"No pude guardar eso: {result.get('error', 'Error desconocido')}"
        
        memory_core.add_to_stm(session_id, "assistant", response_text, {
            "type": "memory_store",
            "stored": result['success']
        })
        
        return {
            "success": result['success'],
            "response": response_text,
            "type": "memory_store"
        }
    
    elif parsed.intent == "recall":
        # Recuperar información
        query = parsed.task if hasattr(parsed, 'task') else message.replace("recuerda", "").strip()
        
        # Buscar en STM primero (contexto reciente)
        stm_context = memory_core.get_stm_context(session_id, limit=5)
        
        # Buscar en LTM
        ltm_results = memory_core.search_ltm(query, limit=5)
        
        if ltm_results:
            response_parts = [f"Encontré esto en mi memoria:"]
            for i, entry in enumerate(ltm_results[:3], 1):
                response_parts.append(f"{i}. {entry['content']} (confianza: {entry['confidence']:.0%})")
            response_text = "\n".join(response_parts)
        else:
            response_text = "No encontré nada relevante en mi memoria sobre eso."
        
        memory_core.add_to_stm(session_id, "assistant", response_text, {
            "type": "memory_recall",
            "query": query,
            "results_found": len(ltm_results)
        })
        
        return {
            "success": True,
            "response": response_text,
            "type": "memory_recall",
            "stm_context": len(stm_context),
            "ltm_results": len(ltm_results)
        }
    
    else:
        # Chat general - usar LLM con provider especificado o el activo
        provider_param = data.get("provider", None)
        
        # Si se especifica un provider, usarlo o fallar con mensaje claro
        if provider_param:
            try:
                provider_type = ProviderType(provider_param)
                config = llm_manager.providers.get(provider_type)
                
                # Sincronizar API key desde SecureCredentialStore
                from core.SecureCredentials import credential_store
                api_key = credential_store.get_credential("llm_apis", f"{provider_param}_key")
                if api_key and config:
                    config.api_key = api_key
                    config.enabled = True  # FORZAR enabled si hay API key
                    # También actualizar modelo si existe
                    model = credential_store.get_credential("llm_apis", f"{provider_param}_model")
                    if model:
                        config.model = model
                    logger.info(f"API key sincronizada para {provider_param}")
                
                # Si hay API key o está enabled o es local, usarlo
                if config and (config.enabled or config.is_local or api_key):
                    llm_manager.active_provider = provider_type
                    logger.info(f"Using specified provider: {provider_param} (has_key: {bool(api_key)}, enabled: {config.enabled if config else False})")
                else:
                    # Provider especificado pero no configurado
                    error_msg = f"⚠️ El provider '{provider_param}' no está configurado. "
                    if provider_param == "groq":
                        error_msg += "Ve a APIs → Groq y guarda tu API key."
                    elif provider_param == "gemini":
                        error_msg += "Ve a APIs → Gemini y guarda tu API key."
                    elif provider_param == "openai":
                        error_msg += "Ve a APIs → OpenAI y guarda tu API key."
                    elif provider_param == "ollama":
                        error_msg += "Instala Ollama localmente (ollama.com/download)."
                    else:
                        error_msg += f"Configura tu API key en la sección de APIs."
                    
                    return {
                        "success": False,
                        "response": error_msg,
                        "type": "chat",
                        "error": "provider_not_configured"
                    }
            except ValueError:
                return {
                    "success": False,
                    "response": f"⚠️ Provider inválido: {provider_param}",
                    "type": "chat",
                    "error": "invalid_provider"
                }
        
        # Si no hay provider especificado ni activo, dar error claro
        if not llm_manager.active_provider:
            return {
                "success": False,
                "response": "⚠️ No hay ninguna API configurada. Ve al menú 'API Keys' y configura Gemini, OpenAI, Groq u Ollama.",
                "type": "chat",
                "error": "no_provider"
            }
        
        try:
            # Verificar que hay un provider configurado
            if not llm_manager.active_provider:
                response_text = "⚠️ No hay ninguna API de IA configurada. Por favor, configura una API en el menú 'API Keys' (Gemini, OpenAI, Groq, Ollama, etc.)"
                memory_core.add_to_stm(session_id, "assistant", response_text, {
                    "type": "chat",
                    "error": "no_provider_configured"
                })
                return {
                    "success": False,
                    "response": response_text,
                    "type": "chat",
                    "error": "no_provider"
                }
            
            # Verificar que el provider está habilitado
            current_config = llm_manager.get_active_config()
            if not current_config:
                response_text = "⚠️ Error de configuración del provider activo"
                return {"success": False, "response": response_text, "type": "chat", "error": "config_error"}
            
            # Si es local (Ollama), verificar que esté disponible
            if current_config.is_local:
                check = await llm_manager.check_local_provider(llm_manager.active_provider)
                if not check.get("available"):
                    response_text = f"⚠️ {check.get('error', 'Provider local no disponible')}\n\n" + "\n".join(check.get('setup_instructions', []))
                    memory_core.add_to_stm(session_id, "assistant", response_text, {
                        "type": "chat",
                        "error": "local_provider_unavailable"
                    })
                    return {
                        "success": False,
                        "response": response_text,
                        "type": "chat",
                        "error": "local_unavailable",
                        "setup_instructions": check.get('setup_instructions', [])
                    }
            
            # Buscar conocimiento relevante en LTM para contexto
            relevant = memory_core.search_ltm(message, limit=3)
            context_parts = []
            if relevant:
                context_parts.append("Información relevante de memoria:")
                for r in relevant:
                    context_parts.append(f"- {r['content']}")
            
            # Preparar el prompt completo
            full_prompt = message
            if context_parts:
                full_prompt = "\n".join(context_parts) + "\n\nPregunta actual: " + message
            
            # Generar respuesta con LLM
            logger.info(f"Generating response with {llm_manager.active_provider.value}")
            response_chunks = []
            async for chunk in llm_manager.generate(
                prompt=full_prompt,
                system="Eres MININA, una asistente de IA útil y amigable. Responde en español de manera concisa y natural.",
                max_tokens=2000,
                temperature=0.7,
                stream=False
            ):
                response_chunks.append(chunk)
            
            response_text = "".join(response_chunks)
            
            if response_text.startswith("Error:") or response_text.startswith("⚠️"):
                # Hubo un error en la generación
                memory_core.add_to_stm(session_id, "assistant", response_text, {
                    "type": "chat",
                    "error": "llm_error",
                    "provider": llm_manager.active_provider.value if llm_manager.active_provider else None
                })
                return {
                    "success": False,
                    "response": response_text,
                    "type": "chat",
                    "error": "llm_generation_failed"
                }
            
            # Guardar respuesta exitosa en memoria
            memory_core.add_to_stm(session_id, "assistant", response_text, {
                "type": "chat",
                "memory_refs": len(relevant),
                "provider": llm_manager.active_provider.value if llm_manager.active_provider else None
            })
            
            # Broadcast to bus
            await bus.publish("chat.MESSAGE", {
                "message": message,
                "response": response_text,
                "user_id": user_id,
                "session_id": session_id,
                "has_memory_context": bool(relevant),
                "provider": llm_manager.active_provider.value if llm_manager.active_provider else None
            }, sender="WebUI")
            
            return {
                "success": True,
                "response": response_text,
                "type": "chat",
                "memory_context": [r['content'] for r in relevant],
                "provider": llm_manager.active_provider.value if llm_manager.active_provider else None
            }
            
        except Exception as e:
            logger.error(f"Error in LLM chat: {e}")
            response_text = f"⚠️ Error al conectar con la API: {str(e)}. Verifica que la API key esté configurada correctamente."
            memory_core.add_to_stm(session_id, "assistant", response_text, {
                "type": "chat",
                "error": str(e)
            })
            return {
                "success": False,
                "response": response_text,
                "type": "chat",
                "error": str(e)
            }


def _save_to_history(user_id: str, message: str, response: str, msg_type: str, skill: str = None):
    """Save message to chat history."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "message": message,
        "response": response,
        "type": msg_type
    }
    if skill:
        entry["skill"] = skill
    
    _chat_history.append(entry)
    
    # Mantener solo últimos MAX_HISTORY mensajes
    if len(_chat_history) > MAX_HISTORY:
        _chat_history.pop(0)


@router.get("/history")
@handle_route_errors("MININA.WebUI.Chat")
async def get_chat_history(session_id: str, limit: int = 50) -> Dict[str, Any]:
    """Get chat history from STM for a session."""
    context = memory_core.get_stm_context(session_id, limit)
    
    return {
        "success": True,
        "session_id": session_id,
        "messages": context,
        "count": len(context)
    }


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str = "default"):
    """WebSocket endpoint for real-time chat with memory."""
    await websocket.accept()
    client_id = f"ws_{id(websocket)}"
    
    logger.info(f"WebSocket client connected: {client_id}, session: {session_id}")
    
    # Enviar contexto previo si existe
    try:
        context = memory_core.get_stm_context(session_id, limit=5)
        if context:
            await websocket.send_json({
                "type": "context",
                "session_id": session_id,
                "previous_messages": context
            })
    except Exception:
        pass
    
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            role = data.get("role", "user")
            
            # Guardar en memoria
            memory_core.add_to_stm(session_id, role, message)
            
            # Echo back
            await websocket.send_json({
                "type": "echo",
                "data": data,
                "client_id": client_id,
                "stored": True
            })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {client_id}")
        # Consolidar sesión a MTM al desconectar
        memory_core.clear_session(session_id)
    except Exception as e:
        logger.warning(f"WebSocket error for {client_id}: {e}")
