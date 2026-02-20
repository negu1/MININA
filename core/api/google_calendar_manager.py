"""
MININA v3.0 - Google Calendar Manager
API para operaciones con Google Calendar
"""

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta


@dataclass
class CalendarEvent:
    """Evento de calendario"""
    id: str
    summary: str
    description: str
    start: str
    end: str
    location: str
    attendees: List[str]
    link: str


class GoogleCalendarManager:
    """
    Manager de Google Calendar para MININA
    
    Requiere:
    - Google OAuth2 credentials (client_id, client_secret)
    - Access token con permisos de Calendar
    
    Para obtener:
    1. Ve a https://console.cloud.google.com/
    2. Crea un proyecto y habilita "Google Calendar API"
    3. Ve a "Credenciales" y crea OAuth2 credentials
    4. Descarga el archivo credentials.json
    """
    
    API_BASE_URL = "https://www.googleapis.com/calendar/v3"
    
    def __init__(self, config_path: str = "data/google_calendar_config.json"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.client_id: Optional[str] = None
        self.client_secret: Optional[str] = None
        self._load_config()
    
    def _load_config(self):
        """Cargar configuración guardada"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.access_token = data.get("access_token")
                    self.refresh_token = data.get("refresh_token")
                    self.client_id = data.get("client_id")
                    self.client_secret = data.get("client_secret")
            except Exception as e:
                print(f"Error cargando configuración Google Calendar: {e}")
    
    def _save_config(self):
        """Guardar configuración"""
        try:
            data = {
                "updated_at": datetime.now().isoformat(),
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando configuración Google Calendar: {e}")
    
    def set_credentials(
        self,
        client_id: str,
        client_secret: str,
        access_token: str,
        refresh_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Configurar credenciales de Google Calendar"""
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.refresh_token = refresh_token
        self._save_config()
        
        return {
            "success": True,
            "message": "Credenciales de Google Calendar configuradas correctamente"
        }
    
    def is_configured(self) -> bool:
        """Verificar si está configurado"""
        return bool(self.access_token and self.client_id)
    
    def list_events(
        self,
        calendar_id: str = "primary",
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Listar eventos del calendario
        
        Args:
            calendar_id: ID del calendario (default: primary)
            time_min: Fecha mínima (ISO format)
            time_max: Fecha máxima (ISO format)
            max_results: Máximo de eventos a retornar
        
        Returns:
            {
                "success": bool,
                "events": List[CalendarEvent],
                "error": str (si falla)
            }
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "Google Calendar no configurado"
            }
        
        # Simulación de eventos (para testing)
        mock_events = [
            {
                "id": "event1",
                "summary": "Reunión de equipo",
                "description": "Reunión semanal del equipo de desarrollo",
                "start": (datetime.now() + timedelta(hours=2)).isoformat(),
                "end": (datetime.now() + timedelta(hours=3)).isoformat(),
                "location": "Sala de conferencias A",
                "attendees": ["dev1@company.com", "dev2@company.com"],
                "link": "https://calendar.google.com/event?eid=event1"
            },
            {
                "id": "event2",
                "summary": "Llamada con cliente",
                "description": "Presentación del proyecto MININA",
                "start": (datetime.now() + timedelta(days=1)).isoformat(),
                "end": (datetime.now() + timedelta(days=1, hours=1)).isoformat(),
                "location": "Google Meet",
                "attendees": ["cliente@empresa.com"],
                "link": "https://calendar.google.com/event?eid=event2"
            }
        ]
        
        return {
            "success": True,
            "calendar_id": calendar_id,
            "events": mock_events,
            "count": len(mock_events)
        }
    
    def create_event(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        description: str = "",
        location: str = "",
        attendees: List[str] = None,
        calendar_id: str = "primary"
    ) -> Dict[str, Any]:
        """Crear evento en el calendario"""
        if not self.is_configured():
            return {
                "success": False,
                "error": "Google Calendar no configurado"
            }
        
        if not summary:
            return {"success": False, "error": "Falta título del evento (summary)"}
        
        if not start_time or not end_time:
            return {"success": False, "error": "Faltan horarios de inicio y fin"}
        
        # Simulación de creación
        return {
            "success": True,
            "event_id": "new_event_123",
            "summary": summary,
            "start": start_time,
            "end": end_time,
            "description": description,
            "location": location,
            "attendees": attendees or [],
            "link": "https://calendar.google.com/event?eid=new_event_123",
            "message": f"Evento '{summary}' creado exitosamente"
        }
    
    def delete_event(self, event_id: str, calendar_id: str = "primary") -> Dict[str, Any]:
        """Eliminar evento del calendario"""
        if not self.is_configured():
            return {
                "success": False,
                "error": "Google Calendar no configurado"
            }
        
        if not event_id:
            return {"success": False, "error": "Falta ID del evento"}
        
        # Simulación de eliminación
        return {
            "success": True,
            "event_id": event_id,
            "message": f"Evento {event_id} eliminado exitosamente"
        }
    
    def update_event(
        self,
        event_id: str,
        summary: str = None,
        start_time: str = None,
        end_time: str = None,
        description: str = None,
        location: str = None,
        calendar_id: str = "primary"
    ) -> Dict[str, Any]:
        """Actualizar evento existente"""
        if not self.is_configured():
            return {
                "success": False,
                "error": "Google Calendar no configurado"
            }
        
        if not event_id:
            return {"success": False, "error": "Falta ID del evento"}
        
        # Simulación de actualización
        return {
            "success": True,
            "event_id": event_id,
            "updated_fields": {
                "summary": summary,
                "start": start_time,
                "end": end_time,
                "description": description,
                "location": location
            },
            "message": f"Evento {event_id} actualizado exitosamente"
        }
    
    def get_config(self) -> Dict[str, Any]:
        """Obtener configuración actual"""
        return {
            "configured": self.is_configured(),
            "client_id": self.client_id[:10] + "***" if self.client_id else None,
            "has_access_token": bool(self.access_token),
            "has_refresh_token": bool(self.refresh_token)
        }


# Singleton
google_calendar_manager = GoogleCalendarManager()
