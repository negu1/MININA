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
    def __init__(self):
        # Usar ruta relativa al directorio de MININA en Desktop
        # Esto asegura que los datos esten junto a la aplicacion
        minina_root = Path(__file__).parent.parent
        self.data_dir = minina_root / "data"
        
        self.base_dir = self.data_dir / "skills_vault"
        self.staging_dir = self.base_dir / "staging"
        self.live_dir = self.base_dir / "live"
        self.quarantine_dir = self.base_dir / "quarantine"
        
        # user_skills_dir también en la ruta relativa
        self.user_skills_dir = self.data_dir / "skills_user"
        
        # output_dir para archivos generados por skills
        self.output_dir = self.data_dir / "output"

        # Crear todos los directorios
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        self.live_dir.mkdir(parents=True, exist_ok=True)
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        self.user_skills_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.gate = SkillSafetyGate()

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
                   permissions: list = None, description: str = "") -> dict:
        """Guardar skill del usuario desde código"""
        try:
            import json
            
            # Sanitizar ID
            sid = re.sub(r"[^a-zA-Z0-9_\-]+", "_", (skill_id or name).lower()).strip("_") or "skill"
            
            # Crear directorio en live
            live_skill_dir = self.live_dir / sid
            live_skill_dir.mkdir(parents=True, exist_ok=True)
            
            # Guardar skill.py
            skill_py_path = live_skill_dir / "skill.py"
            skill_py_path.write_text(code, encoding="utf-8")
            
            # Guardar manifest
            manifest = {
                "id": sid,
                "name": name or sid,
                "version": version or "1.0",
                "permissions": permissions or [],
                "description": description,
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
                "message": f"Skill '{name}' guardada correctamente",
                "path": str(dst_module)
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
            
            # Eliminar de user_skills_dir
            user_py = self.user_skills_dir / f"{skill_id}.py"
            if user_py.exists():
                user_py.unlink()
                deleted.append(str(user_py))
            
            # Eliminar de live
            live_dir = self.live_dir / skill_id
            if live_dir.exists():
                shutil.rmtree(live_dir, ignore_errors=True)
                deleted.append(str(live_dir))
            
            return {
                "success": True,
                "deleted": deleted,
                "message": f"Skill '{skill_id}' eliminada"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

vault = SkillVault()
