import ast
import json
import multiprocessing as mp
import os
import sys
import time
import zipfile
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class SafetyReport:
    ok: bool
    skill_id: str
    name: str
    version: str
    permissions: List[str]
    reasons: List[str]


_DEFAULT_FORBIDDEN_MODULES = {
    "ctypes",
    "socket",
    "importlib",
    "inspect",
    "asyncio.subprocess",
    "subprocess",
    "shutil",
    "win32api",
    "win32con",
    "win32gui",
    "pyautogui",
    "keyring",  # Prevenir acceso a almacenes de contraseñas
    "getpass",  # Prevenir lectura interactiva de contraseñas
}

# Variables de entorno sensibles que las skills NO deben acceder
_SENSITIVE_ENV_VARS = {
    "TELEGRAM_TOKEN", "TELEGRAM_BOT_TOKEN", "TELEGRAM_API_KEY",
    "WHATSAPP_TOKEN", "WHATSAPP_ACCESS_TOKEN",
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GROQ_API_KEY", "GEMINI_API_KEY",
    "MIIA_ADMIN_PIN", "ADMIN_PASSWORD", "SECRET_KEY",
    "DATABASE_URL", "DB_PASSWORD", "REDIS_PASSWORD",
    "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",
    "GITHUB_TOKEN", "GITLAB_TOKEN",
    "PASSWORD", "SECRET", "PRIVATE_KEY", "API_SECRET",
    "FACEBOOK_PASSWORD", "INSTAGRAM_PASSWORD", "TWITTER_PASSWORD",
    "EMAIL_PASSWORD", "SMTP_PASSWORD", "IMAP_PASSWORD"
}

_DEFAULT_FORBIDDEN_CALLS = {
    "eval",
    "exec",
    "compile",
    "__import__",
}

_NETWORK_MODULES = {"requests", "httpx", "urllib", "urllib3"}


def _env_int(name: str, default: int) -> int:
    try:
        v = str(os.environ.get(name, str(default)) or str(default)).strip()
        return int(v)
    except Exception:
        return default


def _safe_zip_members(z: zipfile.ZipFile) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    max_files = _env_int("MIIA_SKILL_ZIP_MAX_FILES", 60)
    max_uncompressed_mb = _env_int("MIIA_SKILL_ZIP_MAX_UNCOMPRESSED_MB", 40)
    max_uncompressed = max_uncompressed_mb * 1024 * 1024

    infos = z.infolist()
    if len(infos) > max_files:
        reasons.append(f"ZIP excede máximo de archivos ({len(infos)} > {max_files})")

    total = 0
    for info in infos:
        # seguridad de path traversal
        name = (info.filename or "").replace("\\", "/")
        if not name or name.endswith("/"):
            continue
        if name.startswith("/") or re.match(r"^[A-Za-z]:/", name):
            reasons.append(f"Ruta absoluta en ZIP no permitida: {name}")
            continue
        if ".." in name.split("/"):
            reasons.append(f"Path traversal en ZIP no permitido: {name}")
            continue

        try:
            total += int(getattr(info, "file_size", 0) or 0)
        except Exception:
            pass

    if total > max_uncompressed:
        reasons.append(
            f"ZIP excede tamaño descomprimido máximo ({total / (1024 * 1024):.1f}MB > {max_uncompressed_mb}MB)"
        )

    return (len(reasons) == 0), reasons


def _read_existing_safety_report(extracted_dir: Path) -> Dict[str, Any]:
    p = extracted_dir / "safety_report.json"
    if not p.exists():
        return {}
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def _slugify(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9_\- ]+", "", s)
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"_+", "_", s)
    s = s.strip("_-")
    return s or "user_skill"


