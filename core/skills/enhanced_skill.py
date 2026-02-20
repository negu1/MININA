"""
MININA v3.0 - EnhancedSkill Base Class
Clase base mejorada para skills
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio


class ResourceProfile(Enum):
    CPU_INTENSIVE = "cpu_intensive"
    IO_INTENSIVE = "io_intensive"
    NETWORK = "network"
    GENERAL = "general"


@dataclass
class SkillMetadata:
    """Metadata de skill mejorada"""
    name: str
    version: str = "1.0.0"
    description: str = ""
    resource_profile: ResourceProfile = ResourceProfile.GENERAL
    estimated_duration: int = 30  # segundos
    retry_policy: str = "exponential_backoff"
    max_retries: int = 3
    permissions: List[str] = None
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []


@dataclass
class SkillResult:
    """Resultado de ejecución de skill"""
    success: bool
    result: Any = None
    message: str = ""
    generated_files: List[Dict[str, Any]] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.generated_files is None:
            self.generated_files = []
        if self.metadata is None:
            self.metadata = {}


class EnhancedSkill(ABC):
    """
    Clase base mejorada para skills
    
    Todas las skills deben heredar de esta clase
    """
    
    def __init__(self):
        self.metadata = SkillMetadata(
            name=self.__class__.__name__,
            description=""
        )
        self._progress = 0
        
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> SkillResult:
        """
        Método principal de ejecución
        
        Args:
            context: Contexto de ejecución
            
        Returns:
            SkillResult: Resultado de la ejecución
        """
        pass
    
    async def report_progress(self, progress: int, message: str = ""):
        """Reportar progreso de ejecución"""
        self._progress = progress
        # TODO: Enviar evento de progreso al bus
        
    def validate_input(self, context: Dict[str, Any]) -> bool:
        """Validar input antes de ejecución"""
        return True
    
    def on_success(self, result: SkillResult):
        """Hook llamado en éxito"""
        pass
    
    def on_failure(self, error: Exception):
        """Hook llamado en fallo"""
        pass
