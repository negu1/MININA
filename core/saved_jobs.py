"""
MININA v3.0 - Sistema de Trabajos y Rutinas Guardadas
Gestión de trabajos/recetas reutilizables del orquestador
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
import os
from enum import Enum


class JobStatus(Enum):
    ACTIVE = "active"       # Disponible para uso
    ARCHIVED = "archived"   # Archivado temporalmente
    DRAFT = "draft"         # En desarrollo


class JobType(Enum):
    AUTOMATION = "automation"      # Automatización
    REPORT = "report"              # Generación de reportes
    INTEGRATION = "integration"    # Integración con APIs
    COMMUNICATION = "communication" # Comunicación
    DATA_PROCESSING = "data_processing" # Procesamiento de datos
    CUSTOM = "custom"              # Personalizado


@dataclass
class SavedJob:
    """
    Trabajo/Rutina guardada del orquestador
    """
    job_id: str
    name: str                           # Nombre descriptivo
    description: str                    # Descripción
    objective: str                     # Objetivo del trabajo
    job_type: JobType                   # Tipo de trabajo
    status: JobStatus                   # Estado
    
    # Configuración del plan
    plan_template: Dict[str, Any]      # Template del plan (sin plan_id)
    skills_required: List[str]          # Skills necesarios
    
    # Frecuencia y programación
    is_recurring: bool = False          # ¿Es recurrente?
    frequency: Optional[str] = None    # daily, weekly, monthly, custom
    schedule_time: Optional[str] = None # Hora de ejecución (HH:MM)
    schedule_days: List[str] = field(default_factory=list)  # Días de la semana
    
    # Preferencias
    notify_on_completion: bool = True
    notify_on_failure: bool = True
    notification_channels: List[str] = field(default_factory=lambda: ["ui"])
    
    # Historial
    last_executed: Optional[str] = None
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: List[str] = field(default_factory=list)
    icon: str = "🤖"                     # Emoji/icono
    color: str = "#6366f1"               # Color de categoría
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        data = asdict(self)
        data['job_type'] = self.job_type.value
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SavedJob':
        """Crear desde diccionario"""
        data['job_type'] = JobType(data.get('job_type', 'custom'))
        data['status'] = JobStatus(data.get('status', 'active'))
        return cls(**data)


class SavedJobsManager:
    """
    Gestor de trabajos/rutinas guardadas
    Singleton para persistencia
    """
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if SavedJobsManager._initialized:
            return
            
        self.data_dir = "data"
        self.jobs_file = os.path.join(self.data_dir, "saved_jobs.json")
        self.jobs: Dict[str, SavedJob] = {}
        
        # Asegurar directorio existe
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Cargar trabajos existentes
        self._load_jobs()
        
        # Crear ejemplos si está vacío
        if not self.jobs:
            self._create_sample_jobs()
        
        SavedJobsManager._initialized = True
    
    def _load_jobs(self):
        """Cargar trabajos desde archivo"""
        if os.path.exists(self.jobs_file):
            try:
                with open(self.jobs_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for job_id, job_data in data.items():
                        self.jobs[job_id] = SavedJob.from_dict(job_data)
            except Exception as e:
                print(f"Error cargando trabajos guardados: {e}")
    
    def _save_jobs(self):
        """Guardar trabajos a archivo"""
        try:
            data = {job_id: job.to_dict() for job_id, job in self.jobs.items()}
            with open(self.jobs_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando trabajos: {e}")
    
    def _create_sample_jobs(self):
        """Crear trabajos de ejemplo"""
        samples = [
            SavedJob(
                job_id="stock_supermarket_daily",
                name="📦 Stock del Supermercado",
                description="Actualiza y reporta el stock diario del supermercado",
                objective="Generar reporte de stock del supermercado con niveles actuales, productos bajos y alertas de reorden",
                job_type=JobType.REPORT,
                status=JobStatus.ACTIVE,
                plan_template={
                    "objective": "Generar reporte de stock del supermercado",
                    "tasks": [
                        {"name": "Leer datos de stock", "description": "Obtener datos actuales de inventario"},
                        {"name": "Analizar niveles", "description": "Identificar productos bajos y agotados"},
                        {"name": "Generar reporte", "description": "Crear reporte con tablas y alertas"},
                        {"name": "Enviar notificación", "description": "Notificar al equipo de compras"}
                    ]
                },
                skills_required=["data_analysis", "reporting"],
                is_recurring=True,
                frequency="daily",
                schedule_time="08:00",
                icon="📦",
                color="#f59e0b",
                tags=["supermercado", "stock", "diario", "reporte"]
            ),
            SavedJob(
                job_id="backup_weekly",
                name="💾 Backup Semanal",
                description="Realiza backup semanal de todos los datos importantes",
                objective="Crear copia de seguridad de bases de datos, documentos y configuraciones",
                job_type=JobType.AUTOMATION,
                status=JobStatus.ACTIVE,
                plan_template={
                    "objective": "Backup semanal de datos",
                    "tasks": [
                        {"name": "Backup bases de datos", "description": "Exportar todas las bases de datos"},
                        {"name": "Backup documentos", "description": "Sincronizar carpetas importantes"},
                        {"name": "Verificar integridad", "description": "Comprobar que los backups son válidos"},
                        {"name": "Notificar resultado", "description": "Enviar confirmación de backup"}
                    ]
                },
                skills_required=["file_management", "system"],
                is_recurring=True,
                frequency="weekly",
                schedule_time="02:00",
                schedule_days=["sunday"],
                icon="💾",
                color="#10b981",
                tags=["backup", "seguridad", "semanal"]
            ),
            SavedJob(
                job_id="social_media_post",
                name="📱 Post Redes Sociales",
                description="Crea y publica contenido en redes sociales",
                objective="Generar contenido atractivo y programar publicaciones en redes sociales",
                job_type=JobType.COMMUNICATION,
                status=JobStatus.DRAFT,
                plan_template={
                    "objective": "Crear contenido para redes sociales",
                    "tasks": [
                        {"name": "Generar ideas", "description": "Brainstorm de temas relevantes"},
                        {"name": "Crear contenido", "description": "Escribir posts con hashtags"},
                        {"name": "Diseñar gráficos", "description": "Crear imágenes para las publicaciones"},
                        {"name": "Programar publicación", "description": "Agendar posts en horarios óptimos"}
                    ]
                },
                skills_required=["content_generation", "design", "social_media"],
                is_recurring=False,
                icon="📱",
                color="#ec4899",
                tags=["redes sociales", "marketing", "contenido"]
            ),
            SavedJob(
                job_id="inventory_monthly",
                name="📊 Inventario Mensual",
                description="Inventario completo de todos los productos",
                objective="Realizar inventario físico y reconciliar con sistema",
                job_type=JobType.DATA_PROCESSING,
                status=JobStatus.ACTIVE,
                plan_template={
                    "objective": "Inventario mensual completo",
                    "tasks": [
                        {"name": "Preparar hojas de conteo", "description": "Generar listas de productos"},
                        {"name": "Conteo físico", "description": "Registrar cantidades reales"},
                        {"name": "Reconciliación", "description": "Comparar con stock del sistema"},
                        {"name": "Ajustar discrepancias", "description": "Corregir diferencias encontradas"},
                        {"name": "Reporte final", "description": "Generar reporte de inventario"}
                    ]
                },
                skills_required=["data_analysis", "reporting"],
                is_recurring=True,
                frequency="monthly",
                schedule_time="09:00",
                schedule_days=["1"],  # Primer día del mes
                icon="📊",
                color="#8b5cf6",
                tags=["inventario", "mensual", "stock", "reporte"]
            ),
            SavedJob(
                job_id="send_newsletter",
                name="📧 Enviar Newsletter",
                description="Prepara y envía newsletter a suscriptores",
                objective="Diseñar, redactar y enviar newsletter mensual a lista de suscriptores",
                job_type=JobType.COMMUNICATION,
                status=JobStatus.ACTIVE,
                plan_template={
                    "objective": "Enviar newsletter mensual",
                    "tasks": [
                        {"name": "Diseñar template", "description": "Crear diseño del newsletter"},
                        {"name": "Redactar contenido", "description": "Escribir artículos y novedades"},
                        {"name": "Revisar diseño", "description": "Verificar formato y links"},
                        {"name": "Enviar prueba", "description": "Enviar a email de prueba"},
                        {"name": "Enviar masivo", "description": "Distribuir a todos los suscriptores"}
                    ]
                },
                skills_required=["email", "design", "content_generation"],
                is_recurring=True,
                frequency="monthly",
                schedule_time="10:00",
                icon="📧",
                color="#3b82f6",
                tags=["email", "newsletter", "comunicación"]
            ),
            SavedJob(
                job_id="analyze_sales",
                name="📈 Análisis de Ventas",
                description="Análisis mensual de ventas y tendencias",
                objective="Analizar datos de ventas del mes, identificar tendencias y generar insights",
                job_type=JobType.REPORT,
                status=JobStatus.ACTIVE,
                plan_template={
                    "objective": "Análisis de ventas mensual",
                    "tasks": [
                        {"name": "Obtener datos", "description": "Extraer datos de ventas del mes"},
                        {"name": "Calcular métricas", "description": "KPIs: ingresos, ticket promedio, conversión"},
                        {"name": "Identificar tendencias", "description": "Análisis de productos y temporadas"},
                        {"name": "Comparar períodos", "description": "vs mes anterior y vs año pasado"},
                        {"name": "Generar dashboard", "description": "Crear visualizaciones"}
                    ]
                },
                skills_required=["data_analysis", "visualization", "reporting"],
                is_recurring=True,
                frequency="monthly",
                schedule_time="11:00",
                icon="📈",
                color="#10b981",
                tags=["ventas", "análisis", "métricas", "mensual"]
            )
        ]
        
        for job in samples:
            self.jobs[job.job_id] = job
        
        self._save_jobs()
    
    # ============== CRUD Operations ==============
    
    def create_job(self, job: SavedJob) -> bool:
        """Crear nuevo trabajo"""
        if job.job_id in self.jobs:
            return False
        self.jobs[job.job_id] = job
        self._save_jobs()
        return True
    
    def update_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """Actualizar trabajo existente"""
        if job_id not in self.jobs:
            return False
        
        job = self.jobs[job_id]
        for key, value in updates.items():
            if hasattr(job, key):
                setattr(job, key, value)
        
        job.updated_at = datetime.now().isoformat()
        self._save_jobs()
        return True
    
    def delete_job(self, job_id: str) -> bool:
        """Eliminar trabajo"""
        if job_id not in self.jobs:
            return False
        del self.jobs[job_id]
        self._save_jobs()
        return True
    
    def get_job(self, job_id: str) -> Optional[SavedJob]:
        """Obtener trabajo por ID"""
        return self.jobs.get(job_id)
    
    def get_all_jobs(self) -> List[SavedJob]:
        """Obtener todos los trabajos"""
        return list(self.jobs.values())
    
    def get_active_jobs(self) -> List[SavedJob]:
        """Obtener trabajos activos"""
        return [j for j in self.jobs.values() if j.status == JobStatus.ACTIVE]
    
    def get_jobs_by_type(self, job_type: JobType) -> List[SavedJob]:
        """Obtener trabajos por tipo"""
        return [j for j in self.jobs.values() if j.job_type == job_type]
    
    def get_jobs_by_tag(self, tag: str) -> List[SavedJob]:
        """Obtener trabajos por etiqueta"""
        return [j for j in self.jobs.values() if tag in j.tags]
    
    def search_jobs(self, query: str) -> List[SavedJob]:
        """Buscar trabajos por nombre/descripción"""
        query = query.lower()
        results = []
        for job in self.jobs.values():
            if (query in job.name.lower() or 
                query in job.description.lower() or
                query in job.objective.lower() or
                any(query in tag.lower() for tag in job.tags)):
                results.append(job)
        return results
    
    # ============== Activation ==============
    
    def activate_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Activar un trabajo guardado
        Retorna la información necesaria para ejecutar en el orquestador
        """
        job = self.jobs.get(job_id)
        if not job:
            return None
        
        # Actualizar estadísticas
        job.last_executed = datetime.now().isoformat()
        job.execution_count += 1
        self._save_jobs()
        
        return {
            "job_id": job.job_id,
            "name": job.name,
            "objective": job.objective,
            "plan_template": job.plan_template,
            "skills_required": job.skills_required,
            "notification_channels": job.notification_channels
        }
    
    def record_execution_result(self, job_id: str, success: bool):
        """Registrar resultado de ejecución"""
        job = self.jobs.get(job_id)
        if job:
            if success:
                job.success_count += 1
            else:
                job.failure_count += 1
            self._save_jobs()
    
    # ============== Categories ==============
    
    def get_job_types(self) -> List[Dict[str, str]]:
        """Obtener tipos de trabajos disponibles"""
        return [
            {"id": "automation", "name": "Automatización", "icon": "🤖", "color": "#6366f1"},
            {"id": "report", "name": "Reportes", "icon": "📊", "color": "#3b82f6"},
            {"id": "integration", "name": "Integraciones", "icon": "🔗", "color": "#8b5cf6"},
            {"id": "communication", "name": "Comunicación", "icon": "💬", "color": "#ec4899"},
            {"id": "data_processing", "name": "Procesamiento de Datos", "icon": "🔄", "color": "#f59e0b"},
            {"id": "custom", "name": "Personalizado", "icon": "⚙️", "color": "#6b7280"},
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas"""
        total = len(self.jobs)
        active = len([j for j in self.jobs.values() if j.status == JobStatus.ACTIVE])
        recurring = len([j for j in self.jobs.values() if j.is_recurring])
        total_executions = sum(j.execution_count for j in self.jobs.values())
        
        by_type = {}
        for job_type in JobType:
            by_type[job_type.value] = len([j for j in self.jobs.values() if j.job_type == job_type])
        
        return {
            "total": total,
            "active": active,
            "recurring": recurring,
            "total_executions": total_executions,
            "by_type": by_type
        }


# Singleton getter
def get_saved_jobs_manager() -> SavedJobsManager:
    return SavedJobsManager()
