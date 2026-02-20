"""
Sistema de Gestión de Archivos/Trabajos para MININA
Organiza archivos generados por skills en carpetas por tipo
"""
import json
import os
import shutil
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import mimetypes

logger = logging.getLogger("FileManager")

WORKS_BASE_PATH = Path("data/works")

# Mapeo de extensiones a tipos de trabajo
FILE_TYPE_MAPPING = {
    # Imágenes
    '.jpg': 'imagenes', '.jpeg': 'imagenes', '.png': 'imagenes', 
    '.gif': 'imagenes', '.bmp': 'imagenes', '.svg': 'imagenes',
    '.webp': 'imagenes', '.ico': 'imagenes',
    
    # Videos
    '.mp4': 'videos', '.avi': 'videos', '.mkv': 'videos',
    '.mov': 'videos', '.wmv': 'videos', '.flv': 'videos',
    '.webm': 'videos',
    
    # PDFs
    '.pdf': 'pdfs',
    
    # Apps (ejecutables, scripts)
    '.exe': 'apps', '.msi': 'apps', '.app': 'apps',
    '.apk': 'apps', '.ipa': 'apps',
    
    # Web (HTML, CSS, JS)
    '.html': 'web', '.htm': 'web', '.css': 'web',
    '.js': 'web', '.jsx': 'web', '.ts': 'web', '.tsx': 'web',
    
    # Software (código fuente, configuraciones)
    '.py': 'software', '.java': 'software', '.cpp': 'software',
    '.c': 'software', '.h': 'software', '.cs': 'software',
    '.go': 'software', '.rs': 'software', '.rb': 'software',
    '.php': 'software', '.swift': 'software', '.kt': 'software',
    '.json': 'software', '.xml': 'software', '.yaml': 'software',
    '.yml': 'software', '.sql': 'software', '.sh': 'software',
    '.bat': 'software', '.ps1': 'software', '.dockerfile': 'software',
}

CATEGORY_NAMES = {
    'imagenes': '🖼️ Imágenes',
    'videos': '🎬 Videos', 
    'pdfs': '📄 PDFs',
    'apps': '📱 Aplicaciones',
    'web': '🌐 Web',
    'software': '💻 Software',
}

CATEGORY_ICONS = {
    'imagenes': 'fa-image',
    'videos': 'fa-video',
    'pdfs': 'fa-file-pdf',
    'apps': 'fa-mobile-alt',
    'web': 'fa-globe',
    'software': 'fa-code',
}


@dataclass
class WorkFile:
    id: str
    filename: str
    original_name: str
    category: str
    path: str
    size: int
    created_at: str
    skill_name: str
    skill_id: str
    description: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return asdict(self)


class WorksManager:
    """Gestor centralizado de trabajos/archivos"""
    
    def __init__(self):
        self.base_path = WORKS_BASE_PATH
        self.index_file = self.base_path / "works_index.json"
        self.works: Dict[str, WorkFile] = {}
        
        # Crear estructura de carpetas
        for category in CATEGORY_NAMES.keys():
            (self.base_path / category).mkdir(parents=True, exist_ok=True)
        
        self._load_index()
    
    def _load_index(self):
        """Cargar índice de trabajos"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for work_id, work_data in data.get("works", {}).items():
                    self.works[work_id] = WorkFile(**work_data)
                
                logger.info(f"Cargados {len(self.works)} trabajos del índice")
            except Exception as e:
                logger.error(f"Error cargando índice de trabajos: {e}")
    
    def _save_index(self):
        """Guardar índice de trabajos"""
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "total_works": len(self.works),
                "works": {k: v.to_dict() for k, v in self.works.items()}
            }
            
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando índice de trabajos: {e}")
    
    def _get_category(self, filename: str) -> str:
        """Determinar categoría basada en extensión"""
        ext = Path(filename).suffix.lower()
        return FILE_TYPE_MAPPING.get(ext, 'software')  # Default a software
    
    def _generate_id(self, filename: str) -> str:
        """Generar ID único para el trabajo"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_input = f"{filename}_{timestamp}_{os.urandom(8).hex()}"
        file_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        return f"{timestamp}_{file_hash}"
    
    def save_file(self, source_path: str, filename: str, skill_name: str, 
                  skill_id: str, description: str = "", metadata: Dict = None) -> Optional[WorkFile]:
        """Guardar un archivo generado por una skill"""
        try:
            source = Path(source_path)
            if not source.exists():
                logger.error(f"Archivo fuente no existe: {source_path}")
                return None
            
            # Determinar categoría
            category = self._get_category(filename)
            
            # Generar ID y ruta destino
            work_id = self._generate_id(filename)
            category_path = self.base_path / category
            
            # Asegurar nombre único
            dest_filename = f"{work_id}_{filename}"
            dest_path = category_path / dest_filename
            
            # Copiar archivo
            shutil.copy2(source_path, dest_path)
            
            # Crear registro
            work = WorkFile(
                id=work_id,
                filename=dest_filename,
                original_name=filename,
                category=category,
                path=str(dest_path.relative_to(self.base_path)),
                size=dest_path.stat().st_size,
                created_at=datetime.now().isoformat(),
                skill_name=skill_name,
                skill_id=skill_id,
                description=description,
                metadata=metadata or {}
            )
            
            self.works[work_id] = work
            self._save_index()
            
            # Publicar evento de work completado
            try:
                import asyncio
                from core.CortexBus import bus
                asyncio.create_task(bus.publish(
                    "work.COMPLETED",
                    {
                        "work_id": work_id,
                        "work_name": filename,
                        "category": category,
                        "skill_name": skill_name,
                        "timestamp": datetime.now().isoformat()
                    },
                    sender="WorksManager"
                ))
            except Exception as e:
                logger.warning(f"Error publicando evento work.COMPLETED: {e}")
            
            logger.info(f"[WORKS] Guardado: {filename} en {category} (ID: {work_id})")
            return work
            
        except Exception as e:
            logger.error(f"Error guardando archivo: {e}")
            return None
    
    def save_content(self, content: str or bytes, filename: str, skill_name: str,
                     skill_id: str, description: str = "", metadata: Dict = None) -> Optional[WorkFile]:
        """Guardar contenido directamente (string o bytes)"""
        try:
            category = self._get_category(filename)
            work_id = self._generate_id(filename)
            category_path = self.base_path / category
            
            dest_filename = f"{work_id}_{filename}"
            dest_path = category_path / dest_filename
            
            # Escribir contenido
            mode = 'wb' if isinstance(content, bytes) else 'w'
            encoding = None if isinstance(content, bytes) else 'utf-8'
            
            with open(dest_path, mode, encoding=encoding) as f:
                f.write(content)
            
            work = WorkFile(
                id=work_id,
                filename=dest_filename,
                original_name=filename,
                category=category,
                path=str(dest_path.relative_to(self.base_path)),
                size=dest_path.stat().st_size,
                created_at=datetime.now().isoformat(),
                skill_name=skill_name,
                skill_id=skill_id,
                description=description,
                metadata=metadata or {}
            )
            
            self.works[work_id] = work
            self._save_index()
            
            # Publicar evento de work completado
            try:
                import asyncio
                from core.CortexBus import bus
                asyncio.create_task(bus.publish(
                    "work.COMPLETED",
                    {
                        "work_id": work_id,
                        "work_name": filename,
                        "category": category,
                        "skill_name": skill_name,
                        "timestamp": datetime.now().isoformat()
                    },
                    sender="WorksManager"
                ))
            except Exception as e:
                logger.warning(f"Error publicando evento work.COMPLETED: {e}")
            
            logger.info(f"[WORKS] Guardado contenido: {filename} en {category} (ID: {work_id})")
            return work
            
        except Exception as e:
            logger.error(f"Error guardando contenido: {e}")
            return None
    
    def get_work(self, work_id: str) -> Optional[WorkFile]:
        """Obtener un trabajo por ID"""
        return self.works.get(work_id)
    
    def get_works_by_category(self, category: str) -> List[WorkFile]:
        """Obtener trabajos de una categoría"""
        return [w for w in self.works.values() if w.category == category]
    
    def get_works_by_skill(self, skill_id: str) -> List[WorkFile]:
        """Obtener trabajos generados por una skill específica"""
        return [w for w in self.works.values() if w.skill_id == skill_id]
    
    def get_all_categories(self) -> List[Dict]:
        """Obtener todas las categorías con conteos"""
        result = []
        for cat_id, cat_name in CATEGORY_NAMES.items():
            works = self.get_works_by_category(cat_id)
            result.append({
                "id": cat_id,
                "name": cat_name,
                "icon": CATEGORY_ICONS.get(cat_id, "fa-file"),
                "count": len(works),
                "total_size": sum(w.size for w in works)
            })
        return result
    
    def get_all_works(self, category: str = None, limit: int = 1000) -> List[Dict]:
        """Obtener todos los trabajos, opcionalmente filtrados por categoría"""
        works = self.works.values()
        
        if category:
            works = [w for w in works if w.category == category]
        
        # Ordenar por fecha descendente
        works = sorted(works, key=lambda x: x.created_at, reverse=True)
        
        return [w.to_dict() for w in works[:limit]]
    
    def delete_work(self, work_id: str) -> bool:
        """Eliminar un trabajo"""
        work = self.works.get(work_id)
        if not work:
            return False
        
        try:
            # Eliminar archivo físico
            file_path = self.base_path / work.path
            if file_path.exists():
                file_path.unlink()
            
            # Eliminar del índice
            del self.works[work_id]
            self._save_index()
            
            logger.info(f"[WORKS] Eliminado: {work_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error eliminando trabajo: {e}")
            return False
    
    def get_file_path(self, work_id: str) -> Optional[Path]:
        """Obtener ruta física del archivo"""
        work = self.works.get(work_id)
        if work:
            return self.base_path / work.path
        return None


# Instancia global
works_manager = WorksManager()
