"""
WebUI State Management
======================
Gestión de estado thread-safe para la WebUI.
"""
import asyncio
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime

from fastapi import WebSocket


@dataclass
class UIState:
    """Estado global de la UI."""
    voice_active: bool = False
    current_path: str = ""
    llm_status: Dict[str, Any] = field(default_factory=dict)
    last_actions: List[Dict[str, Any]] = field(default_factory=list)
    system_status: str = "online"
    connected_clients: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "voice_active": self.voice_active,
            "current_path": self.current_path,
            "llm_status": self.llm_status,
            "system_status": self.system_status,
            "connected_clients": len(self.connected_clients),
        }


class WebSocketManager:
    """Gestión de conexiones WebSocket."""
    
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, client_id: str, websocket: WebSocket):
        """Register new WebSocket connection."""
        async with self._lock:
            self.connections[client_id] = websocket
    
    async def disconnect(self, client_id: str):
        """Remove WebSocket connection."""
        async with self._lock:
            if client_id in self.connections:
                del self.connections[client_id]
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients."""
        disconnected = []
        
        for client_id, ws in list(self.connections.items()):
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            async with self._lock:
                self.connections.pop(client_id, None)
    
    async def send_to_client(self, client_id: str, message: Dict[str, Any]):
        """Send message to specific client."""
        if client_id in self.connections:
            try:
                await self.connections[client_id].send_json(message)
            except Exception:
                await self.disconnect(client_id)


class StateManager:
    """Thread-safe state manager."""
    
    def __init__(self):
        self.state = UIState()
        self.ws_manager = WebSocketManager()
        self._lock = asyncio.Lock()
    
    async def update_state(self, **kwargs):
        """Update state attributes."""
        async with self._lock:
            for key, value in kwargs.items():
                if hasattr(self.state, key):
                    setattr(self.state, key, value)
    
    async def add_action(self, action: str, details: Optional[Dict] = None):
        """Add action to history."""
        async with self._lock:
            self.state.last_actions.append({
                "action": action,
                "timestamp": datetime.now().isoformat(),
                "details": details or {}
            })
            # Keep only last 100 actions
            if len(self.state.last_actions) > 100:
                self.state.last_actions = self.state.last_actions[-100:]
    
    async def broadcast_update(self, update_type: str, data: Dict[str, Any]):
        """Broadcast state update to all clients."""
        await self.ws_manager.broadcast({
            "type": update_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_state(self) -> Dict[str, Any]:
        """Get current state as dictionary."""
        return self.state.to_dict()


# Global instance
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """Get or create global state manager."""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager
