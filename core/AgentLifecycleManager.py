import asyncio
import importlib.util
import logging
import multiprocessing as mp
import os
import signal
import sys
import time
import uuid
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import psutil

from core.CortexBus import bus

logger = logging.getLogger("AgentLifecycleManager")


@dataclass
class AgentInfo:
    pid: int
    skill_name: str
    context: Dict[str, Any]
    spawned_at: float
    session_id: str
    result_queue: Any = field(default=None)
    max_lifetime: int = 300


class AgentLifecycleManager:
    def __init__(self, skills_dir: Optional[str] = None):
        # Usar ruta relativa al directorio de MININA en Desktop
        minina_root = Path(__file__).parent.parent
        self.data_dir = minina_root / "data"
        
        if skills_dir:
            self.skills_dir = Path(skills_dir)
        else:
            self.skills_dir = self.data_dir / "skills"
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        
        self.user_skills_dir = self.data_dir / "skills_user"
        self.user_skills_dir.mkdir(parents=True, exist_ok=True)
        
        # Usar el mismo live_dir que SkillVault (ruta relativa)
        self.live_dir = self.data_dir / "skills_vault" / "live"
        self.live_dir.mkdir(parents=True, exist_ok=True)
        
        self.active_agents: Dict[int, AgentInfo] = {}
        self._results_buffer: Dict[str, Dict[str, Any]] = {}
        self._retry_callbacks: Dict[str, Any] = {}

        bus.subscribe("skill.RETRY_REQUEST", self._on_retry_request)

    async def execute_skill(self, skill_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar skill directamente y retornar resultado"""
        try:
            pid = self.spawn_skill(skill_name, context)
            agent = self.active_agents[pid]
            session_id = agent.session_id
            
            result = await asyncio.wait_for(self._wait_for_result(pid, session_id), timeout=30)
            self._kill_agent(pid)
            
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _register_retry(self, session_id: str, callback: Any) -> None:
        self._retry_callbacks[session_id] = callback

    def _pop_retry(self, session_id: str) -> Optional[Any]:
        try:
            return self._retry_callbacks.pop(session_id, None)
        except Exception:
            return None

    async def _on_retry_request(self, data: Dict[str, Any]) -> None:
        session_id = (data or {}).get("session_id")
        if not session_id:
            return

        cb = self._pop_retry(session_id)
        if not cb:
            await bus.publish(
                "user.SPEAK",
                {"message": "No hay reintento disponible para esa sesión.", "priority": "high"},
                sender="AgentLifecycleManager",
            )
            return

        try:
            await bus.publish(
                "user.SPEAK",
                {"message": "🔁 Reintentando...", "priority": "normal"},
                sender="AgentLifecycleManager",
            )
            await cb()
        except Exception as e:
            await bus.publish(
                "user.SPEAK",
                {"message": f"❌ Reintento falló: {str(e)}", "priority": "high"},
                sender="AgentLifecycleManager",
            )

    def list_available_skills(self) -> list[str]:
        skills = []
        if self.skills_dir.exists():
            for f in self.skills_dir.glob("*.py"):
                if not f.name.startswith("_"):
                    skills.append(f.stem)
        if self.user_skills_dir.exists():
            for f in self.user_skills_dir.glob("*.py"):
                if not f.name.startswith("_"):
                    skills.append(f.stem)
        return list(sorted(set(skills)))

    def get_skill_path(self, skill_name: str) -> Optional[Path]:
        # Primero buscar en live_dir (prioridad)
        live_path = self.live_dir / skill_name / "skill.py"
        if live_path.exists():
            return live_path
        # Luego en user_skills_dir
        up = self.user_skills_dir / f"{skill_name}.py"
        if up.exists():
            return up
        # Finalmente en skills_dir
        p = self.skills_dir / f"{skill_name}.py"
        return p if p.exists() else None

    def _skill_needs_direct_execution(self, skill_path: Path) -> bool:
        """
        Detecta si una skill necesita ejecución directa (sin sandbox)
        porque usa UI automation o dependencias especiales.
        """
        try:
            code = skill_path.read_text(encoding='utf-8', errors='ignore')
            ui_modules = ['pywinauto', 'pyautogui', 'win32gui', 'win32con', 
                         'win32api', 'ctypes.wintypes', 'autogui']
            return any(module in code for module in ui_modules)
        except Exception:
            return False

    def spawn_skill(self, skill_name: str, context: Dict[str, Any]) -> int:
        skill_path = self.get_skill_path(skill_name)
        if not skill_path:
            available = self.list_available_skills()
            raise FileNotFoundError(f"Skill '{skill_name}' no encontrada. Disponibles: {available}")
        
        # Verificar si la skill necesita ejecución directa (UI automation)
        if self._skill_needs_direct_execution(skill_path):
            logger.info(f"Skill '{skill_name}' usa UI automation - ejecutando directamente sin sandbox")
            return self._spawn_skill_direct(skill_path, context)
        
        # Ejecución normal con sandbox
        return self._spawn_skill_sandbox(skill_path, context)
    
    def _spawn_skill_direct(self, skill_path: Path, context: Dict[str, Any]) -> int:
        """Ejecuta skill directamente en el proceso actual (sin sandbox) para UI automation"""
        import threading
        
        skill_name = skill_path.stem
        session_id = str(uuid.uuid4())
        
        # Crear un resultado fake para mantener compatibilidad
        class FakeQueue:
            def __init__(self, manager):
                self.manager = manager
                self.result = None
            def put(self, item):
                self.result = item
                # Publicar resultado async
                try:
                    bus.publish_sync("agent.RESULT", item, sender="SkillWorker")
                except:
                    pass
            def get_nowait(self):
                return self.result
        
        fake_queue = FakeQueue(self)
        
        def execute_direct():
            try:
                # Ejecutar directamente
                spec = importlib.util.spec_from_file_location(f"skill_{skill_name}", str(skill_path))
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if not hasattr(module, "execute"):
                    raise AttributeError(f"Skill {skill_name} no tiene función 'execute'")
                
                result = module.execute(context)
                
                fake_queue.put({
                    "session_id": session_id,
                    "skill": skill_name,
                    "result": result,
                    "success": True,
                    "timestamp": time.time(),
                })
            except Exception as e:
                fake_queue.put({
                    "session_id": session_id,
                    "skill": skill_name,
                    "error": str(e),
                    "success": False,
                    "timestamp": time.time(),
                })
        
        # Ejecutar en thread separado para no bloquear
        thread = threading.Thread(target=execute_direct, name=f"skill-{skill_name}")
        thread.start()
        
        # Simular un PID para compatibilidad
        fake_pid = int(time.time() * 1000) % 100000
        
        self.active_agents[fake_pid] = AgentInfo(
            pid=fake_pid,
            skill_name=skill_name,
            context=context,
            spawned_at=time.time(),
            session_id=session_id,
            result_queue=fake_queue,
        )
        
        bus.publish_sync(
            "agent.SPAWNED",
            {"pid": fake_pid, "skill_name": skill_name, "session_id": session_id, 
             "context": context, "direct_execution": True},
            sender="AgentLifecycleManager",
        )
        
        return fake_pid

    def _spawn_skill_sandbox(self, skill_path: Path, context: Dict[str, Any]) -> int:
        """Ejecuta skill con sandbox (proceso aislado en directorio temporal)"""
        
        skill_name = skill_path.stem
        
        # Crear directorio sandbox temporal en ubicación fija
        import tempfile
        temp_base = self.data_dir / "temp_sandbox"
        temp_base.mkdir(parents=True, exist_ok=True)
        
        sandbox_dir = Path(tempfile.mkdtemp(prefix=f"skill_{skill_name}_", dir=str(temp_base)))
        
        # Crear directorio output en el sandbox para que el skill pueda guardar archivos
        sandbox_output_dir = sandbox_dir / "output"
        sandbox_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Copiar skill.py al sandbox
        sandbox_skill_path = sandbox_dir / "skill.py"
        try:
            # Leer código original
            original_code = skill_path.read_text(encoding='utf-8')
            
            # Corregir rutas 'output/' hardcoded para usar ruta absoluta del sandbox
            sandbox_output_str = str(sandbox_dir / "output").replace('\\', '/')
            corrected_code = original_code.replace("'output/", f"'{sandbox_output_str}/")
            corrected_code = corrected_code.replace('"output/', f'"{sandbox_output_str}/')
            corrected_code = corrected_code.replace("'output\\", f"'{sandbox_output_str}/")
            corrected_code = corrected_code.replace('"output\\', f'"{sandbox_output_str}/')
            
            # Escribir código corregido
            sandbox_skill_path.write_text(corrected_code, encoding='utf-8')
        except Exception as e:
            logger.error(f"Error corrigiendo rutas en skill: {e}")
            # Fallback: copiar sin modificar
            try:
                shutil.copy2(skill_path, sandbox_skill_path)
            except Exception as e2:
                logger.error(f"Error copiando skill: {e2}")
                sandbox_skill_path = skill_path
        
        # Leer permisos del manifest si existe
        permissions = []
        live_manifest = self.live_dir / skill_name / "manifest.json"
        if live_manifest.exists():
            try:
                import json
                manifest = json.loads(live_manifest.read_text(encoding="utf-8"))
                permissions = manifest.get("permissions", [])
                # Copiar manifest al sandbox
                shutil.copy2(live_manifest, sandbox_dir / "manifest.json")
            except Exception:
                pass
        
        # Agregar sandbox_dir al contexto para que el skill pueda usarlo
        context["permissions"] = permissions
        context["skill_name"] = skill_name
        context["sandbox_dir"] = str(sandbox_dir)

        session_id = str(uuid.uuid4())
        ctx = mp.get_context("spawn")
        q = ctx.Queue()
        
        # Preparar environment con PYTHONPATH
        import site
        user_site = site.getusersitepackages()
        pythonpath = os.environ.get('PYTHONPATH', '')
        paths_to_add = [p for p in sys.path if 'site-packages' in p]
        if user_site and user_site not in paths_to_add:
            paths_to_add.append(user_site)
        
        new_pythonpath = os.pathsep.join(paths_to_add + ([pythonpath] if pythonpath else []))
        
        proc = ctx.Process(
            target=_wrapped_execute,
            args=(str(sandbox_skill_path), context, session_id, q, new_pythonpath, str(sandbox_dir)),
            name=f"skill-{skill_name}-{session_id[:8]}",
        )
        proc.start()

        pid = proc.pid
        self.active_agents[pid] = AgentInfo(
            pid=pid,
            skill_name=skill_name,
            context=context,
            spawned_at=time.time(),
            session_id=session_id,
            result_queue=q,
        )

        bus.publish_sync(
            "agent.SPAWNED",
            {"pid": pid, "skill_name": skill_name, "session_id": session_id, "context": context, "permissions": permissions, "sandbox_dir": str(sandbox_dir)},
            sender="AgentLifecycleManager",
        )
        return pid

    async def use_and_kill(
        self,
        skill_name: str,
        task: str,
        timeout: Optional[float] = None,
        user_id: str = "anon",
    ) -> Dict[str, Any]:
        ctx_task = task
        ctx_extra: Dict[str, Any] = {}

        if isinstance(task, str):
            t = task.strip()
            if t.startswith("{") and t.endswith("}"):
                try:
                    obj = json.loads(t)
                    if isinstance(obj, dict):
                        ctx_extra = obj
                        ctx_task = str(obj.get("task", ""))
                except Exception:
                    pass

        # Preparar contexto con output_dir
        output_dir = str(self.data_dir / "output" / "Imagenes")
        context = {
            "task": ctx_task,
            "user_id": user_id,
            "timestamp": time.time(),
            "output_dir": output_dir,
            **ctx_extra
        }

        pid: Optional[int] = None
        session_id: Optional[str] = None

        await bus.publish(
            "user.SPEAK",
            {"message": f"🚀 Iniciando {skill_name}...", "priority": "normal"},
            sender="AgentLifecycleManager",
        )

        try:
            pid = self.spawn_skill(skill_name, context)
            agent = self.active_agents[pid]
            session_id = agent.session_id
            actual_timeout = timeout or agent.max_lifetime

            await bus.publish(
                "user.SPEAK",
                {"message": f"⏳ Ejecutando {skill_name}...", "priority": "low"},
                sender="AgentLifecycleManager",
            )

            result = await asyncio.wait_for(self._wait_for_result(pid, session_id), timeout=actual_timeout)
            self._kill_agent(pid)

            result_summary = str(result.get("result", ""))[:100]
            await bus.publish(
                "user.SPEAK",
                {"message": f"✅ {skill_name} completado: {result_summary}", "priority": "normal"},
                sender="AgentLifecycleManager",
            )

            return {
                "success": True,
                "result": result,
                "skill": skill_name,
                "session_id": session_id,
                "pid": pid,
                "duration": time.time() - agent.spawned_at,
            }

        except FileNotFoundError as e:
            sid = str(uuid.uuid4())

            async def _retry_cb():
                return await self.use_and_kill(skill_name, task, timeout=timeout, user_id=user_id)

            self._register_retry(sid, _retry_cb)
            await bus.publish(
                "agent.RESULT",
                {
                    "session_id": sid,
                    "skill": skill_name,
                    "error": str(e),
                    "success": False,
                    "timestamp": time.time(),
                },
                sender="AgentLifecycleManager",
            )
            await bus.publish(
                "skill.RETRY_AVAILABLE",
                {"session_id": sid, "skill": skill_name, "original_error": str(e), "timestamp": time.time()},
                sender="AgentLifecycleManager",
            )
            return {"success": False, "error": str(e), "skill": skill_name, "session_id": sid}

        except asyncio.TimeoutError:
            if pid is not None:
                self._force_kill(pid)

            if session_id:
                async def _retry_cb():
                    return await self.use_and_kill(skill_name, task, timeout=timeout, user_id=user_id)

                self._register_retry(session_id, _retry_cb)

            await bus.publish(
                "agent.RESULT",
                {
                    "session_id": session_id or str(uuid.uuid4()),
                    "skill": skill_name,
                    "error": f"Timeout ({timeout}s)",
                    "success": False,
                    "timestamp": time.time(),
                },
                sender="AgentLifecycleManager",
            )

            await bus.publish(
                "skill.RETRY_AVAILABLE",
                {"session_id": session_id or "", "skill": skill_name, "original_error": f"Timeout ({timeout}s)", "timestamp": time.time()},
                sender="AgentLifecycleManager",
            )

            await bus.publish(
                "user.SPEAK",
                {"message": f"⏱️ {skill_name} tomó demasiado tiempo (timeout).", "priority": "high"},
                sender="AgentLifecycleManager",
            )
            return {"success": False, "error": f"Timeout ({timeout}s)", "skill": skill_name, "pid": pid, "session_id": session_id}

        except Exception as e:
            if pid is not None:
                self._cleanup(pid)

            if session_id:
                async def _retry_cb():
                    return await self.use_and_kill(skill_name, task, timeout=timeout, user_id=user_id)

                self._register_retry(session_id, _retry_cb)

            await bus.publish(
                "agent.RESULT",
                {
                    "session_id": session_id or str(uuid.uuid4()),
                    "skill": skill_name,
                    "error": str(e),
                    "success": False,
                    "timestamp": time.time(),
                },
                sender="AgentLifecycleManager",
            )

            await bus.publish(
                "skill.RETRY_AVAILABLE",
                {"session_id": session_id or "", "skill": skill_name, "original_error": str(e), "timestamp": time.time()},
                sender="AgentLifecycleManager",
            )

            await bus.publish(
                "user.SPEAK",
                {"message": f"❌ {skill_name} falló: {str(e)[:50]}", "priority": "high"},
                sender="AgentLifecycleManager",
            )
            return {"success": False, "error": str(e), "skill": skill_name, "session_id": session_id}

    async def _wait_for_result(self, pid: int, session_id: str) -> Dict[str, Any]:
        start = time.time()
        q = self.active_agents[pid].result_queue

        while pid in self.active_agents:
            if q is not None:
                try:
                    while True:
                        msg = q.get_nowait()
                        if isinstance(msg, dict) and msg.get("session_id"):
                            self._results_buffer[msg["session_id"]] = msg
                            bus.publish_sync("agent.RESULT", msg, sender="AgentLifecycleManager")
                except Exception:
                    pass

            if session_id in self._results_buffer:
                return self._results_buffer.pop(session_id)

            if not self._is_process_alive(pid):
                if session_id in self._results_buffer:
                    return self._results_buffer.pop(session_id)
                raise RuntimeError("Proceso terminó sin resultado")

            await asyncio.sleep(0.05)
            if time.time() - start > 60:
                raise TimeoutError("Polling timeout")

        return {}

    def _is_process_alive(self, pid: int) -> bool:
        try:
            proc = psutil.Process(pid)
            return proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
        except psutil.NoSuchProcess:
            return False

    def _kill_agent(self, pid: int):
        if pid not in self.active_agents:
            return
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except psutil.TimeoutExpired:
                self._force_kill(pid)
                return
        except psutil.NoSuchProcess:
            pass
        except Exception as e:
            logger.error(f"Error killing agent {pid}: {e}")
        self._cleanup(pid)

    def _force_kill(self, pid: int):
        try:
            if os.name == "nt":
                psutil.Process(pid).kill()
            else:
                sigkill = getattr(signal, "SIGKILL", None)
                if sigkill is not None:
                    os.kill(pid, sigkill)
                else:
                    psutil.Process(pid).kill()
        except Exception:
            pass
        self._cleanup(pid)

    def _cleanup(self, pid: int):
        if pid in self.active_agents:
            agent = self.active_agents.pop(pid)
            try:
                if agent.result_queue is not None:
                    try:
                        agent.result_queue.close()
                    except Exception:
                        pass
            except Exception:
                pass
            bus.publish_sync(
                "agent.KILLED",
                {"pid": pid, "session_id": agent.session_id, "skill": agent.skill_name},
                sender="AgentLifecycleManager",
            )


def _wrapped_execute(skill_path, context, session_id, q, pythonpath_val, sandbox_dir=None):
    """Wrapper que setea PYTHONPATH y sandbox_dir antes de ejecutar la skill"""
    if pythonpath_val:
        import os
        os.environ['PYTHONPATH'] = pythonpath_val
    _execute_skill_wrapper(skill_path, context, session_id, q, sandbox_dir)


def _execute_skill_wrapper(skill_path: str, context: Dict[str, Any], session_id: str, result_queue, sandbox_dir: str = None):
    """
    Wrapper de ejecución de skills con sandbox de seguridad.
    Aplica las mismas protecciones que SkillSafetyGate en producción.
    """
    try:
        import builtins
        import types
        import os as _os
        
        logging.basicConfig(level=logging.INFO)
        skill_name = Path(skill_path).stem
        skill_dir = str(Path(skill_path).parent.resolve())
        
        # Usar sandbox_dir si se proporciona, de lo contrario usar skill_dir
        sandbox_base = sandbox_dir if sandbox_dir else skill_dir
        
        # ============ SANDBOX DE SEGURIDAD ============
        
        # 1. Filtrar variables de entorno sensibles (igual que SkillSafetyGate)
        sensitive_patterns = [
            "TOKEN", "KEY", "SECRET", "PASSWORD", "CREDENTIAL",
            "API_KEY", "PIN", "AUTH", "PRIVATE"
        ]
        
        keep_safe = {"PATH", "TEMP", "TMP", "SystemRoot", "WINDIR", "USERPROFILE", "HOMEPATH"}
        
        for k in list(_os.environ.keys()):
            upper_k = k.upper()
            is_sensitive = any(s in upper_k for s in sensitive_patterns)
            if k not in keep_safe or is_sensitive:
                try:
                    _os.environ.pop(k, None)
                except:
                    pass
        
        # 2. Bloquear módulos peligrosos y redirigir rutas output/
        blocked_modules = {
            "keyring", "getpass", "ctypes", "subprocess",
            "importlib", "inspect", "asyncio.subprocess"
        }
        
        real_import = builtins.__import__
        
        def sandboxed_import(name, *args, **kwargs):
            base_module = name.split('.')[0]
            if base_module in blocked_modules:
                raise ImportError(f"Módulo '{name}' bloqueado por seguridad")
            return real_import(name, *args, **kwargs)
        
        builtins.__import__ = sandboxed_import
        
        # 2.5 Redirigir automáticamente rutas 'output/' al directorio output del sandbox
        real_open = builtins.open
        sandbox_output_path = Path(sandbox_base) / "output"
        
        def sandboxed_open(file, mode="r", *args, **kwargs):
            # Si el archivo es una ruta relativa que empieza con 'output/', redirigir
            if isinstance(file, str):
                if file.startswith('output/') or file.startswith('output\\'):
                    # Reemplazar 'output/' con la ruta absoluta del sandbox output
                    relative_path = file[7:]  # Quitar 'output/' o 'output\'
                    file = str(sandbox_output_path / relative_path)
            return real_open(file, mode, *args, **kwargs)
        
        builtins.open = sandboxed_open
        
        # 3. Bloquear socket y network si no tiene permiso
        permissions = context.get("permissions", [])
        allow_network = "network" in permissions or "credentials" in permissions
        if not allow_network:
            blocked_modules.add("socket")
        
        if not allow_network:
            try:
                blocked_socket = types.ModuleType("socket")
                class _BlockedSock:
                    def __init__(self, *a, **kw):
                        raise PermissionError("Acceso a red bloqueado")
                blocked_socket.socket = _BlockedSock
                sys.modules["socket"] = blocked_socket
            except:
                pass
        
        # 4. Integrar CredentialVault si hay credenciales temporales
        credential_session = context.get("credential_session")
        user_id = context.get("user_id", "unknown")
        if credential_session and "credentials" in permissions:
            try:
                from core.SkillCredentialVault import credential_vault
                creds = credential_vault.get_credentials(credential_session, skill_name, user_id)
                if creds:
                    context["credentials"] = creds
            except Exception as e:
                logger.error(f"Error recuperando credenciales: {e}")
        
        # 4.5 Integrar API keys desde el contexto (para skills con permiso 'network')
        if "network" in permissions or "credentials" in permissions:
            api_keys = context.get("api_keys", {})
            if api_keys:
                # Inyectar API keys como variables de entorno temporales
                for provider, key in api_keys.items():
                    env_var_name = f"{provider.upper()}_API_KEY"
                    _os.environ[env_var_name] = key
                    logger.info(f"API key para {provider} configurada en entorno")
                # También pasarlas al contexto para acceso directo
                context["api_keys"] = api_keys
        
        # 5. Configurar sys.path
        original_syspath = sys.path.copy()
        site_packages = [p for p in sys.path if 'site-packages' in p or 'dist-packages' in p or 'lib' in p.lower()]
        try:
            import site
            user_site = site.getusersitepackages()
            if user_site and user_site not in site_packages:
                site_packages.append(user_site)
        except Exception:
            pass
        sys.path = [sandbox_base] + site_packages
        
        # NOTA: El sandbox de archivos se eliminó para permitir que PIL y otras
        # librerías trabajen correctamente. La seguridad se mantiene mediante:
        # - Bloqueo de módulos peligrosos
        # - Bloqueo de red (si no tiene permiso)
        # - Filtrado de variables de entorno
        
        # Cambiar working directory al sandbox
        original_cwd = _os.getcwd()
        try:
            _os.chdir(sandbox_base)
        except Exception:
            pass
        
        # ============ EJECUCIÓN DE LA SKILL ============
        
        spec = importlib.util.spec_from_file_location(f"skill_{skill_name}", skill_path)
        if not spec or not spec.loader:
            raise ImportError(f"No se pudo cargar spec para {skill_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module.__name__] = module
        spec.loader.exec_module(module)

        if not hasattr(module, "execute"):
            raise AttributeError(f"Skill {skill_name} no tiene función 'execute'")

        execute_func = module.execute
        if asyncio.iscoroutinefunction(execute_func):
            result = asyncio.run(execute_func(context))
        else:
            result = execute_func(context)

        payload = {
            "session_id": session_id,
            "skill": skill_name,
            "result": result,
            "success": True,
            "timestamp": time.time(),
        }

        try:
            result_queue.put(payload)
        except Exception:
            pass

        try:
            bus.publish_sync("agent.RESULT", payload, sender="SkillWorker")
        except Exception:
            pass
        
        # ============ LIMPIEZA ============
        
        # Restaurar working directory
        try:
            _os.chdir(original_cwd)
        except Exception:
            pass
        
        # 6. Liberar credenciales
        if credential_session:
            try:
                from core.SkillCredentialVault import credential_vault
                credential_vault.release_credentials(credential_session)
                logger.info(f"Credenciales liberadas para skill {skill_name}")
            except Exception as e:
                logger.error(f"Error liberando credenciales: {e}")
        
        # 7. Limpiar credenciales de memoria
        if "credentials" in context:
            try:
                for key in list(context["credentials"].keys()):
                    context["credentials"][key] = "0" * len(context["credentials"][key])
                context["credentials"].clear()
                del context["credentials"]
            except:
                pass
        
        # 8. Restaurar sys.path
        sys.path = original_syspath
        
        # 9. Copiar archivos generados del sandbox al directorio de salida permanente
        if sandbox_dir and (sandbox_dir / "output").exists():
            try:
                sandbox_output = sandbox_dir / "output"
                # Usar output_dir del contexto o default relativo al skill_dir
                final_output = Path(context.get("output_dir", str(Path(skill_dir).parent / "output")))
                final_output.mkdir(parents=True, exist_ok=True)
                
                # Copiar todos los archivos del sandbox output al directorio final
                for item in sandbox_output.iterdir():
                    if item.is_file():
                        dest = final_output / item.name
                        shutil.copy2(item, dest)
                        logger.info(f"Archivo copiado: {item.name} -> {dest}")
            except Exception as e:
                logger.error(f"Error copiando archivos del sandbox: {e}")
        
        # 10. Limpiar sandbox temporal (solo si es un dir temporal)
        if sandbox_dir and sandbox_dir != skill_dir:
            try:
                shutil.rmtree(sandbox_dir, ignore_errors=True)
                logger.info(f"Sandbox limpiado: {sandbox_dir}")
            except Exception as e:
                logger.error(f"Error limpiando sandbox: {e}")
        
        # 11. Forzar garbage collection
        try:
            import gc
            gc.collect()
        except:
            pass

    except Exception as e:
        payload = {
            "session_id": session_id,
            "skill": Path(skill_path).stem if 'skill_path' in locals() else "unknown",
            "error": str(e),
            "success": False,
            "timestamp": time.time(),
        }

        try:
            result_queue.put(payload)
        except Exception:
            pass

        try:
            bus.publish_sync("agent.RESULT", payload, sender="SkillWorker")
        except Exception:
            pass


agent_manager = AgentLifecycleManager()
