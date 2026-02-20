import json
import os
import shutil
import time
import zipfile
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from core.SkillSafetyGate import SafetyReport, SkillSafetyGate


@dataclass
class VaultItem:
    zip_path: Path
    staged_at: float


class SkillVault:
    """
    SkillVault - Gestión segura de skills con estructura de carpetas clara:
    
    ESTRUCTURA:
    data/skills_vault/
    ├── external_staging/    ← Skills externas en evaluación (descargadas)
    ├── external_live/       ← Skills externas aprobadas
    ├── external_quarantine/ ← Skills externas rechazadas/maliciosas
    ├── staging/             ← Skills internas en desarrollo
    ├── live/                ← Skills internas aprobadas
    └── quarantine/          ← Skills internas rechazadas
    
    data/skills_user/        ← Skills disponibles para el sistema
    """
    def __init__(self):
        # Usar ruta relativa al directorio de MININA
        minina_root = Path(__file__).parent.parent
        self.data_dir = minina_root / "data"
        
        # Vault principal
        self.base_dir = self.data_dir / "skills_vault"
        
        # Carpetas para skills EXTERNAS (no creadas por MININA)
        self.external_staging_dir = self.base_dir / "external_staging"
        self.external_live_dir = self.base_dir / "external_live"
        self.external_quarantine_dir = self.base_dir / "external_quarantine"
        
        # Carpetas para skills INTERNAS (creadas por MININA)
        self.staging_dir = self.base_dir / "staging"
        self.live_dir = self.base_dir / "live"
        self.quarantine_dir = self.base_dir / "quarantine"
        
        # Skills disponibles para el sistema
        self.user_skills_dir = self.data_dir / "skills_user"
        
        # Output para archivos generados
        self.output_dir = self.data_dir / "output"

        # Crear todos los directorios
        self._ensure_directories()

        # Gate de seguridad
        self.gate = SkillSafetyGate()
    
    def _ensure_directories(self):
        """Crear estructura de carpetas si no existen"""
        dirs = [
            self.external_staging_dir,
            self.external_live_dir,
            self.external_quarantine_dir,
            self.staging_dir,
            self.live_dir,
            self.quarantine_dir,
            self.user_skills_dir,
            self.output_dir,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def stage_external_zip(self, zip_path: Path) -> VaultItem:
        """Stage a skill externa (no creada por MININA) para evaluación"""
        import time
        out = self.external_staging_dir / f"ext_{int(time.time())}_{zip_path.name}"
        shutil.copy2(zip_path, out)
        return VaultItem(zip_path=out, staged_at=time.time())
    
    def approve_external_skill(self, skill_id: str) -> dict:
        """Aprobar una skill externa y moverla a live"""
        try:
            # Buscar en external_staging
            staged = None
            for f in self.external_staging_dir.glob("*.zip"):
                if skill_id in f.name:
                    staged = f
                    break
            
            if not staged or not staged.exists():
                return {"success": False, "error": "Skill no encontrada en staging externo"}
            
            # Validar
            report, extracted_dir = self.gate.validate_zip_detailed(staged)
            if not report.ok:
                # Mover a cuarentena externa
                qdir = self._quarantine_external(staged, report)
                return {"success": False, "error": f"Validación fallida. En cuarentena: {qdir}", "report": report.to_dict()}
            
            # Mover a external_live
            live_dir = self.external_live_dir / report.skill_id
            if live_dir.exists():
                shutil.rmtree(live_dir, ignore_errors=True)
            
            if extracted_dir and extracted_dir.exists():
                shutil.move(str(extracted_dir), str(live_dir))
            
            # Copiar a skills_user
            src_skill = live_dir / "skill.py"
            if src_skill.exists():
                dst_module = self.user_skills_dir / f"{report.skill_id}.py"
                shutil.copy2(src_skill, dst_module)
            
            # Limpiar staging
            try:
                staged.unlink()
            except:
                pass
            
            return {
                "success": True,
                "skill_id": report.skill_id,
                "message": f"Skill externa '{report.name}' aprobada e instalada",
                "location": str(live_dir)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _quarantine_external(self, staged_zip: Path, report: SafetyReport) -> Path:
        """Poner skill externa en cuarentena"""
        sid = (report.skill_id or "unknown").strip() or "unknown"
        ts = time.strftime("%Y%m%d_%H%M%S")
        qdir = self.external_quarantine_dir / sid / ts
        qdir.mkdir(parents=True, exist_ok=True)
        
        try:
            shutil.copy2(staged_zip, qdir / "original.zip")
        except:
            pass
        
        try:
            (qdir / "safety_report.json").write_text(
                json.dumps({
                    "skill_id": report.skill_id,
                    "name": report.name,
                    "ok": report.ok,
                    "reasons": report.reasons,
                    "timestamp": time.time(),
                }, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except:
            pass
        
        try:
            staged_zip.unlink()
        except:
            pass
        
        return qdir
    
    def list_external_staging(self) -> list:
        """Listar skills externas en evaluación"""
        skills = []
        try:
            for f in self.external_staging_dir.glob("*.zip"):
                try:
                    stat = f.stat()
                    skills.append({
                        "filename": f.name,
                        "path": str(f),
                        "size": stat.st_size,
                        "added_at": stat.st_mtime,
                    })
                except:
                    pass
        except Exception as e:
            print(f"Error listando staging externo: {e}")
        return sorted(skills, key=lambda x: x.get("added_at", 0), reverse=True)
    
    def list_external_quarantine(self) -> list:
        """Listar skills externas en cuarentena"""
        skills = []
        try:
            for skill_dir in self.external_quarantine_dir.iterdir():
                if skill_dir.is_dir():
                    for ts_dir in skill_dir.iterdir():
                        if ts_dir.is_dir():
                            report_file = ts_dir / "safety_report.json"
                            info = {
                                "skill_id": skill_dir.name,
                                "timestamp": ts_dir.name,
                                "path": str(ts_dir),
                            }
                            if report_file.exists():
                                try:
                                    data = json.loads(report_file.read_text(encoding="utf-8"))
                                    info.update(data)
                                except:
                                    pass
                            skills.append(info)
        except Exception as e:
            print(f"Error listando cuarentena externa: {e}")
        return skills

    def stage_zip(self, zip_path: Path, chat_id: int) -> VaultItem:
        target = self.staging_dir / f"chat_{chat_id}"
        target.mkdir(parents=True, exist_ok=True)
        out = target / f"{int(time.time())}_{zip_path.name}"
        shutil.copy2(zip_path, out)
        return VaultItem(zip_path=out, staged_at=time.time())

    def _quarantine_attempt(
        self,
        skill_id: str,
        staged_zip: Optional[Path],
        extracted_dir: Optional[Path],
        report: SafetyReport,
    ) -> Path:
        sid = (skill_id or "unknown").strip() or "unknown"
        ts = time.strftime("%Y%m%d_%H%M%S")
        qdir = self.quarantine_dir / sid / ts
        qdir.mkdir(parents=True, exist_ok=True)

        if staged_zip is not None and staged_zip.exists():
            try:
                shutil.copy2(staged_zip, qdir / "original.zip")
            except Exception:
                pass
            try:
                staged_zip.unlink(missing_ok=True)  # type: ignore
            except Exception:
                pass

        if extracted_dir is not None and extracted_dir.exists() and extracted_dir.is_dir():
            try:
                shutil.copytree(extracted_dir, qdir / "extracted", dirs_exist_ok=True)
            except Exception:
                pass
            try:
                shutil.rmtree(extracted_dir, ignore_errors=True)
            except Exception:
                pass

        try:
            (qdir / "safety_report.json").write_text(
                json.dumps(
                    {
                        "skill_id": report.skill_id,
                        "name": report.name,
                        "version": report.version,
                        "permissions": report.permissions,
                        "ok": report.ok,
                        "reasons": report.reasons,
                        "timestamp": time.time(),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        except Exception:
            pass

        try:
            (qdir / "reasons.txt").write_text("\n".join(report.reasons or []), encoding="utf-8")
        except Exception:
            pass

        return qdir

    def validate_and_install(self, staged_zip: Path) -> Tuple[SafetyReport, Optional[Path]]:
        report, extracted_dir = self.gate.validate_zip_detailed(staged_zip)
        if not report.ok:
            qdir = self._quarantine_attempt(report.skill_id or "unknown", staged_zip=staged_zip, extracted_dir=extracted_dir, report=report)
            report.reasons = list(report.reasons) + [f"Cuarentena: {qdir}"]
            return report, None

        if extracted_dir is None or not extracted_dir.exists():
            rep = SafetyReport(False, report.skill_id, report.name, report.version, report.permissions, ["No se generó directorio extraído"]) 
            qdir = self._quarantine_attempt(report.skill_id or "unknown", staged_zip=staged_zip, extracted_dir=None, report=rep)
            rep.reasons = list(rep.reasons) + [f"Cuarentena: {qdir}"]
            return rep, None

        # Promover a live definitivo
        live_skill_dir = self.live_dir / report.skill_id
        if live_skill_dir.exists():
            shutil.rmtree(live_skill_dir, ignore_errors=True)
        try:
            shutil.move(str(extracted_dir), str(live_skill_dir))
        except Exception:
            shutil.copytree(extracted_dir, live_skill_dir, dirs_exist_ok=True)
            shutil.rmtree(extracted_dir, ignore_errors=True)

        src_skill = live_skill_dir / "skill.py"
        if not src_skill.exists():
            rep = SafetyReport(False, report.skill_id, report.name, report.version, report.permissions, ["No se generó skill.py"])
            qdir = self._quarantine_attempt(report.skill_id, staged_zip=staged_zip, extracted_dir=live_skill_dir, report=rep)
            rep.reasons = list(rep.reasons) + [f"Cuarentena: {qdir}"]
            return rep, None

        dst_module = self.user_skills_dir / f"{report.skill_id}.py"
        shutil.copy2(src_skill, dst_module)

        # limpiar staging
        try:
            staged_zip.unlink(missing_ok=True)  # type: ignore
        except Exception:
            pass

        return report, dst_module

    def install_from_prepared_dir(self, prepared_dir: Path) -> Tuple[SafetyReport, Optional[Path]]:
        report = self.gate.validate_extracted_dir(prepared_dir)
        if not report.ok:
            return report, None

        live_skill_dir = self.live_dir / report.skill_id
        if live_skill_dir.exists():
            shutil.rmtree(live_skill_dir, ignore_errors=True)
        live_skill_dir.mkdir(parents=True, exist_ok=True)

        try:
            shutil.copytree(prepared_dir, live_skill_dir, dirs_exist_ok=True)
        except Exception as e:
            return SafetyReport(False, report.skill_id, report.name, report.version, report.permissions, [f"No se pudo copiar a live: {e}"]), None

        src_skill = live_skill_dir / "skill.py"
        if not src_skill.exists():
            return SafetyReport(False, report.skill_id, report.name, report.version, report.permissions, ["Falta skill.py en live"]), None

        dst_module = self.user_skills_dir / f"{report.skill_id}.py"
        try:
            shutil.copy2(src_skill, dst_module)
        except Exception as e:
            return SafetyReport(False, report.skill_id, report.name, report.version, report.permissions, [f"No se pudo instalar en skills_user: {e}"]), None

        return report, dst_module

    def quarantine(self, staged_zip: Path, reason: str = "") -> Path:
        rep = SafetyReport(False, "manual", "", "", [], [reason or "Cuarentena manual"])
        return self._quarantine_attempt("manual", staged_zip=staged_zip, extracted_dir=None, report=rep)

    def delete_staged(self, staged_zip: Path) -> None:
        try:
            staged_zip.unlink(missing_ok=True)  # type: ignore
        except Exception:
            pass

    def _move_zip(self, staged_zip: Path, dest_dir: Path, reason: str = "") -> Path:
        dest_dir.mkdir(parents=True, exist_ok=True)
        out = dest_dir / staged_zip.name
        try:
            if out.exists():
                out.unlink()
        except Exception:
            pass

        try:
            shutil.move(str(staged_zip), str(out))
        except Exception:
            shutil.copy2(staged_zip, out)
            try:
                staged_zip.unlink(missing_ok=True)  # type: ignore
            except Exception:
                pass

        if reason:
            try:
                (dest_dir / f"{out.stem}.reason.txt").write_text(reason, encoding="utf-8")
            except Exception:
                pass

        return out

    def list_user_skills(self) -> list:
        """Listar skills del usuario con metadata"""
        skills = []
        try:
            for f in self.user_skills_dir.glob("*.py"):
                if f.name.startswith("_"):
                    continue
                skill_id = f.stem
                
                # Buscar manifest en live
                manifest_path = self.live_dir / skill_id / "manifest.json"
                info = {
                    "id": skill_id,
                    "name": skill_id,
                    "version": "1.0",
                    "permissions": [],
                    "installed_at": None
                }
                
                if manifest_path.exists():
                    try:
                        import json
                        data = json.loads(manifest_path.read_text(encoding="utf-8"))
                        info["name"] = data.get("name", skill_id)
                        info["version"] = data.get("version", "1.0")
                        info["permissions"] = data.get("permissions", [])
                    except:
                        pass
                
                # Fecha de instalación
                try:
                    info["installed_at"] = f.stat().st_mtime
                except:
                    pass
                
                skills.append(info)
        except Exception as e:
            print(f"Error listando skills: {e}")
        
        return sorted(skills, key=lambda x: x.get("installed_at", 0), reverse=True)

    def save_skill(self, skill_id: str, name: str, code: str, version: str = "1.0", 
                   permissions: list = None, description: str = "", 
                   category: str = "general", tags: list = None) -> dict:
        """Guardar skill del usuario desde código con categorización"""
        try:
            import json
            
            # Sanitizar ID
            sid = re.sub(r"[^a-zA-Z0-9_\-]+", "_", (skill_id or name).lower()).strip("_") or "skill"
            
            # Crear directorio en live organizado por categoría
            category_dir = self.live_dir / category
            category_dir.mkdir(parents=True, exist_ok=True)
            
            live_skill_dir = category_dir / sid
            live_skill_dir.mkdir(parents=True, exist_ok=True)
            
            # Guardar skill.py
            skill_py_path = live_skill_dir / "skill.py"
            skill_py_path.write_text(code, encoding="utf-8")
            
            # Guardar manifest con categoría
            manifest = {
                "id": sid,
                "name": name or sid,
                "version": version or "1.0",
                "permissions": permissions or [],
                "description": description,
                "category": category,
                "tags": tags or [],
                "created_at": time.time()
            }
            manifest_path = live_skill_dir / "manifest.json"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            
            # Copiar a user_skills_dir
            dst_module = self.user_skills_dir / f"{sid}.py"
            shutil.copy2(skill_py_path, dst_module)
            
            return {
                "success": True,
                "skill_id": sid,
                "message": f"Skill '{name}' guardada en categoría '{category}'",
                "path": str(dst_module),
                "category": category
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def delete_skill(self, skill_id: str) -> dict:
        """Eliminar skill del usuario"""
        try:
            deleted = []
            category = None
            
            # Buscar en todas las categorías para encontrar el skill
            for cat_dir in self.live_dir.iterdir():
                if cat_dir.is_dir():
                    live_dir = cat_dir / skill_id
                    if live_dir.exists():
                        category = cat_dir.name
                        shutil.rmtree(live_dir, ignore_errors=True)
                        deleted.append(str(live_dir))
                        break
            
            # Eliminar de user_skills_dir
            user_py = self.user_skills_dir / f"{skill_id}.py"
            if user_py.exists():
                user_py.unlink()
                deleted.append(str(user_py))
            
            return {
                "success": True,
                "deleted": deleted,
                "message": f"Skill '{skill_id}' eliminada" + (f" de categoría '{category}'" if category else "")
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def list_skills_by_category(self, category: str = None) -> dict:
        """Listar skills organizadas por categoría"""
        try:
            if category:
                # Listar solo una categoría
                category_dir = self.live_dir / category
                if not category_dir.exists():
                    return {"success": True, "category": category, "skills": []}
                
                skills = []
                for skill_dir in category_dir.iterdir():
                    if skill_dir.is_dir():
                        manifest_path = skill_dir / "manifest.json"
                        info = self._read_manifest(manifest_path, skill_dir.name)
                        skills.append(info)
                
                return {
                    "success": True,
                    "category": category,
                    "skills": sorted(skills, key=lambda x: x.get("name", ""))
                }
            else:
                # Listar todas las categorías
                categories = {}
                for cat_dir in self.live_dir.iterdir():
                    if cat_dir.is_dir():
                        cat_name = cat_dir.name
                        skills = []
                        for skill_dir in cat_dir.iterdir():
                            if skill_dir.is_dir():
                                manifest_path = skill_dir / "manifest.json"
                                info = self._read_manifest(manifest_path, skill_dir.name)
                                skills.append(info)
                        if skills:
                            categories[cat_name] = sorted(skills, key=lambda x: x.get("name", ""))
                
                return {
                    "success": True,
                    "categories": categories,
                    "total_skills": sum(len(s) for s in categories.values())
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _read_manifest(self, manifest_path: Path, skill_id: str) -> dict:
        """Leer manifest de una skill"""
        info = {
            "id": skill_id,
            "name": skill_id,
            "version": "1.0",
            "category": "general",
            "tags": [],
            "description": "",
            "permissions": []
        }
        
        if manifest_path.exists():
            try:
                import json
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                info.update(data)
            except:
                pass
        
        return info

    def get_skill_category(self, skill_id: str) -> str:
        """Obtener la categoría de una skill"""
        for cat_dir in self.live_dir.iterdir():
            if cat_dir.is_dir():
                if (cat_dir / skill_id).exists():
                    return cat_dir.name
        return "general"

    def discover_skills_for_objective(self, objective: str) -> list:
        """Descubrir skills relevantes para un objetivo basado en tags y descripción"""
        objective_lower = objective.lower()
        matching_skills = []
        
        try:
            # Buscar en todas las categorías
            result = self.list_skills_by_category()
            if not result.get("success"):
                return []
            
            for category, skills in result.get("categories", {}).items():
                for skill in skills:
                    score = 0
                    
                    # Coincidencia en nombre
                    name = skill.get("name", "").lower()
                    if name in objective_lower or any(word in objective_lower for word in name.split()):
                        score += 3
                    
                    # Coincidencia en descripción
                    desc = skill.get("description", "").lower()
                    if any(word in desc for word in objective_lower.split()[:5]):
                        score += 2
                    
                    # Coincidencia en tags
                    tags = skill.get("tags", [])
                    for tag in tags:
                        if tag.lower() in objective_lower:
                            score += 2
                    
                    # Coincidencia en categoría
                    if category in objective_lower or category.replace("_", " ") in objective_lower:
                        score += 1
                    
                    if score > 0:
                        skill["relevance_score"] = score
                        matching_skills.append(skill)
            
            # Ordenar por relevancia
            return sorted(matching_skills, key=lambda x: x.get("relevance_score", 0), reverse=True)
            
        except Exception as e:
            print(f"Error descubriendo skills: {e}")
            return []

    def get_skill_manifest(self, skill_id: str) -> dict:
        """Obtener el manifest completo de una skill"""
        category = self.get_skill_category(skill_id)
        manifest_path = self.live_dir / category / skill_id / "manifest.json"
        return self._read_manifest(manifest_path, skill_id)

vault = SkillVault()