def _parse_simple_yaml(text: str) -> Dict[str, Any]:
    # YAML muy básico (sin dependencias) para público.
    # Soporta:
    # key: value
    # permissions:
    #  - fs_read
    obj: Dict[str, Any] = {}
    current_key: Optional[str] = None
    for raw in (text or "").splitlines():
        line = raw.rstrip("\n")
        if not line.strip() or line.strip().startswith("#"):
            continue
        if re.match(r"^[A-Za-z0-9_\-]+\s*:\s*.*$", line) and not line.lstrip().startswith("-"):
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip()
            current_key = k
            if v == "":
                obj[k] = []
            else:
                obj[k] = v.strip('"')
            continue

        if line.lstrip().startswith("-") and current_key:
            item = line.lstrip()[1:].strip().strip('"')
            if not isinstance(obj.get(current_key), list):
                obj[current_key] = []
            if item:
                obj[current_key].append(item)
            continue

    return obj


def _load_skill_yaml(extracted_dir: Path) -> Tuple[str, str, List[str], List[str]]:
    y = extracted_dir / "skill.yaml"
    if not y.exists():
        return "", "", [], []
    try:
        data = _parse_simple_yaml(y.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    name = str(data.get("name") or "").strip() or "Skill"
    skill_id = _slugify(str(data.get("id") or "") or name)
    perms = data.get("permissions")
    permissions: List[str] = []
    if isinstance(perms, list):
        permissions = [str(p).strip() for p in perms if str(p).strip()]
    message = str(data.get("message") or data.get("description") or "")
    return skill_id, name, permissions, [message] if message else []


def _detect_entrypoint(extracted_dir: Path) -> Tuple[Optional[Path], Optional[str]]:
    # Orden recomendado:
    # 1) skill.py:execute
    # 2) main.py:main
    # 3) cualquier .py con run/main/handle/process(context)
    preferred = [
        (extracted_dir / "skill.py", "execute"),
        (extracted_dir / "main.py", "main"),
    ]
    for p, fn in preferred:
        if p.exists():
            try:
                tree = ast.parse(p.read_text(encoding="utf-8"))
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name == fn and len(node.args.args) >= 1:
                        return p, fn
            except Exception:
                pass

    candidates = []
    for p in extracted_dir.rglob("*.py"):
        if p.name.startswith("_"):
            continue
        if p.name.lower() in {"__init__.py"}:
            continue
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in {"run", "main", "handle", "process", "execute"}:
                if len(node.args.args) >= 1:
                    candidates.append((p, node.name))

    if candidates:
        # Heurística simple: priorizar main.py y luego nombres más comunes
        candidates.sort(key=lambda t: (0 if t[0].name.lower() == "main.py" else 1, {"execute": 0, "main": 1, "run": 2, "handle": 3, "process": 4}.get(t[1], 9)))
        return candidates[0][0], candidates[0][1]

    return None, None


def _write_manifest(extracted_dir: Path, skill_id: str, name: str, version: str, permissions: List[str]) -> None:
    manifest_path = extracted_dir / "manifest.json"
    obj = {
        "id": skill_id,
        "name": name,
        "version": version,
        "permissions": permissions,
    }
    manifest_path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_declarative_skill(extracted_dir: Path, message: str) -> None:
    skill_path = extracted_dir / "skill.py"
    # Skill declarativa mínima: devuelve mensaje. (Seguro para público)
    skill_path.write_text(
        "def execute(context):\n"
        "    msg = " + json.dumps(message or "OK", ensure_ascii=False) + "\n"
        "    return {\"success\": True, \"message\": msg, \"kind\": \"declarative\"}\n",
        encoding="utf-8",
    )


def _write_wrapper_skill(extracted_dir: Path, entry_rel: str, func_name: str) -> None:
    # Wrapper: carga el archivo destino por exec y llama a la función detectada.
    skill_path = extracted_dir / "skill.py"
    skill_path.write_text(
        "import time\n"
        "from pathlib import Path\n\n"
        "def execute(context):\n"
        "    base = Path(__file__).parent\n"
        f"    target = (base / {json.dumps(entry_rel)}).resolve()\n"
        "    ns = {\"__file__\": str(target)}\n"
        "    code = target.read_text(encoding=\"utf-8\")\n"
        "    exec(compile(code, str(target), \"exec\"), ns, ns)\n"
        f"    fn = ns.get({json.dumps(func_name)})\n"
        "    if not callable(fn):\n"
        f"        raise RuntimeError(\"No se encontró función entrypoint: {func_name}\")\n"
        "    out = fn(context)\n"
        "    return out\n",
        encoding="utf-8",
    )


def _read_manifest(extracted_dir: Path) -> Tuple[str, str, str, List[str], List[str]]:
    manifest_path = extracted_dir / "manifest.json"
    if not manifest_path.exists():
        return "", "", "", [], ["Falta manifest.json"]

    try:
        obj = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        return "", "", "", [], [f"manifest.json inválido: {e}"]

    skill_id = str(obj.get("id") or "").strip()
    name = str(obj.get("name") or "").strip()
    version = str(obj.get("version") or "").strip()
    perms = obj.get("permissions")
    permissions: List[str] = []
    if isinstance(perms, list):
        permissions = [str(p).strip() for p in perms if str(p).strip()]

    reasons: List[str] = []
    if not skill_id:
        reasons.append("manifest.json: falta id")
    if not name:
        reasons.append("manifest.json: falta name")
    if not version:
        reasons.append("manifest.json: falta version")

    return skill_id, name, version, permissions, reasons


def _ast_check(code: str, permissions: List[str]) -> List[str]:
    reasons: List[str] = []
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        # Formato claro de error de sintaxis con ubicación exacta
        line_num = e.lineno if e.lineno else "?"
        col_num = e.offset if e.offset else "?"
        error_msg = f"Error de sintaxis en línea {line_num}, columna {col_num}: {e.msg}"
        return [error_msg]
    except Exception as e:
        return [f"Python inválido: {e}"]

    requested_network = "network" in {p.lower() for p in permissions}

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mod = ""
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = (alias.name or "").split(".")[0]
                    if mod in _DEFAULT_FORBIDDEN_MODULES:
                        reasons.append(f"Import prohibido: {mod}")
                    if mod in _NETWORK_MODULES and not requested_network:
                        reasons.append(f"Import de red requiere permiso network: {mod}")
            else:
                mod = (node.module or "").split(".")[0]
                if mod in _DEFAULT_FORBIDDEN_MODULES:
                    reasons.append(f"Import prohibido: {mod}")
                if mod in _NETWORK_MODULES and not requested_network:
                    reasons.append(f"Import de red requiere permiso network: {mod}")

        if isinstance(node, ast.Call):
            # llamadas directas a eval/exec/compile
            if isinstance(node.func, ast.Name) and node.func.id in _DEFAULT_FORBIDDEN_CALLS:
                reasons.append(f"Llamada prohibida: {node.func.id}()")

            # os.system / subprocess.Popen etc (heurístico)
            if isinstance(node.func, ast.Attribute):
                attr = node.func.attr
                if attr in {"system", "popen", "Popen", "run", "call"}:
                    reasons.append(f"Posible ejecución de comandos detectada: .{attr}()")

    return reasons


def _sandbox_worker(extracted_dir: str, sandbox_dir: str, q, timeout_seconds: float, allow_network: bool):
    """
    SANDBOX WORKER - Solo validación de seguridad, NO ejecución de código.
    El sandbox verifica que el código sea seguro mediante análisis AST.
    La ejecución real ocurre en AgentLifecycleManager.
    """
    start = time.time()
    try:
        extracted = Path(extracted_dir)
        skill_path = extracted / "skill.py"
        if not skill_path.exists():
            raise RuntimeError("Falta skill.py")

        # Leer código para validación AST
        try:
            code_utf8 = skill_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                raw = skill_path.read_bytes()
                code_utf8 = raw.decode('latin-1')
            except Exception:
                code_utf8 = skill_path.read_text(encoding="utf-8", errors='replace')
        
        # Verificar que tenga función execute (sintaxis, no ejecución)
        try:
            tree = ast.parse(code_utf8)
            has_execute = any(isinstance(node, ast.FunctionDef) and node.name == "execute" for node in ast.walk(tree))
            if not has_execute:
                raise RuntimeError("skill.py debe exponer execute(context)")
        except SyntaxError as e:
            # Error de sintaxis específico
            line_num = e.lineno if e.lineno else "?"
            col_num = e.offset if e.offset else "?"
            raise RuntimeError(f"Error de sintaxis en línea {line_num}, columna {col_num}: {e.msg}")
        
        # Validación de seguridad AST
        from core.SkillSafetyGate import _ast_check
        permissions = ["fs_read", "network"] if allow_network else ["fs_read"]
        reasons = _ast_check(code_utf8, permissions)
        
        if reasons:
            # Separar errores de sintaxis de errores de seguridad
            syntax_errors = [r for r in reasons if r.startswith("Error de sintaxis") or r.startswith("Python inválido")]
            if syntax_errors:
                raise RuntimeError(f"Error de sintaxis: {syntax_errors[0]}")
            else:
                # Es un error de seguridad
                security_issues = "; ".join(reasons)
                raise RuntimeError(f"Violación de seguridad: {security_issues}")
        
        q.put({"ok": True, "result": {"validated": True}})
        
    except Exception as e:
        q.put({"ok": False, "error": str(e)})


class SkillSafetyGate:
    def __init__(self):
        pass

    def prepare_extracted_dir(self, extracted_dir: Path) -> SafetyReport:
        reasons: List[str] = []

        # 1) Preferir formato público: skill.yaml
        y_id, y_name, y_perms, y_msgs = _load_skill_yaml(extracted_dir)
        if y_id:
            skill_id = y_id
            name = y_name
            version = "1.0"
            permissions = y_perms

            if not (extracted_dir / "manifest.json").exists():
                try:
                    _write_manifest(extracted_dir, skill_id, name, version, permissions)
                except Exception as e:
                    reasons.append(f"No se pudo escribir manifest.json: {e}")

            if not (extracted_dir / "skill.py").exists():
                try:
                    _write_declarative_skill(extracted_dir, y_msgs[0] if y_msgs else "OK")
                except Exception as e:
                    reasons.append(f"No se pudo escribir skill.py declarativa: {e}")

            ok = len(reasons) == 0
            return SafetyReport(ok, skill_id, name, version, permissions, reasons)

        # 2) Modo avanzado: auto-detect entrypoint + generar wrapper si hace falta
        entry_file, entry_fn = _detect_entrypoint(extracted_dir)
        if not entry_file or not entry_fn:
            return SafetyReport(False, "", "", "", [], ["No pude detectar entrypoint. Recomendado: incluir skill.yaml o main.py con main(context)"])

        # manifest: si falta, autogenerar
        manifest_path = extracted_dir / "manifest.json"
        if manifest_path.exists():
            skill_id, name, version, permissions, manifest_reasons = _read_manifest(extracted_dir)
            reasons.extend(manifest_reasons)
        else:
            name = entry_file.stem
            skill_id = _slugify(name)
            version = "1.0"
            permissions = []
            try:
                _write_manifest(extracted_dir, skill_id, name, version, permissions)
            except Exception as e:
                reasons.append(f"No se pudo escribir manifest.json: {e}")

        skill_path = extracted_dir / "skill.py"
        if skill_path.exists():
            # Si ya existe, se espera que exponga execute. Si no, lo envolvemos.
            try:
                tree = ast.parse(skill_path.read_text(encoding="utf-8"))
                has_execute = any(isinstance(n, ast.FunctionDef) and n.name == "execute" for n in ast.walk(tree))
            except Exception:
                has_execute = False

            if not has_execute:
                try:
                    rel = str(entry_file.relative_to(extracted_dir))
                    _write_wrapper_skill(extracted_dir, rel, entry_fn)
                except Exception as e:
                    reasons.append(f"No se pudo generar wrapper execute(): {e}")
        else:
            try:
                rel = str(entry_file.relative_to(extracted_dir))
                _write_wrapper_skill(extracted_dir, rel, entry_fn)
            except Exception as e:
                reasons.append(f"No se pudo generar skill.py wrapper: {e}")

        ok = len(reasons) == 0
        return SafetyReport(ok, skill_id, name, version, permissions, reasons)

    def validate_zip(self, zip_path: Path) -> SafetyReport:
        rep, _ = self.validate_zip_detailed(zip_path)
        return rep

    def validate_zip_detailed(self, zip_path: Path) -> Tuple[SafetyReport, Optional[Path]]:
        reasons: List[str] = []

        if not zip_path.exists() or zip_path.suffix.lower() != ".zip":
            return SafetyReport(False, "", "", "", [], ["Archivo no es .zip"]), None

        max_zip_mb = _env_int("MIIA_SKILL_ZIP_MAX_MB", 15)
        try:
            size = zip_path.stat().st_size
            if size > max_zip_mb * 1024 * 1024:
                return (
                    SafetyReport(
                        False,
                        "",
                        "",
                        "",
                        [],
                        [f"ZIP excede tamaño máximo ({size / (1024*1024):.1f}MB > {max_zip_mb}MB)"],
                    ),
                    None,
                )
        except Exception:
            pass

        tmp_root = Path(os.environ.get("MIIA_SKILL_SIM_TMP", ""))
        if not str(tmp_root).strip():
            tmp_root = Path(os.getenv("TEMP", "."))
        extract_dir = tmp_root / "miia_skill_sim" / f"extract_{time.time_ns()}"
        sandbox_dir = tmp_root / "miia_skill_sim" / f"sandbox_{time.time_ns()}"
        extract_dir.mkdir(parents=True, exist_ok=True)
        sandbox_dir.mkdir(parents=True, exist_ok=True)
        
        # Crear directorio output básico para que skills puedan guardar archivos
        # Esto es preparación de entorno, NO modificación de código
        (sandbox_dir / "output").mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_path, "r") as z:
                ok_members, member_reasons = _safe_zip_members(z)
                if not ok_members:
                    return SafetyReport(False, "", "", "", [], member_reasons), None
                z.extractall(extract_dir)
        except Exception as e:
            return SafetyReport(False, "", "", "", [], [f"No se pudo extraer zip: {e}"]), None

        prep = self.prepare_extracted_dir(extract_dir)
        if not prep.ok:
            return prep, extract_dir

        rep = self.validate_extracted_dir(extract_dir, sandbox_dir=sandbox_dir)
        return rep, extract_dir

    def validate_extracted_dir(self, extracted_dir: Path, sandbox_dir: Optional[Path] = None) -> SafetyReport:
        reasons: List[str] = []

        if sandbox_dir is None:
            tmp_root = Path(os.environ.get("MIIA_SKILL_SIM_TMP", ""))
            if not str(tmp_root).strip():
                tmp_root = Path(os.getenv("TEMP", "."))
            sandbox_dir = tmp_root / "miia_skill_sim" / f"sandbox_{time.time_ns()}"
            sandbox_dir.mkdir(parents=True, exist_ok=True)

        skill_id, name, version, permissions, manifest_reasons = _read_manifest(extracted_dir)
        reasons.extend(manifest_reasons)

        skill_py = extracted_dir / "skill.py"
        if not skill_py.exists():
            reasons.append("Falta skill.py")
            return SafetyReport(False, skill_id, name, version, permissions, reasons)

        try:
            code_utf8 = skill_py.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Fallback: leer como latin-1 (acepta cualquier byte) y normalizar a UTF-8
            try:
                raw = skill_py.read_bytes()
                code_utf8 = raw.decode('latin-1')
            except Exception:
                code_utf8 = skill_py.read_text(encoding="utf-8", errors='replace')
        code = code_utf8

        reasons.extend(_ast_check(code, permissions))

        if reasons:
            rep = SafetyReport(False, skill_id, name, version, permissions, reasons)
            try:
                existing = _read_existing_safety_report(extracted_dir)
                existing.update(
                    {
                        "skill_id": rep.skill_id,
                        "name": rep.name,
                        "version": rep.version,
                        "permissions": rep.permissions,
                        "validated_at": time.time(),
                        "ok": False,
                        "reasons": rep.reasons,
                        "limits": {
                            "zip_max_mb": _env_int("MIIA_SKILL_ZIP_MAX_MB", 15),
                            "zip_max_files": _env_int("MIIA_SKILL_ZIP_MAX_FILES", 60),
                            "zip_max_uncompressed_mb": _env_int("MIIA_SKILL_ZIP_MAX_UNCOMPRESSED_MB", 40),
                            "sim_timeout": float(os.environ.get("MIIA_SKILL_SIM_TIMEOUT", "4") or "4"),
                        },
                    }
                )
                (extracted_dir / "safety_report.json").write_text(
                    json.dumps(existing, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            except Exception:
                pass
            return rep

        allow_network = "network" in {p.lower() for p in (permissions or [])}

        ctx = mp.get_context("spawn")
        q = ctx.Queue()
        t = float(os.environ.get("MIIA_SKILL_SIM_TIMEOUT", "4") or "4")
        p = ctx.Process(
            target=_sandbox_worker,
            args=(str(extracted_dir), str(sandbox_dir), q, t, allow_network),
            name=f"skill-sim-{skill_id or 'unknown'}",
        )
        p.start()
        p.join(timeout=t + 1.0)

        if p.is_alive():
            try:
                p.kill()
            except Exception:
                pass
            rep = SafetyReport(False, skill_id, name, version, permissions, ["Timeout en simulador"])
            try:
                existing = _read_existing_safety_report(extracted_dir)
                existing.update(
                    {
                        "skill_id": rep.skill_id,
                        "name": rep.name,
                        "version": rep.version,
                        "permissions": rep.permissions,
                        "validated_at": time.time(),
                        "ok": False,
                        "reasons": rep.reasons,
                    }
                )
                (extracted_dir / "safety_report.json").write_text(
                    json.dumps(existing, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            except Exception:
                pass
            return rep

        try:
            msg = q.get_nowait()
        except Exception:
            msg = {"ok": False, "error": "Simulador no devolvió resultado"}

        if not isinstance(msg, dict) or not msg.get("ok"):
            rep = SafetyReport(False, skill_id, name, version, permissions, [str((msg or {}).get("error") or "Falló simulador")])
            try:
                existing = _read_existing_safety_report(extracted_dir)
                existing.update(
                    {
                        "skill_id": rep.skill_id,
                        "name": rep.name,
                        "version": rep.version,
                        "permissions": rep.permissions,
                        "validated_at": time.time(),
                        "ok": False,
                        "reasons": rep.reasons,
                    }
                )
                (extracted_dir / "safety_report.json").write_text(
                    json.dumps(existing, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            except Exception:
                pass
            return rep

        rep = SafetyReport(True, skill_id, name, version, permissions, [])
        try:
            existing = _read_existing_safety_report(extracted_dir)
            if "prepared_at" not in existing:
                existing["prepared_at"] = time.time()
            existing.update(
                {
                    "skill_id": rep.skill_id,
                    "name": rep.name,
                    "version": rep.version,
                    "permissions": rep.permissions,
                    "validated_at": time.time(),
                    "ok": True,
                    "reasons": [],
                    "limits": {
                        "zip_max_mb": _env_int("MIIA_SKILL_ZIP_MAX_MB", 15),
                        "zip_max_files": _env_int("MIIA_SKILL_ZIP_MAX_FILES", 60),
                        "zip_max_uncompressed_mb": _env_int("MIIA_SKILL_ZIP_MAX_UNCOMPRESSED_MB", 40),
                        "sim_timeout": float(os.environ.get("MIIA_SKILL_SIM_TIMEOUT", "4") or "4"),
                    },
                }
            )
            (extracted_dir / "safety_report.json").write_text(
                json.dumps(existing, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass
        return rep
