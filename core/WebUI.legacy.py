import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from core.CortexBus import bus
from core.UserObservabilityStore import store

logger = logging.getLogger("MININAWebUI")

# Estado global de la UI
ui_state = {
    "voice_active": False,
    "current_path": "",
    "llm_status": {},
    "last_actions": [],
    "system_status": "online"
}

# Conexiones WebSocket
ws_connections = []

async def broadcast_message(message: dict):
    """Broadcast a todos los clientes WebSocket"""
    disconnected = []
    for ws in ws_connections:
        try:
            await ws.send_json(message)
        except:
            disconnected.append(ws)
    for ws in disconnected:
        if ws in ws_connections:
            ws_connections.remove(ws)

# HTML Template profesional con paneles
HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MININA - Control Panel</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        .glass-panel {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .sidebar-item { transition: all 0.3s ease; }
        .sidebar-item:hover {
            background: rgba(59, 130, 246, 0.1);
            transform: translateX(5px);
        }
        .sidebar-item.active {
            background: rgba(59, 130, 246, 0.2);
            border-right: 3px solid #3b82f6;
        }
        .voice-indicator { animation: pulse 2s infinite; }
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(1.1); }
        }
        .status-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
        .status-online { background: #22c55e; box-shadow: 0 0 10px #22c55e; }
        .card-hover { transition: all 0.3s ease; }
        .card-hover:hover { transform: translateY(-2px); box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
        .log-entry {
            font-family: 'Courier New', monospace;
            font-size: 0.85rem;
            padding: 4px 8px;
            border-left: 3px solid #3b82f6;
            margin: 2px 0;
            background: rgba(59, 130, 246, 0.05);
        }
        .panel { display: none; }
        .panel.active { display: block; }
    </style>
</head>
<body class="bg-gray-100 h-screen overflow-hidden">
    <div class="flex h-full">
        <!-- Sidebar -->
        <aside class="w-64 bg-slate-900 text-white flex flex-col shadow-2xl">
            <div class="p-6 border-b border-slate-700">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
                        <i class="fas fa-robot text-white text-xl"></i>
                    </div>
                    <div>
                        <h1 class="font-bold text-lg">MININA</h1>
                        <p class="text-xs text-slate-400">Product-20</p>
                    </div>
                </div>
            </div>
            
            <nav class="flex-1 p-4 space-y-2">
                <button onclick="showPanel('dashboard')" class="sidebar-item active w-full text-left p-3 rounded-lg flex items-center gap-3" data-panel="dashboard">
                    <i class="fas fa-home w-5"></i><span>Dashboard</span>
                </button>
                <button onclick="showPanel('pc')" class="sidebar-item w-full text-left p-3 rounded-lg flex items-center gap-3" data-panel="pc">
                    <i class="fas fa-folder w-5"></i><span>Explorador PC</span>
                </button>
                <button onclick="showPanel('bot')" class="sidebar-item w-full text-left p-3 rounded-lg flex items-center gap-3" data-panel="bot">
                    <i class="fas fa-robot w-5"></i><span>Configurar Bot</span>
                </button>
                <button onclick="showPanel('llm')" class="sidebar-item w-full text-left p-3 rounded-lg flex items-center gap-3" data-panel="llm">
                    <i class="fas fa-brain w-5"></i><span>Configurar IA</span>
                </button>
                <button onclick="showPanel('skills')" class="sidebar-item w-full text-left p-3 rounded-lg flex items-center gap-3" data-panel="skills">
                    <i class="fas fa-cubes w-5"></i><span>Skills</span>
                </button>
                <button onclick="showPanel('chat')" class="sidebar-item w-full text-left p-3 rounded-lg flex items-center gap-3" data-panel="chat">
                    <i class="fas fa-comments w-5"></i><span>Chat</span>
                </button>
                <button onclick="showPanel('update')" class="sidebar-item w-full text-left p-3 rounded-lg flex items-center gap-3" data-panel="update">
                    <i class="fas fa-sync-alt w-5"></i><span>Actualización</span>
                </button>
                <button onclick="showPanel('backup')" class="sidebar-item w-full text-left p-3 rounded-lg flex items-center gap-3" data-panel="backup">
                    <i class="fas fa-save w-5"></i><span>Backup</span>
                </button>
                <button onclick="showPanel('logs')" class="sidebar-item w-full text-left p-3 rounded-lg flex items-center gap-3" data-panel="logs">
                    <i class="fas fa-terminal w-5"></i><span>Logs y Estado</span>
                </button>
            </nav>
            
            <div class="p-4 border-t border-slate-700">
                <div class="flex items-center gap-2 text-sm">
                    <span class="status-dot status-online"></span>
                    <span>Sistema Online</span>
                </div>
                <p class="text-xs text-slate-500 mt-2">WebSocket: <span id="ws-status" class="text-yellow-500">Conectando...</span></p>
            </div>
        </aside>
        
        <!-- Main Content -->
        <main class="flex-1 overflow-y-auto p-6">
            
            <!-- Dashboard Panel -->
            <div id="panel-dashboard" class="panel active">
                <div class="flex items-center justify-between mb-6">
                    <h2 class="text-2xl font-bold text-gray-800">Dashboard</h2>
                    <div class="flex items-center gap-3">
                        <span id="last-update" class="text-sm text-gray-500">Actualizado: --</span>
                        <button onclick="updateDashboard()" class="px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm">
                            <i class="fas fa-sync-alt mr-1"></i> Actualizar
                        </button>
                    </div>
                </div>
                
                <!-- Cards Grid -->
                <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
                    <div class="glass-panel rounded-xl p-4 card-hover">
                        <div class="flex items-center justify-between mb-2">
                            <div>
                                <p class="text-gray-500 text-xs">Estado Voz</p>
                                <p class="text-xl font-bold text-gray-800" id="dash-voice">Inactivo</p>
                            </div>
                            <div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                                <i class="fas fa-microphone text-blue-600"></i>
                            </div>
                        </div>
                        <div class="h-1 bg-gray-200 rounded-full">
                            <div id="dash-voice-bar" class="h-1 bg-blue-500 rounded-full" style="width: 0%"></div>
                        </div>
                    </div>
                    
                    <div class="glass-panel rounded-xl p-4 card-hover">
                        <div class="flex items-center justify-between mb-2">
                            <div>
                                <p class="text-gray-500 text-xs">Skills Guardadas</p>
                                <p class="text-xl font-bold text-gray-800" id="dash-skills">0</p>
                            </div>
                            <div class="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                                <i class="fas fa-cubes text-green-600"></i>
                            </div>
                        </div>
                        <div class="flex items-center gap-1">
                            <span id="dash-skills-running" class="text-xs text-orange-600 font-medium">0</span>
                            <span class="text-xs text-gray-400">en ejecución</span>
                        </div>
                    </div>
                    
                    <div class="glass-panel rounded-xl p-4 card-hover">
                        <div class="flex items-center justify-between mb-2">
                            <div>
                                <p class="text-gray-500 text-xs">Archivos Generados</p>
                                <p class="text-xl font-bold text-gray-800" id="dash-files">0</p>
                            </div>
                            <div class="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
                                <i class="fas fa-folder-open text-purple-600"></i>
                            </div>
                        </div>
                        <div class="flex flex-wrap gap-1 text-xs">
                            <span id="dash-files-img" class="px-1.5 py-0.5 bg-pink-100 text-pink-600 rounded">🖼️ 0</span>
                            <span id="dash-files-txt" class="px-1.5 py-0.5 bg-green-100 text-green-600 rounded">📝 0</span>
                        </div>
                    </div>
                    
                    <div class="glass-panel rounded-xl p-4 card-hover">
                        <div class="flex items-center justify-between mb-2">
                            <div>
                                <p class="text-gray-500 text-xs">Providers IA</p>
                                <p class="text-xl font-bold text-gray-800" id="dash-llm">0</p>
                            </div>
                            <div class="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center">
                                <i class="fas fa-brain text-indigo-600"></i>
                            </div>
                        </div>
                        <div class="text-xs text-gray-500" id="dash-llm-active">Ninguno activo</div>
                    </div>
                    
                    <div class="glass-panel rounded-xl p-4 card-hover">
                        <div class="flex items-center justify-between mb-2">
                            <div>
                                <p class="text-gray-500 text-xs">Acciones Hoy</p>
                                <p class="text-xl font-bold text-gray-800" id="dash-actions">0</p>
                            </div>
                            <div class="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center">
                                <i class="fas fa-bolt text-orange-600"></i>
                            </div>
                        </div>
                        <div class="text-xs text-gray-500">eventos registrados</div>
                    </div>
                    
                    <div class="glass-panel rounded-xl p-4 card-hover">
                        <div class="flex items-center justify-between mb-2">
                            <div>
                                <p class="text-gray-500 text-xs">Sistema</p>
                                <p class="text-xl font-bold text-gray-800" id="dash-cpu">--%</p>
                            </div>
                            <div class="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                                <i class="fas fa-microchip text-red-600"></i>
                            </div>
                        </div>
                        <div class="text-xs text-gray-500">RAM: <span id="dash-ram">--%</span></div>
                    </div>
                </div>
                
                <!-- Quick Actions -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <div class="glass-panel rounded-xl p-4">
                        <h4 class="font-bold mb-3 text-gray-700">Accesos Rápidos</h4>
                        <div class="grid grid-cols-2 gap-2">
                            <button onclick="showPanel('skills')" class="p-2 bg-blue-50 hover:bg-blue-100 rounded-lg text-sm text-left">
                                <i class="fas fa-cubes text-blue-500 mr-2"></i>Mis Skills
                            </button>
                            <button onclick="showPanel('skills'); showSkillsTab('creaciones')" class="p-2 bg-purple-50 hover:bg-purple-100 rounded-lg text-sm text-left">
                                <i class="fas fa-folder-open text-purple-500 mr-2"></i>Mis Creaciones
                            </button>
                            <button onclick="showPanel('pc')" class="p-2 bg-green-50 hover:bg-green-100 rounded-lg text-sm text-left">
                                <i class="fas fa-folder text-green-500 mr-2"></i>Explorador PC
                            </button>
                            <button onclick="showPanel('chat')" class="p-2 bg-yellow-50 hover:bg-yellow-100 rounded-lg text-sm text-left">
                                <i class="fas fa-comments text-yellow-500 mr-2"></i>Chat
                            </button>
                        </div>
                    </div>
                    
                    <div class="glass-panel rounded-xl p-4">
                        <h4 class="font-bold mb-3 text-gray-700">Estado del Sistema</h4>
                        <div class="space-y-2 text-sm">
                            <div class="flex justify-between">
                                <span class="text-gray-500">WebSocket:</span>
                                <span id="ws-status-badge" class="px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs">Conectado</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-500">MININA:</span>
                                <span class="text-green-600 font-medium">Online</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-500">Directorio de datos:</span>
                                <span class="text-gray-700 font-mono text-xs">.\data\</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="glass-panel rounded-xl p-5">
                    <h3 class="font-bold text-lg mb-4 flex items-center gap-2">
                        <i class="fas fa-history text-blue-500"></i>Actividad Reciente
                    </h3>
                    <div id="activity-log" class="space-y-2 max-h-60 overflow-y-auto">
                        <p class="text-gray-500 text-sm">Esperando actividad...</p>
                    </div>
                </div>
            </div>
            
            <!-- PC Explorer Panel -->
            <div id="panel-pc" class="panel">
                <h2 class="text-2xl font-bold mb-6 text-gray-800">Explorador de PC</h2>
                <div class="glass-panel rounded-xl p-3 mb-4 flex items-center gap-2">
                    <button onclick="pcAction('back')" class="p-2 hover:bg-gray-100 rounded-lg" title="Atrás"><i class="fas fa-arrow-left"></i></button>
                    <button onclick="pcAction('home')" class="p-2 hover:bg-gray-100 rounded-lg" title="Inicio"><i class="fas fa-home"></i></button>
                    <div class="flex-1 bg-gray-100 rounded-lg px-4 py-2 font-mono text-sm" id="current-path">C:\\Users</div>
                    <button onclick="pcAction('refresh')" class="p-2 hover:bg-gray-100 rounded-lg" title="Actualizar"><i class="fas fa-sync-alt"></i></button>
                </div>
                <div class="glass-panel rounded-xl p-4">
                    <div id="file-list" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                        <div class="p-4 border border-gray-200 rounded-lg hover:border-blue-400 cursor-pointer text-center">
                            <i class="fas fa-folder text-3xl text-yellow-500 mb-2"></i>
                            <p class="text-sm font-medium">Documentos</p>
                        </div>
                        <div class="p-4 border border-gray-200 rounded-lg hover:border-blue-400 cursor-pointer text-center">
                            <i class="fas fa-folder text-3xl text-yellow-500 mb-2"></i>
                            <p class="text-sm font-medium">Descargas</p>
                        </div>
                        <div class="p-4 border border-gray-200 rounded-lg hover:border-blue-400 cursor-pointer text-center">
                            <i class="fas fa-folder text-3xl text-yellow-500 mb-2"></i>
                            <p class="text-sm font-medium">Escritorio</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Bot Config Panel -->
            <div id="panel-bot" class="panel">
                <h2 class="text-2xl font-bold mb-6 text-gray-800">Configuración de Bot</h2>
                
                <!-- Tabs -->
                <div class="flex gap-2 mb-6">
                    <button onclick="showBotTab('telegram')" id="tab-telegram" class="px-4 py-2 bg-blue-500 text-white rounded-lg font-medium">
                        <i class="fab fa-telegram mr-2"></i>Telegram
                    </button>
                    <button onclick="showBotTab('whatsapp')" id="tab-whatsapp" class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg">
                        <i class="fab fa-whatsapp mr-2"></i>WhatsApp
                    </button>
                </div>
                
                <!-- Telegram Tab -->
                <div id="bot-tab-telegram" class="bot-tab">
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <!-- Guía paso a paso -->
                        <div class="glass-panel rounded-xl p-6">
                            <h3 class="font-bold text-lg mb-4 flex items-center gap-2">
                                <i class="fas fa-book text-blue-500"></i>Guía Rápida
                            </h3>
                            
                            <!-- Advertencias de seguridad -->
                            <div class="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                                <h4 class="font-bold text-red-700 mb-2"><i class="fas fa-shield-alt mr-2"></i>⚠️ Advertencias de Seguridad</h4>
                                <ul class="text-sm text-red-600 space-y-1">
                                    <li>• NUNCA compartas tu Bot Token con nadie</li>
                                    <li>• Guarda el token en un lugar seguro</li>
                                    <li>• Si el token se filtra, cualquiera puede controlar tu bot</li>
                                    <li>🔒 MiIA encriptará y protegerá tu token automáticamente</li>
                                </ul>
                            </div>
                            
                            <div class="space-y-4">
                                <div class="p-3 bg-blue-50 rounded-lg">
                                    <p class="font-bold text-blue-800">Paso 1: Crear bot con BotFather</p>
                                    <ol class="text-sm text-blue-600 mt-2 ml-4 space-y-1">
                                        <li>1. Abre Telegram y busca: <a href="https://t.me/BotFather" target="_blank" class="underline">@BotFather</a></li>
                                        <li>2. Escribe: <code>/newbot</code></li>
                                        <li>3. Elige un nombre (ej: MiIA Asistente)</li>
                                        <li>4. Elige username terminado en 'bot'</li>
                                    </ol>
                                    <p class="text-sm text-green-600 mt-2">✅ Resultado: Token largo con números y letras</p>
                                </div>
                                
                                <div class="p-3 bg-blue-50 rounded-lg">
                                    <p class="font-bold text-blue-800">Paso 2: Obtener tu Chat ID</p>
                                    <ol class="text-sm text-blue-600 mt-2 ml-4 space-y-1">
                                        <li>1. Busca: <a href="https://t.me/userinfobot" target="_blank" class="underline">@userinfobot</a></li>
                                        <li>2. Inicia conversación</li>
                                        <li>3. El bot responde con tu información</li>
                                    </ol>
                                    <p class="text-sm text-green-600 mt-2">✅ Copia el número después de 'Id:'</p>
                                </div>
                                
                                <div class="p-3 bg-green-50 rounded-lg">
                                    <p class="font-bold text-green-800">Paso 3: Configurar aquí</p>
                                    <p class="text-sm text-green-600 mt-2">Pega el Token y Chat ID en el formulario →</p>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Formulario -->
                        <div class="glass-panel rounded-xl p-6">
                            <h3 class="font-bold text-lg mb-4 flex items-center gap-2">
                                <i class="fas fa-cog text-green-500"></i>Configuración
                            </h3>
                            
                            <div id="telegram-status" class="mb-4">
                                <span class="px-3 py-1 bg-gray-200 text-gray-600 rounded-full text-sm">
                                    <i class="fas fa-circle mr-1"></i>No configurado
                                </span>
                            </div>
                            
                            <form id="telegram-form" class="space-y-4">
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-1">Nombre del Bot</label>
                                    <input type="text" id="telegram-bot-name" placeholder="MiIA Bot" 
                                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                                </div>
                                
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-1">
                                        Bot Token <span class="text-red-500">*</span>
                                    </label>
                                    <div class="relative">
                                        <input type="password" id="telegram-token" placeholder="123456789:ABCdefGHIjkl..." 
                                            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm">
                                        <button type="button" onclick="togglePassword('telegram-token')" class="absolute right-2 top-2 text-gray-400 hover:text-gray-600">
                                            <i class="fas fa-eye"></i>
                                        </button>
                                    </div>
                                    <p class="text-xs text-gray-500 mt-1">Ejemplo: 123456789:ABCdefGHIjklMNOpqrSTUvwxyz</p>
                                </div>
                                
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-1">
                                        Chat ID <span class="text-red-500">*</span>
                                    </label>
                                    <input type="text" id="telegram-chat-id" placeholder="123456789" 
                                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono">
                                    <p class="text-xs text-gray-500 mt-1">Tu número de usuario de Telegram</p>
                                </div>
                                
                                <div class="flex gap-2 pt-4">
                                    <button type="button" onclick="saveTelegramConfig()" 
                                        class="flex-1 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium">
                                        <i class="fas fa-save mr-2"></i>Guardar Configuración
                                    </button>
                                </div>
                                
                                <div id="telegram-actions" class="hidden flex gap-2">
                                    <button type="button" onclick="updateTelegramToken()" 
                                        class="flex-1 px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-white rounded-lg text-sm">
                                        <i class="fas fa-sync-alt mr-2"></i>Cambiar Token
                                    </button>
                                    <button type="button" onclick="deleteTelegramConfig()" 
                                        class="flex-1 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg text-sm">
                                        <i class="fas fa-trash mr-2"></i>Eliminar
                                    </button>
                                </div>
                            </form>
                            
                            <div id="telegram-message" class="mt-4 hidden"></div>
                        </div>
                    </div>
                </div>
                
                <!-- WhatsApp Tab -->
                <div id="bot-tab-whatsapp" class="bot-tab hidden">
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <!-- Guía -->
                        <div class="glass-panel rounded-xl p-6">
                            <h3 class="font-bold text-lg mb-4 flex items-center gap-2">
                                <i class="fas fa-book text-green-500"></i>Guía WhatsApp Business API
                            </h3>
                            
                            <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                                <h4 class="font-bold text-yellow-700 mb-2"><i class="fas fa-exclamation-triangle mr-2"></i>⚠️ Requisitos Importantes</h4>
                                <ul class="text-sm text-yellow-600 space-y-1">
                                    <li>• Requiere cuenta de Meta Business</li>
                                    <li>• Número de teléfono dedicado (NO usar tu personal)</li>
                                    <li>• Proceso de verificación puede tardar días</li>
                                    <li>🔒 MiIA encriptará todas las credenciales</li>
                                </ul>
                            </div>
                            
                            <div class="space-y-4">
                                <div class="p-3 bg-green-50 rounded-lg">
                                    <p class="font-bold text-green-800">Paso 1: Meta Business</p>
                                    <ol class="text-sm text-green-600 mt-2 ml-4 space-y-1">
                                        <li>1. Ve a: <a href="https://business.facebook.com" target="_blank" class="underline">business.facebook.com</a></li>
                                        <li>2. Crea cuenta de Meta Business</li>
                                        <li>3. Verifica con documento de identidad</li>
                                    </ol>
                                    <p class="text-sm text-green-600 mt-2">✅ Obtendrás Business Account ID</p>
                                </div>
                                
                                <div class="p-3 bg-green-50 rounded-lg">
                                    <p class="font-bold text-green-800">Paso 2: WhatsApp Business</p>
                                    <ol class="text-sm text-green-600 mt-2 ml-4 space-y-1">
                                        <li>1. En Meta Business Suite → Configuración</li>
                                        <li>2. Canales → WhatsApp</li>
                                        <li>3. Agrega número de teléfono dedicado</li>
                                        <li>4. Verifica por SMS</li>
                                    </ol>
                                    <p class="text-sm text-green-600 mt-2">✅ Obtendrás Phone Number ID</p>
                                </div>
                                
                                <div class="p-3 bg-green-50 rounded-lg">
                                    <p class="font-bold text-green-800">Paso 3: Access Token</p>
                                    <ol class="text-sm text-green-600 mt-2 ml-4 space-y-1">
                                        <li>1. Ve a: <a href="https://developers.facebook.com" target="_blank" class="underline">developers.facebook.com</a></li>
                                        <li>2. Crea app tipo 'Business'</li>
                                        <li>3. Agrega producto 'WhatsApp'</li>
                                        <li>4. Genera token permanente</li>
                                    </ol>
                                    <p class="text-xs text-red-500 mt-2">⚠️ El token temporal expira en 24h</p>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Formulario WhatsApp -->
                        <div class="glass-panel rounded-xl p-6">
                            <h3 class="font-bold text-lg mb-4 flex items-center gap-2">
                                <i class="fas fa-cog text-green-500"></i>Configuración WhatsApp
                            </h3>
                            
                            <div id="whatsapp-status" class="mb-4">
                                <span class="px-3 py-1 bg-gray-200 text-gray-600 rounded-full text-sm">
                                    <i class="fas fa-circle mr-1"></i>No configurado
                                </span>
                            </div>
                            
                            <form id="whatsapp-form" class="space-y-4">
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-1">Phone Number ID</label>
                                    <input type="text" id="whatsapp-phone-id" placeholder="123456789012345" 
                                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 font-mono">
                                </div>
                                
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-1">Business Account ID</label>
                                    <input type="text" id="whatsapp-business-id" placeholder="987654321098765" 
                                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 font-mono">
                                </div>
                                
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-1">Access Token</label>
                                    <div class="relative">
                                        <input type="password" id="whatsapp-token" placeholder="EAABsB..." 
                                            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 font-mono text-sm">
                                        <button type="button" onclick="togglePassword('whatsapp-token')" class="absolute right-2 top-2 text-gray-400 hover:text-gray-600">
                                            <i class="fas fa-eye"></i>
                                        </button>
                                    </div>
                                </div>
                                
                                <div class="flex gap-2 pt-4">
                                    <button type="button" onclick="saveWhatsAppConfig()" 
                                        class="flex-1 px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg font-medium">
                                        <i class="fas fa-save mr-2"></i>Guardar
                                    </button>
                                </div>
                                
                                <div id="whatsapp-actions" class="hidden flex gap-2">
                                    <button type="button" onclick="updateWhatsAppToken()" 
                                        class="flex-1 px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-white rounded-lg text-sm">
                                        <i class="fas fa-sync-alt mr-2"></i>Cambiar Token
                                    </button>
                                    <button type="button" onclick="deleteWhatsAppConfig()" 
                                        class="flex-1 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg text-sm">
                                        <i class="fas fa-trash mr-2"></i>Eliminar
                                    </button>
                                </div>
                            </form>
                            
                            <div id="whatsapp-message" class="mt-4 hidden"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- LLM Config Panel -->
            <div id="panel-llm" class="panel">
                <h2 class="text-2xl font-bold mb-6 text-gray-800">Configuración de IA</h2>
                
                <div class="mb-6">
                    <h3 class="text-lg font-semibold mb-3 flex items-center gap-2">
                        <i class="fas fa-laptop text-green-500"></i>APIs Locales (Gratis)
                    </h3>
                    <div class="glass-panel rounded-xl p-5 card-hover">
                        <div class="flex items-center justify-between mb-4">
                            <div class="flex items-center gap-3">
                                <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                                    <i class="fas fa-server text-green-600 text-xl"></i>
                                </div>
                                <div>
                                    <h4 class="font-bold">Ollama</h4>
                                    <p class="text-sm text-gray-500">Modelos locales en tu PC</p>
                                </div>
                            </div>
                            <span id="ollama-status" class="px-3 py-1 bg-gray-200 text-gray-600 rounded-full text-sm">Verificando...</span>
                        </div>
                        <div class="flex gap-2">
                            <button onclick="checkOllama()" class="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm">
                                <i class="fas fa-sync-alt mr-1"></i>Verificar
                            </button>
                            <a href="https://ollama.com/download" target="_blank" class="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg text-sm inline-flex items-center">
                                <i class="fas fa-download mr-1"></i>Descargar
                            </a>
                        </div>
                    </div>
                </div>
                
                <div>
                    <h3 class="text-lg font-semibold mb-3 flex items-center gap-2">
                        <i class="fas fa-cloud text-purple-500"></i>APIs en la Nube
                    </h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        <div class="glass-panel rounded-xl p-4 card-hover">
                            <div class="flex items-center gap-3 mb-3">
                                <div class="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                                    <i class="fas fa-brain text-purple-600"></i>
                                </div>
                                <div>
                                    <h4 class="font-bold">OpenAI</h4>
                                    <p class="text-xs text-gray-500">GPT-4o, GPT-4o Mini</p>
                                </div>
                            </div>
                            <button onclick="toggleCloudConfig('openai')" class="w-full px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm">Configurar</button>
                            <div id="cloud-config-openai" class="hidden mt-3 space-y-2">
                                <input type="password" id="openai-api-key" placeholder="OPENAI_API_KEY" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono">
                                <div class="flex gap-2">
                                    <button onclick="saveCloudKey('openai')" class="flex-1 px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm">Guardar</button>
                                    <button onclick="activateProvider('openai')" class="flex-1 px-3 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg text-sm">Activar</button>
                                </div>
                            </div>
                        </div>
                        <div class="glass-panel rounded-xl p-4 card-hover">
                            <div class="flex items-center gap-3 mb-3">
                                <div class="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
                                    <i class="fas fa-bolt text-yellow-600"></i>
                                </div>
                                <div>
                                    <h4 class="font-bold">Groq</h4>
                                    <p class="text-xs text-gray-500">Ultra rápido</p>
                                </div>
                            </div>
                            <button onclick="toggleCloudConfig('groq')" class="w-full px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm">Configurar</button>
                            <div id="cloud-config-groq" class="hidden mt-3 space-y-2">
                                <input type="password" id="groq-api-key" placeholder="GROQ_API_KEY" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono">
                                <div class="flex gap-2">
                                    <button onclick="saveCloudKey('groq')" class="flex-1 px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm">Guardar</button>
                                    <button onclick="activateProvider('groq')" class="flex-1 px-3 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg text-sm">Activar</button>
                                </div>
                                <p class="text-xs text-gray-500">Key: https://console.groq.com/keys</p>
                            </div>
                        </div>
                        <div class="glass-panel rounded-xl p-4 card-hover">
                            <div class="flex items-center gap-3 mb-3">
                                <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                                    <i class="fas fa-robot text-blue-600"></i>
                                </div>
                                <div>
                                    <h4 class="font-bold">Gemini</h4>
                                    <p class="text-xs text-gray-500">Google AI</p>
                                </div>
                            </div>
                            <button onclick="toggleCloudConfig('gemini')" class="w-full px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm">Configurar</button>
                            <div id="cloud-config-gemini" class="hidden mt-3 space-y-2">
                                <input type="password" id="gemini-api-key" placeholder="GEMINI_API_KEY" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono">
                                <div class="flex gap-2">
                                    <button onclick="saveCloudKey('gemini')" class="flex-1 px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm">Guardar</button>
                                    <button onclick="activateProvider('gemini')" class="flex-1 px-3 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg text-sm">Activar</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Skills Panel -->
            <div id="panel-skills" class="panel">
                <h2 class="text-2xl font-bold mb-6 text-gray-800">Gestión de Skills</h2>
                
                <!-- Tabs de Skills -->
                <div class="flex gap-2 mb-6 border-b">
                    <button onclick="showSkillsTab('my-skills')" id="skills-tab-my" onclick="showSkillsTab('my-skills')" class="px-4 py-2 bg-blue-500 text-white rounded-t-lg font-medium">
                        <i class="fas fa-cubes mr-2"></i>Mis Skills
                    </button>
                    <button onclick="showSkillsTab('wizard')" id="skills-tab-wizard" onclick="showSkillsTab('wizard')" class="px-4 py-2 bg-gray-200 text-gray-700 rounded-t-lg">
                        <i class="fas fa-magic mr-2"></i>Crear Skill (Wizard)
                    </button>
                    <button onclick="showSkillsTab('editor')" id="skills-tab-editor" onclick="showSkillsTab('editor')" class="px-4 py-2 bg-gray-200 text-gray-700 rounded-t-lg">
                        <i class="fas fa-code mr-2"></i>Editor Avanzado
                    </button>
                    <button onclick="showSkillsTab('marketplace')" id="skills-tab-market" onclick="showSkillsTab('marketplace')" class="px-4 py-2 bg-gray-200 text-gray-700 rounded-t-lg">
                        <i class="fas fa-store mr-2"></i>Marketplace
                    </button>
                    <button onclick="showSkillsTab('creaciones')" id="skills-tab-creaciones" onclick="showSkillsTab('creaciones')" class="px-4 py-2 bg-gray-200 text-gray-700 rounded-t-lg">
                        <i class="fas fa-folder-open mr-2"></i>Mis Creaciones
                    </button>
                </div>
                
                <!-- Tab: Mis Skills -->
                <div id="skills-content-my-skills" class="skills-tab-content">
                    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <div class="lg:col-span-2 space-y-4" id="user-skills-list">
                            <div class="glass-panel rounded-xl p-5 card-hover">
                                <div class="flex items-start justify-between">
                                    <div class="flex items-center gap-3">
                                        <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                                            <i class="fas fa-robot text-blue-600"></i>
                                        </div>
                                        <div>
                                            <h4 class="font-bold">pc_control</h4>
                                            <p class="text-sm text-gray-500">Control de PC por voz</p>
                                        </div>
                                    </div>
                                    <span class="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">Activo</span>
                                </div>
                            </div>
                            <div class="glass-panel rounded-xl p-5 card-hover border-dashed border-2 border-gray-300 cursor-pointer hover:border-blue-400" onclick="showSkillsTab('wizard')">
                                <div class="flex items-center justify-center h-20 text-gray-400">
                                    <div class="text-center">
                                        <i class="fas fa-plus-circle text-3xl mb-2"></i>
                                        <p>Crear nuevo skill</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="glass-panel rounded-xl p-5">
                            <h3 class="font-bold mb-4">Información</h3>
                            <p class="text-sm text-gray-600 mb-4">Los skills extienden las capacidades de MiIA.</p>
                            <div class="space-y-2 text-sm mb-4">
                                <div class="flex justify-between"><span class="text-gray-500">Instalados:</span><span class="font-medium" id="skills-count">1</span></div>
                                <div class="flex justify-between"><span class="text-gray-500">Activos:</span><span class="font-medium text-green-600">1</span></div>
                            </div>
                            
                            <!-- Panel de Skills en Ejecución -->
                            <div class="border-t pt-4 mt-4">
                                <h4 class="font-bold mb-3 flex items-center gap-2">
                                    <i class="fas fa-spinner fa-spin text-blue-500"></i>
                                    Skills en Ejecución
                                    <span id="running-count" class="ml-auto px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded">0</span>
                                </h4>
                                <div id="running-skills-panel" class="space-y-2 max-h-64 overflow-y-auto">
                                    <p class="text-gray-400 text-sm">No hay skills en ejecución</p>
                                </div>
                            </div>
                            
                            <div class="p-3 bg-yellow-50 rounded-lg border border-yellow-200 mt-4">
                                <p class="text-xs text-yellow-800">
                                    <i class="fas fa-shield-alt mr-1"></i>
                                    Todos los skills pasan por el <strong>Sandbox de Seguridad</strong> antes de ejecutarse.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Tab: Wizard -->
                <div id="skills-content-wizard" class="skills-tab-content hidden">
                    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <div class="lg:col-span-2">
                            <div class="glass-panel rounded-xl p-6">
                                <h3 class="font-bold text-lg mb-4 flex items-center gap-2">
                                    <i class="fas fa-magic text-purple-500"></i>Wizard de Skills
                                </h3>
                                <p class="text-sm text-gray-600 mb-4">Crea un skill sin escribir código. Elige una plantilla y personalízala.</p>
                                
                                <!-- Paso 1: Plantilla -->
                                <div id="wizard-step-1" class="wizard-step">
                                    <h4 class="font-medium mb-3">1. Selecciona una plantilla:</h4>
                                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
                                        <button onclick="selectTemplate('echo')" class="template-btn p-4 border rounded-lg hover:border-blue-400 hover:bg-blue-50 text-left">
                                            <div class="flex items-center gap-3">
                                                <i class="fas fa-comment-dots text-blue-500 text-xl"></i>
                                                <div>
                                                    <p class="font-medium">Echo / Mensaje</p>
                                                    <p class="text-xs text-gray-500">Responde con un mensaje fijo</p>
                                                </div>
                                            </div>
                                        </button>
                                        <button onclick="selectTemplate('calculator')" class="template-btn p-4 border rounded-lg hover:border-blue-400 hover:bg-blue-50 text-left">
                                            <div class="flex items-center gap-3">
                                                <i class="fas fa-calculator text-green-500 text-xl"></i>
                                                <div>
                                                    <p class="font-medium">Calculadora</p>
                                                    <p class="text-xs text-gray-500">Operaciones matemáticas</p>
                                                </div>
                                            </div>
                                        </button>
                                        <button onclick="selectTemplate('reminder')" class="template-btn p-4 border rounded-lg hover:border-blue-400 hover:bg-blue-50 text-left">
                                            <div class="flex items-center gap-3">
                                                <i class="fas fa-bell text-yellow-500 text-xl"></i>
                                                <div>
                                                    <p class="font-medium">Recordatorio</p>
                                                    <p class="text-xs text-gray-500">Crea recordatorios</p>
                                                </div>
                                            </div>
                                        </button>
                                        <button onclick="selectTemplate('web_search')" class="template-btn p-4 border rounded-lg hover:border-blue-400 hover:bg-blue-50 text-left">
                                            <div class="flex items-center gap-3">
                                                <i class="fas fa-search text-purple-500 text-xl"></i>
                                                <div>
                                                    <p class="font-medium">Búsqueda Web</p>
                                                    <p class="text-xs text-gray-500">Busca información online</p>
                                                </div>
                                            </div>
                                        </button>
                                    </div>
                                </div>
                                
                                <!-- Paso 2: Configuración -->
                                <div id="wizard-step-2" class="wizard-step hidden">
                                    <h4 class="font-medium mb-3">2. Configura tu skill:</h4>
                                    <div class="space-y-4">
                                        <div>
                                            <label class="block text-sm font-medium text-gray-700 mb-1">Nombre del Skill</label>
                                            <input type="text" id="skill-name" placeholder="mi_skill" class="w-full px-3 py-2 border rounded-lg" oninput="validateSkillId()">
                                            <p class="text-xs text-gray-500 mt-1">ID: <span id="skill-id-preview">mi_skill</span></p>
                                        </div>
                                        <div>
                                            <label class="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
                                            <textarea id="skill-description" rows="2" placeholder="¿Qué hace este skill?" class="w-full px-3 py-2 border rounded-lg"></textarea>
                                        </div>
                                        <div>
                                            <label class="block text-sm font-medium text-gray-700 mb-1">Mensaje/Acción</label>
                                            <textarea id="skill-message" rows="3" placeholder="Mensaje que mostrará o acción que realizará..." class="w-full px-3 py-2 border rounded-lg"></textarea>
                                        </div>
                                        <div>
                                            <label class="block text-sm font-medium text-gray-700 mb-1">Permisos requeridos</label>
                                            <div class="space-y-2">
                                                <label class="flex items-center gap-2">
                                                    <input type="checkbox" id="perm-fs-read" class="rounded">
                                                    <span class="text-sm">Leer archivos</span>
                                                </label>
                                                <label class="flex items-center gap-2">
                                                    <input type="checkbox" id="perm-fs-write" class="rounded">
                                                    <span class="text-sm">Escribir archivos</span>
                                                </label>
                                                <label class="flex items-center gap-2">
                                                    <input type="checkbox" id="perm-network" class="rounded">
                                                    <span class="text-sm">Acceso a internet</span>
                                                </label>
                                                <label class="flex items-center gap-2">
                                                    <input type="checkbox" id="perm-credentials" class="rounded">
                                                    <span class="text-sm">🔐 Acceder a credenciales (requiere aprobación)</span>
                                                </label>
                                            </div>
                                            <p class="text-xs text-yellow-600 mt-2">
                                                <i class="fas fa-shield-alt mr-1"></i>
                                                Las credenciales se proporcionan temporalmente y se eliminan automáticamente después del uso.
                                            </p>
                                        </div>
                                    </div>
                                    <div class="flex gap-2 mt-4">
                                        <button onclick="wizardPrevStep(1)" class="px-4 py-2 bg-gray-200 rounded-lg">← Atrás</button>
                                        <button onclick="wizardNextStep(3)" class="px-4 py-2 bg-blue-500 text-white rounded-lg">Siguiente →</button>
                                    </div>
                                </div>
                                
                                <!-- Paso 3: Review y Test -->
                                <div id="wizard-step-3" class="wizard-step hidden">
                                    <h4 class="font-medium mb-3">3. Revisa y prueba:</h4>
                                    <div class="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm mb-4 overflow-x-auto">
                                        <pre id="skill-code-preview"># El código generado aparecerá aquí...</pre>
                                    </div>
                                    <div class="flex gap-2 mb-4">
                                        <button onclick="testSkillInSandbox()" class="px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-white rounded-lg">
                                            <i class="fas fa-flask mr-2"></i>Probar en Sandbox
                                        </button>
                                        <button onclick="validateSkillCode()" class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg">
                                            <i class="fas fa-check-circle mr-2"></i>Validar Código
                                        </button>
                                    </div>
                                    <div id="sandbox-results" class="hidden p-4 bg-gray-50 rounded-lg mb-4">
                                        <p class="text-sm font-medium mb-2">Resultados del Sandbox:</p>
                                        <div id="sandbox-output" class="text-sm"></div>
                                    </div>
                                    <div class="flex gap-2">
                                        <button onclick="wizardPrevStep(2)" class="px-4 py-2 bg-gray-200 rounded-lg">← Atrás</button>
                                        <button onclick="saveWizardSkill()" class="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg">
                                            <i class="fas fa-save mr-2"></i>Guardar Skill
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="glass-panel rounded-xl p-5">
                            <h3 class="font-bold mb-4">Ejemplos</h3>
                            <div class="space-y-3 text-sm">
                                <button onclick="loadExample('hola')" class="w-full text-left p-3 bg-blue-50 rounded-lg hover:bg-blue-100">
                                    <p class="font-medium">👋 Saludo simple</p>
                                    <p class="text-xs text-gray-600">Responde "Hola" con un mensaje amigable</p>
                                </button>
                                <button onclick="loadExample('hora')" class="w-full text-left p-3 bg-green-50 rounded-lg hover:bg-green-100">
                                    <p class="font-medium">🕐 Decir la hora</p>
                                    <p class="text-xs text-gray-600">Informa la hora actual</p>
                                </button>
                                <button onclick="loadExample('clima')" class="w-full text-left p-3 bg-purple-50 rounded-lg hover:bg-purple-100">
                                    <p class="font-medium">🌤️ Consultar clima</p>
                                    <p class="text-xs text-gray-600">Necesita permiso de red</p>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Tab: Editor Avanzado -->
                <div id="skills-content-editor" class="skills-tab-content hidden">
                    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <div class="lg:col-span-2">
                            <div class="glass-panel rounded-xl p-6">
                                <h3 class="font-bold text-lg mb-4 flex items-center gap-2">
                                    <i class="fas fa-code text-orange-500"></i>Editor Avanzado
                                </h3>
                                <p class="text-sm text-gray-600 mb-4">Escribe código Python para crear skills personalizados. El código se ejecuta en un sandbox seguro.</p>
                                
                                <!-- Editor de código -->
                                <div class="mb-4">
                                    <div class="flex items-center justify-between mb-2">
                                        <label class="text-sm font-medium text-gray-700">skill.py</label>
                                        <div class="flex gap-2">
                                            <button onclick="formatCode()" class="px-2 py-1 text-xs bg-gray-200 rounded hover:bg-gray-300">
                                                <i class="fas fa-align-left mr-1"></i>Formatear
                                            </button>
                                            <button onclick="clearEditor()" class="px-2 py-1 text-xs bg-red-100 text-red-600 rounded hover:bg-red-200">
                                                <i class="fas fa-trash mr-1"></i>Limpiar
                                            </button>
                                        </div>
                                    </div>
                                    <textarea id="advanced-code-editor" rows="20" class="w-full px-4 py-3 bg-gray-900 text-green-400 font-mono text-sm rounded-lg resize-y" placeholder="# Escribe tu código Python aquí
def execute(context):
    # Función principal del skill.
    # context: dict con información de la tarea
    task = context.get('task', '')
    
    # Tu lógica aquí
    result = f"Procesando: {task}"
    
    return {
        'success': True,
        'message': result,
        'data': {}
    }"></textarea>
                                </div>
                                
                                <!-- Configuración del skill -->
                                <div class="grid grid-cols-2 gap-4 mb-4">
                                    <div>
                                        <label class="block text-sm font-medium text-gray-700 mb-1">ID del Skill</label>
                                        <input type="text" id="advanced-skill-id" placeholder="mi_skill_avanzado" class="w-full px-3 py-2 border rounded-lg font-mono text-sm">
                                    </div>
                                    <div>
                                        <label class="block text-sm font-medium text-gray-700 mb-1">Nombre</label>
                                        <input type="text" id="advanced-skill-name" placeholder="Mi Skill Avanzado" class="w-full px-3 py-2 border rounded-lg">
                                    </div>
                                </div>
                                <div class="mb-4">
                                    <label class="block text-sm font-medium text-gray-700 mb-1">Versión</label>
                                    <input type="text" id="advanced-skill-version" value="1.0.0" class="w-full px-3 py-2 border rounded-lg font-mono text-sm">
                                </div>
                                <div class="mb-4">
                                    <label class="block text-sm font-medium text-gray-700 mb-2">Permisos</label>
                                    <div class="flex flex-wrap gap-2">
                                        <label class="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg cursor-pointer">
                                            <input type="checkbox" id="adv-perm-fs-read" class="rounded">
                                            <span class="text-sm">fs_read</span>
                                        </label>
                                        <label class="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg cursor-pointer">
                                            <input type="checkbox" id="adv-perm-fs-write" class="rounded">
                                            <span class="text-sm">fs_write</span>
                                        </label>
                                        <label class="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg cursor-pointer">
                                            <input type="checkbox" id="adv-perm-network" class="rounded">
                                            <span class="text-sm">network</span>
                                        </label>
                                        <label class="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg cursor-pointer">
                                            <input type="checkbox" id="adv-perm-ui" class="rounded">
                                            <span class="text-sm">ui_access</span>
                                        </label>
                                    </div>
                                </div>
                                
                                <!-- Botones de acción -->
                                <div class="flex gap-2">
                                    <button onclick="validateAdvancedCode()" class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg">
                                        <i class="fas fa-check-circle mr-2"></i>Validar
                                    </button>
                                    <button onclick="testAdvancedInSandbox()" class="px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-white rounded-lg">
                                        <i class="fas fa-flask mr-2"></i>Test Sandbox
                                    </button>
                                    <button onclick="saveAdvancedSkill()" class="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg">
                                        <i class="fas fa-save mr-2"></i>Guardar Skill
                                    </button>
                                </div>
                                
                                <!-- Resultados de validación -->
                                <div id="validation-results" class="hidden mt-4 p-4 border-t bg-yellow-50">
                                    <p class="text-sm font-medium mb-2">Resultados de validación:</p>
                                    <div id="validation-issues" class="space-y-1 text-sm"></div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- AI Chat Sidebar -->
                        <div class="w-full border-l bg-gray-50 flex flex-col h-full" style="min-height: 600px;">
                            <!-- Header -->
                            <div class="p-3 border-b bg-white">
                                <div class="flex items-center gap-2">
                                    <i class="fas fa-robot text-purple-600"></i>
                                    <span class="font-bold text-sm">Asistente IA</span>
                                    <span id="ai-provider-badge" class="ml-auto px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded">🦙 Ollama</span>
                                </div>
                            </div>
                            
                            <!-- Chat Messages -->
                            <div id="ai-chat-messages" class="flex-1 overflow-y-auto p-3 space-y-3" style="max-height: 400px;">
                                <div class="ai-message bg-purple-100 rounded-lg p-3 text-sm">
                                    <p class="font-medium text-purple-700 mb-1">🤖 Asistente</p>
                                    <p class="text-gray-700">¡Hola! Soy tu asistente de programación. Escribe lo que necesitas y te ayudaré con el código de tu skill. Estoy usando <strong>Ollama (gratis)</strong> por defecto.</p>
                                </div>
                            </div>
                            
                            <!-- Quick Actions -->
                            <div class="p-2 border-t bg-white">
                                <div class="flex flex-wrap gap-1 mb-2">
                                    <button onclick="askAI('Corrige errores')" class="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200">🔧 Corregir</button>
                                    <button onclick="askAI('Mejora el código')" class="px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200">✨ Mejorar</button>
                                    <button onclick="askAI('Añade documentación')" class="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200">📚 Documentar</button>
                                    <button onclick="askAI('Optimiza')" class="px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded hover:bg-purple-200">🚀 Optimizar</button>
                                </div>
                            </div>
                            
                            <!-- Chat Input with Provider Selector -->
                            <div class="p-3 border-t bg-white">
                                <textarea id="ai-chat-input" class="w-full px-3 py-2 text-sm border rounded resize-none mb-2" rows="2" placeholder="Pide cambios, explica tu idea..."></textarea>
                                <div class="flex gap-2 items-center">
                                    <select id="ai-provider-select" class="flex-1 px-2 py-1.5 text-xs border rounded bg-gray-50">
                                        <option value="ollama" selected>🦙 Ollama (Gratis/Local)</option>
                                        <option value="openai">🧠 OpenAI (GPT-4o)</option>
                                        <option value="gemini">🔷 Gemini (Google)</option>
                                        <option value="groq">⚡ Groq (Llama 3)</option>
                                    </select>
                                    <button onclick="sendAIChatMessage()" class="px-4 py-1.5 bg-purple-500 text-white rounded hover:bg-purple-600 text-sm">
                                        <i class="fas fa-paper-plane mr-1"></i> Enviar
                                    </button>
                                </div>
                                <p class="text-xs text-gray-500 mt-1">💡 Cambia de IA aquí mismo ↓</p>
                            </div>
                            
                            <!-- Pending Changes -->
                            <div id="pending-changes" class="hidden p-3 border-t bg-yellow-50">
                                <p class="text-sm font-medium text-yellow-700 mb-2">📋 Cambios sugeridos:</p>
                                <div id="pending-changes-list" class="space-y-2"></div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Tab: Marketplace -->
                <div id="skills-content-marketplace" class="skills-tab-content hidden">
                    <div class="mb-4 flex items-center justify-between">
                        <h3 class="text-lg font-semibold">Skills de la Comunidad</h3>
                        <button onclick="loadMarketplace()" class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm">
                            <i class="fas fa-sync-alt mr-2"></i>Actualizar
                        </button>
                    </div>
                    <div id="marketplace-list" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        <!-- Skills se cargarán aquí -->
                    </div>
                    <div id="marketplace-loading" class="hidden text-center py-12">
                        <i class="fas fa-spinner fa-spin text-3xl text-blue-500 mb-4"></i>
                        <p class="text-gray-500">Cargando marketplace...</p>
                    </div>
                </div>
                
                <!-- Tab: Mis Creaciones -->
                <div id="skills-content-creaciones" class="skills-tab-content hidden">
                    <div class="mb-4 flex items-center justify-between">
                        <div>
                            <h3 class="text-xl font-bold text-gray-800">Mis Creaciones</h3>
                            <p class="text-sm text-gray-500">Tus archivos generados organizados por categoría</p>
                        </div>
                        <button onclick="loadCreaciones()" class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm">
                            <i class="fas fa-sync-alt mr-2"></i>Actualizar
                        </button>
                    </div>
                    
                    <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
                        <div class="glass-panel rounded-xl p-4 text-center">
                            <div class="w-10 h-10 bg-pink-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                                <i class="fas fa-image text-pink-600"></i>
                            </div>
                            <p class="text-2xl font-bold text-gray-800" id="count-imagenes">0</p>
                            <p class="text-xs text-gray-500">Imágenes</p>
                        </div>
                        <div class="glass-panel rounded-xl p-4 text-center">
                            <div class="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                                <i class="fas fa-file-alt text-green-600"></i>
                            </div>
                            <p class="text-2xl font-bold text-gray-800" id="count-texto">0</p>
                            <p class="text-xs text-gray-500">Textos</p>
                        </div>
                        <div class="glass-panel rounded-xl p-4 text-center">
                            <div class="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                                <i class="fas fa-video text-red-600"></i>
                            </div>
                            <p class="text-2xl font-bold text-gray-800" id="count-video">0</p>
                            <p class="text-xs text-gray-500">Videos</p>
                        </div>
                        <div class="glass-panel rounded-xl p-4 text-center">
                            <div class="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                                <i class="fas fa-music text-yellow-600"></i>
                            </div>
                            <p class="text-2xl font-bold text-gray-800" id="count-audio">0</p>
                            <p class="text-xs text-gray-500">Audio</p>
                        </div>
                        <div class="glass-panel rounded-xl p-4 text-center">
                            <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                                <i class="fas fa-file-word text-blue-600"></i>
                            </div>
                            <p class="text-2xl font-bold text-gray-800" id="count-documentos">0</p>
                            <p class="text-xs text-gray-500">Documentos</p>
                        </div>
                        <div class="glass-panel rounded-xl p-4 text-center">
                            <div class="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                                <i class="fas fa-briefcase text-purple-600"></i>
                            </div>
                            <p class="text-2xl font-bold text-gray-800" id="count-trabajos">0</p>
                            <p class="text-xs text-gray-500">Trabajos</p>
                        </div>
                    </div>
                    
                    <div class="space-y-4" id="creaciones-container">
                        <div class="glass-panel rounded-xl p-4">
                            <p class="text-center text-gray-500">Cargando archivos...</p>
                        </div>
                    </div>
                    
                    <div class="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                        <p class="text-sm text-blue-700">
                            <i class="fas fa-info-circle mr-2"></i>
                            <strong>Ubicación:</strong> Tus archivos se guardan en <code>C:\MiIA-Product-20-Data\output\</code>
                        </p>
                    </div>
                </div>
            </div>
            
            <!-- Chat Panel -->
            <div id="panel-chat" class="panel">
                <h2 class="text-2xl font-bold mb-6 text-gray-800">Chat con MiIA</h2>
                
                <div class="glass-panel rounded-xl p-6 h-[calc(100vh-200px)] flex flex-col">
                    <!-- Mensajes -->
                    <div id="chat-messages" class="flex-1 overflow-y-auto space-y-4 mb-4 p-4 bg-gray-50 rounded-lg">
                        <div class="flex gap-3">
                            <div class="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
                                <i class="fas fa-robot text-white"></i>
                            </div>
                            <div class="bg-blue-100 rounded-lg p-3 max-w-[80%]">
                                <p class="text-sm text-blue-800">¡Hola! Soy MiIA. ¿En qué puedo ayudarte hoy?</p>
                                <span class="text-xs text-blue-400 mt-1 block">Ahora</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Input -->
                    <div class="flex gap-3">
                        <button id="chat-voice-btn" onclick="toggleVoice()" class="px-4 py-3 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg transition-all" title="Activar voz permanente">
                            <i class="fas fa-microphone"></i>
                        </button>
                        <input 
                            type="text" 
                            id="chat-input" 
                            placeholder="Escribe tu mensaje..." 
                            class="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            onkeypress="if(event.key==='Enter')sendChat()"
                        >
                        <button onclick="sendChat()" class="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- Update Panel -->
            <div id="panel-update" class="panel">
                <h2 class="text-2xl font-bold mb-6 text-gray-800">Actualización de MiIA</h2>
                
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- Estado de versión -->
                    <div class="glass-panel rounded-xl p-6">
                        <h3 class="font-bold text-lg mb-4 flex items-center gap-2">
                            <i class="fas fa-info-circle text-blue-500"></i>Estado Actual
                        </h3>
                        
                        <div id="update-status-container" class="space-y-4">
                            <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                                <span class="text-gray-600">Versión instalada:</span>
                                <span id="current-version" class="font-mono font-bold text-gray-800">Cargando...</span>
                            </div>
                            
                            <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                                <span class="text-gray-600">Última versión:</span>
                                <span id="latest-version" class="font-mono font-bold text-blue-600">Cargando...</span>
                            </div>
                            
                            <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                                <span class="text-gray-600">Canal de actualización:</span>
                                <span id="update-channel" class="font-bold text-gray-800">Stable</span>
                            </div>
                            
                            <div id="update-available-badge" class="hidden">
                                <div class="p-4 bg-green-100 border border-green-300 rounded-lg">
                                    <div class="flex items-center gap-2 mb-2">
                                        <i class="fas fa-bell text-green-600"></i>
                                        <span class="font-bold text-green-800">¡Actualización disponible!</span>
                                    </div>
                                    <p class="text-sm text-green-700">Hay una nueva versión lista para instalar.</p>
                                </div>
                            </div>
                        </div>
                        
                        <div class="mt-6 flex gap-3">
                            <button onclick="checkForUpdates()" id="btn-check-update" class="flex-1 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium">
                                <i class="fas fa-search mr-2"></i>Buscar Actualizaciones
                            </button>
                        </div>
                        
                        <div id="update-message" class="mt-4 hidden"></div>
                    </div>
                    
                    <!-- Acciones de actualización -->
                    <div class="glass-panel rounded-xl p-6">
                        <h3 class="font-bold text-lg mb-4 flex items-center gap-2">
                            <i class="fas fa-download text-green-500"></i>Acciones
                        </h3>
                        
                        <div id="update-actions" class="space-y-4">
                            <div class="p-4 bg-gray-50 rounded-lg text-center text-gray-500">
                                <i class="fas fa-check-circle text-4xl mb-3 text-green-500"></i>
                                <p>Tienes la última versión instalada</p>
                            </div>
                            
                            <!-- Progreso de descarga (inicialmente oculto) -->
                            <div id="download-progress" class="hidden">
                                <p class="text-sm text-gray-600 mb-2">Descargando actualización...</p>
                                <div class="w-full bg-gray-200 rounded-full h-4">
                                    <div id="progress-bar" class="bg-blue-500 h-4 rounded-full transition-all duration-300" style="width: 0%"></div>
                                </div>
                                <p id="progress-text" class="text-right text-sm text-gray-600 mt-1">0%</p>
                            </div>
                            
                            <!-- Botones de acción -->
                            <div id="action-buttons" class="hidden flex gap-3">
                                <button onclick="downloadUpdate()" id="btn-download" class="flex-1 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium">
                                    <i class="fas fa-download mr-2"></i>Descargar
                                </button>
                            </div>
                            
                            <div id="install-section" class="hidden">
                                <div class="p-4 bg-yellow-50 border border-yellow-200 rounded-lg mb-4">
                                    <p class="text-sm text-yellow-800">
                                        <i class="fas fa-exclamation-triangle mr-2"></i>
                                        <strong>Importante:</strong> Se creará un backup automático antes de instalar.
                                    </p>
                                </div>
                                <button onclick="installUpdate()" id="btn-install" class="w-full px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg font-medium">
                                    <i class="fas fa-rocket mr-2"></i>Instalar Actualización
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Changelog -->
                <div class="glass-panel rounded-xl p-6 mt-6">
                    <h3 class="font-bold text-lg mb-4 flex items-center gap-2">
                        <i class="fas fa-list-alt text-purple-500"></i>Notas de la Versión
                    </h3>
                    <div id="changelog-content" class="prose max-w-none">
                        <p class="text-gray-500 italic">Las notas de versión aparecerán aquí cuando haya una actualización disponible.</p>
                    </div>
                </div>
                
                <!-- Backups -->
                <div class="glass-panel rounded-xl p-6 mt-6">
                    <h3 class="font-bold text-lg mb-4 flex items-center gap-2">
                        <i class="fas fa-archive text-orange-500"></i>Backups Disponibles
                    </h3>
                    <div id="backups-list" class="space-y-2">
                        <p class="text-gray-500 text-sm">No hay backups disponibles.</p>
                    </div>
                    <div class="mt-4 flex gap-3">
                        <button onclick="createBackup()" class="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg text-sm">
                            <i class="fas fa-save mr-2"></i>Crear Backup Manual
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- Backup Panel -->
            <div id="panel-backup" class="panel">
                <h2 class="text-2xl font-bold mb-6 text-gray-800">Configuración de Backup</h2>
                
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- Configuración de Proveedor -->
                    <div class="glass-panel rounded-xl p-6">
                        <h3 class="font-bold text-lg mb-4 flex items-center gap-2">
                            <i class="fas fa-cloud-upload-alt text-blue-500"></i>Destino del Backup
                        </h3>
                        
                        <div class="space-y-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">¿Dónde guardar los backups?</label>
                                <select id="backup-provider" class="w-full px-3 py-2 border border-gray-300 rounded-lg" onchange="showProviderConfig()">
                                    <option value="local">💻 Solo en mi PC (Local)</option>
                                    <option value="google_drive">📁 Google Drive</option>
                                    <option value="dropbox">📦 Dropbox</option>
                                </select>
                            </div>
                            
                            <!-- Config Google Drive -->
                            <div id="google-drive-config" class="hidden space-y-4">
                                <div class="p-4 bg-yellow-50 rounded-lg">
                                    <p class="text-sm font-bold text-yellow-800 mb-2">📋 Sigue estos pasos:</p>
                                    <ol class="list-decimal list-inside text-sm text-yellow-700 space-y-1">
                                        <li>Ir a <a href="https://console.cloud.google.com/apis/credentials" target="_blank" class="underline font-medium">Google Cloud Console</a></li>
                                        <li>Crear nuevo proyecto o seleccionar existente</li>
                                        <li>Habilitar "Google Drive API"</li>
                                        <li>Crear credenciales tipo "Cuenta de servicio" (JSON)</li>
                                        <li>Compartir carpeta de Drive con el email de la cuenta</li>
                                        <li>Copiar y pegar el contenido del archivo JSON aquí:</li>
                                    </ol>
                                </div>
                                <textarea id="google-credentials" rows="6" placeholder="Pega aquí el contenido del archivo JSON de credenciales..." class="w-full px-3 py-2 border rounded-lg text-sm font-mono text-xs"></textarea>
                                <button onclick="verifyGoogleDrive()" class="w-full px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm">
                                    <i class="fas fa-check-circle mr-2"></i>Verificar conexión
                                </button>
                                <div id="google-verify-status" class="hidden text-sm p-2 rounded"></div>
                            </div>
                            
                            <!-- Config Dropbox -->
                            <div id="dropbox-config" class="hidden space-y-4">
                                <div class="p-4 bg-blue-50 rounded-lg">
                                    <p class="text-sm font-bold text-blue-800 mb-2">📋 Sigue estos pasos:</p>
                                    <ol class="list-decimal list-inside text-sm text-blue-700 space-y-1">
                                        <li>Ir a <a href="https://www.dropbox.com/developers/apps" target="_blank" class="underline font-medium">Dropbox App Console</a></li>
                                        <li>Crear nueva app tipo "Scoped access"</li>
                                        <li>En Permisos, activar: files.content.write, files.content.read</li>
                                        <li>Generar "Access token" en Settings</li>
                                        <li>Copiar y pegar el token aquí:</li>
                                    </ol>
                                </div>
                                <input type="password" id="dropbox-token" placeholder="sl.XXXXXXXXXXXXXXXX" class="w-full px-3 py-2 border rounded-lg text-sm">
                                <button onclick="verifyDropbox()" class="w-full px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm">
                                    <i class="fas fa-check-circle mr-2"></i>Verificar conexión
                                </button>
                                <div id="dropbox-verify-status" class="hidden text-sm p-2 rounded"></div>
                            </div>
                            
                            <!-- Config OneDrive -->
                            <div id="onedrive-config" class="hidden space-y-4">
                                <div class="p-4 bg-indigo-50 rounded-lg">
                                    <p class="text-sm font-bold text-indigo-800 mb-2">📋 Sigue estos pasos:</p>
                                    <ol class="list-decimal list-inside text-sm text-indigo-700 space-y-1">
                                        <li>Ir a <a href="https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade" target="_blank" class="underline font-medium">Azure Portal</a></li>
                                        <li>Registrar nueva aplicación</li>
                                        <li>En Permisos, agregar: Files.ReadWrite (Microsoft Graph)</li>
                                        <li>Crear nuevo Client Secret</li>
                                        <li>Copiar Application ID, Client Secret y Tenant ID:</li>
                                    </ol>
                                </div>
                                <input type="text" id="onedrive-client-id" placeholder="Application (client) ID" class="w-full px-3 py-2 border rounded-lg text-sm mb-2">
                                <input type="password" id="onedrive-client-secret" placeholder="Client Secret" class="w-full px-3 py-2 border rounded-lg text-sm mb-2">
                                <input type="text" id="onedrive-tenant-id" placeholder="Tenant ID (o 'common' para personal)" class="w-full px-3 py-2 border rounded-lg text-sm mb-2">
                                <button onclick="verifyOneDrive()" class="w-full px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm">
                                    <i class="fas fa-check-circle mr-2"></i>Verificar conexión
                                </button>
                                <div id="onedrive-verify-status" class="hidden text-sm p-2 rounded"></div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Frecuencia y Opciones -->
                    <div class="glass-panel rounded-xl p-6">
                        <h3 class="font-bold text-lg mb-4 flex items-center gap-2">
                            <i class="fas fa-clock text-green-500"></i>Programación
                        </h3>
                        
                        <div class="space-y-4">
                            <div>
                                <label class="flex items-center gap-2">
                                    <input type="checkbox" id="auto-backup" class="rounded">
                                    <span class="text-sm font-medium">Backup automático</span>
                                </label>
                            </div>
                            
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">Frecuencia</label>
                                <select id="backup-frequency" class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                                    <option value="daily">Todos los días</option>
                                    <option value="weekly" selected>Cada semana</option>
                                    <option value="monthly">Cada mes</option>
                                </select>
                            </div>
                            
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">Hora del backup</label>
                                <input type="time" id="backup-time" value="02:00" class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                                <p class="text-xs text-gray-500 mt-1">Hora local de tu PC</p>
                            </div>
                            
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">Máximo de backups guardados</label>
                                <select id="max-backups" class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                                    <option value="3">3 backups</option>
                                    <option value="5" selected>5 backups</option>
                                    <option value="10">10 backups</option>
                                    <option value="0">Sin límite</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Qué respaldar -->
                <div class="glass-panel rounded-xl p-6 mt-6">
                    <h3 class="font-bold text-lg mb-4 flex items-center gap-2">
                        <i class="fas fa-check-square text-purple-500"></i>¿Qué quieres respaldar?
                    </h3>
                    
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <label class="flex items-center gap-2 p-3 bg-gray-50 rounded-lg cursor-pointer">
                            <input type="checkbox" id="backup-tokens" checked class="rounded">
                            <span class="text-sm">🔑 Tokens y Config</span>
                        </label>
                        
                        <label class="flex items-center gap-2 p-3 bg-gray-50 rounded-lg cursor-pointer">
                            <input type="checkbox" id="backup-skills" checked class="rounded">
                            <span class="text-sm">🧩 Mis Skills</span>
                        </label>
                        
                        <label class="flex items-center gap-2 p-3 bg-gray-50 rounded-lg cursor-pointer">
                            <input type="checkbox" id="backup-settings" checked class="rounded">
                            <span class="text-sm">⚙️ Ajustes</span>
                        </label>
                        
                        <label class="flex items-center gap-2 p-3 bg-gray-50 rounded-lg cursor-pointer">
                            <input type="checkbox" id="backup-history" class="rounded">
                            <span class="text-sm">📜 Historial</span>
                        </label>
                    </div>
                </div>
                
                <!-- Acciones -->
                <div class="glass-panel rounded-xl p-6 mt-6">
                    <div class="flex flex-wrap gap-3">
                        <button onclick="saveBackupConfig()" class="px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium">
                            <i class="fas fa-save mr-2"></i>Guardar Configuración
                        </button>
                        
                        <button onclick="createBackupNow()" class="px-6 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg font-medium">
                            <i class="fas fa-play mr-2"></i>Crear Backup Ahora
                        </button>
                        
                        <button onclick="exportConfig()" class="px-6 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg font-medium">
                            <i class="fas fa-download mr-2"></i>Exportar Configuración
                        </button>
                    </div>
                    
                    <div id="backup-message" class="mt-4 hidden"></div>
                </div>
                
                <!-- Estado y Backups existentes -->
                <div class="glass-panel rounded-xl p-6 mt-6">
                    <h3 class="font-bold text-lg mb-4 flex items-center gap-2">
                        <i class="fas fa-history text-orange-500"></i>Estado y Backups
                    </h3>
                    
                    <div id="backup-status" class="mb-4 p-4 bg-gray-50 rounded-lg">
                        <p class="text-gray-600">Cargando estado...</p>
                    </div>
                    
                    <div id="backup-list" class="space-y-2 max-h-48 overflow-y-auto">
                        <p class="text-gray-500 text-sm">No hay backups disponibles.</p>
                    </div>
                </div>
            </div>
            
            <!-- Logs Panel -->
            <div id="panel-logs" class="panel">
                <h2 class="text-2xl font-bold mb-6 text-gray-800">Logs y Estado</h2>
                <div class="glass-panel rounded-xl p-5">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="font-bold flex items-center gap-2"><i class="fas fa-terminal text-gray-600"></i>Log del Sistema</h3>
                        <div class="flex gap-2">
                            <button onclick="clearLogs()" class="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm">
                                <i class="fas fa-trash"></i> Limpiar
                            </button>
                            <button onclick="loadEvents()" class="px-3 py-1 bg-blue-100 hover:bg-blue-200 text-blue-700 rounded text-sm">
                                <i class="fas fa-sync-alt"></i> Actualizar
                            </button>
                        </div>
                    </div>
                    <div id="system-logs" class="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm h-96 overflow-y-auto">
                        <div class="log-entry">[SYSTEM] MiIA WebUI iniciado...</div>
                    </div>
                </div>
            </div>
            
        </main>
    </div>
    
    <script>
        let ws = null;
        let wsReconnectTimer = null;
        let wsEnabled = true;
        let wsManualClose = false;
        let wsConnecting = false;
        let wsReconnectDelayMs = 1000;
        let wsReconnectAttempts = 0;
        const wsMaxReconnectAttempts = 12;
        
        
        // WebSocket
        function connectWS() {
            if (!wsEnabled) return;
            if (wsConnecting) return;

            if (wsReconnectTimer) {
                clearTimeout(wsReconnectTimer);
                wsReconnectTimer = null;
            }

            // If we already have an open socket, keep it
            try {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    return;
                }
            } catch (e) {
                // ignore
            }

            try {
                if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
                    wsManualClose = true;
                    ws.close();
                }
            } catch (e) {
                // ignore
            }

            wsManualClose = false;
            wsConnecting = true;
            const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
            ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
            
            ws.onopen = () => {
                wsConnecting = false;
                wsReconnectAttempts = 0;
                wsReconnectDelayMs = 1000;
                document.getElementById("ws-status").textContent = "Conectado";
                document.getElementById("ws-status").className = "text-green-500";
                addLog("WebSocket conectado");
            };
            
            ws.onmessage = (e) => {
                const data = JSON.parse(e.data);
                if (data.type === "voice_status") updateVoiceStatus(data.active);
                if (data.type === "log") addLog(data.message);
            };
            
            ws.onclose = () => {
                wsConnecting = false;
                if (!wsEnabled || wsManualClose) {
                    return;
                }
                document.getElementById("ws-status").textContent = "Reconectando...";
                document.getElementById("ws-status").className = "text-yellow-500";
                if (wsEnabled) {
                    wsReconnectAttempts += 1;
                    if (wsReconnectAttempts > wsMaxReconnectAttempts) {
                        wsEnabled = false;
                        document.getElementById("ws-status").textContent = "Desconectado";
                        document.getElementById("ws-status").className = "text-red-500";
                        addLog("WebSocket: demasiados intentos de reconexión, detenido");
                        return;
                    }
                    const delay = Math.min(wsReconnectDelayMs, 15000);
                    wsReconnectDelayMs = Math.min(wsReconnectDelayMs * 2, 15000);
                    wsReconnectTimer = setTimeout(connectWS, delay);
                }
            };

            ws.onerror = () => {
                wsConnecting = false;
            };
        }
        
        // Panel navigation
        function showPanel(id) {
            document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
            document.getElementById("panel-" + id).classList.add("active");
            document.querySelectorAll(".sidebar-item").forEach(item => item.classList.remove("active"));
            document.querySelector(`[data-panel="${id}"]`).classList.add("active");

            // Lazy-load heavy panels to avoid freezing on refresh
            if (id === 'pc') {
                ensurePcExplorerLoaded();
            }
            if (id === 'logs') {
                ensureLogsLoaded();
            }
            if (id === 'bot') {
                ensureBotStatusLoaded();
            }
        }

        let pcExplorerLoaded = false;
        function ensurePcExplorerLoaded() {
            if (pcExplorerLoaded) return;
            pcExplorerLoaded = true;
            loadPcFolder("");
        }

        let logsLoaded = false;
        function ensureLogsLoaded() {
            if (logsLoaded) return;
            logsLoaded = true;
            loadEvents();
        }

        let botStatusLoaded = false;
        function ensureBotStatusLoaded() {
            if (botStatusLoaded) return;
            botStatusLoaded = true;
            try { loadBotStatus(); } catch (e) { /* ignore */ }
        }
        
        // Voice functions with Web Speech API - PERMANENT MODE
        let recognition = null;
        let voiceActive = false;
        
        function initVoiceRecognition() {
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                console.log('Web Speech API not supported');
                return null;
            }
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const rec = new SpeechRecognition();
            rec.lang = 'es-ES';
            rec.continuous = false;
            rec.interimResults = true;
            
            rec.onresult = (event) => {
                const transcript = Array.from(event.results)
                    .map(result => result[0])
                    .map(result => result.transcript)
                    .join('');
                
                if (event.results[0].isFinal) {
                    addChatMessage(transcript, 'user');
                    // Send to backend for processing
                    processVoiceCommand(transcript);
                }
            };
            
            rec.onerror = (event) => {
                console.error('Voice error:', event.error);
                if (event.error !== 'no-speech') {
                    addLog('Error de voz: ' + event.error);
                }
                // Restart automatically on error if still active
                if (voiceActive) {
                    setTimeout(() => restartVoiceRecognitionDebounced(), 500);
                }
            };
            
            rec.onend = () => {
                // Restart automatically if voice is still active (permanent mode)
                if (voiceActive) {
                    setTimeout(() => restartVoiceRecognitionDebounced(), 200);
                }
            };
            
            return rec;
        }
        
        function restartVoiceRecognition() {
            if (!voiceActive) return;
            try {
                if (recognition) {
                    recognition.start();
                    updateVoiceIndicator(true);
                }
            } catch (e) {
                console.log('Restart failed:', e);
                setTimeout(() => restartVoiceRecognition(), 500);
            }
        }

        let lastVoiceRestartMs = 0;
        function restartVoiceRecognitionDebounced() {
            const now = Date.now();
            if (now - lastVoiceRestartMs < 1000) return;
            lastVoiceRestartMs = now;
            restartVoiceRecognition();
        }
        
        function updateVoiceIndicator(active) {
            const btn = document.getElementById('chat-voice-btn');
            const icon = btn ? btn.querySelector('i') : null;
            if (btn && icon) {
                if (active) {
                    btn.classList.replace('bg-gray-200', 'bg-red-500');
                    btn.classList.replace('hover:bg-gray-300', 'hover:bg-red-600');
                    btn.classList.replace('text-gray-700', 'text-white');
                    icon.classList.add('fa-beat');
                    btn.title = 'Voz activa - Clic para desactivar';
                } else {
                    btn.classList.replace('bg-red-500', 'bg-gray-200');
                    btn.classList.replace('hover:bg-red-600', 'hover:bg-gray-300');
                    btn.classList.replace('text-white', 'text-gray-700');
                    icon.classList.remove('fa-beat');
                    btn.title = 'Activar voz permanente';
                }
            }
        }
        
        async function processVoiceCommand(text) {
            try {
                // First try to execute as command
                const cmdResponse = await fetch("/api/command", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({
                        user_id: "default",
                        command: text,
                        source: "voice"
                    })
                });
                
                const cmdData = await cmdResponse.json();
                
                if (cmdData.success && cmdData.executed) {
                    // Command was executed
                    if (cmdData.response) {
                        addChatMessage(cmdData.response, "bot");
                    }
                    if (cmdData.pc_browse && cmdData.pc_browse.success) {
                        currentPcPath = cmdData.pc_browse.current_path || currentPcPath;
                        const curEl = document.getElementById("current-path");
                        if (curEl && cmdData.pc_browse.current_path) {
                            curEl.textContent = cmdData.pc_browse.current_path;
                        }
                        renderPcItems(cmdData.pc_browse.items || [], cmdData.pc_browse.parent_path);
                    }
                    return;
                }
                
                // If not a command, send to chat API
                const response = await fetch("/api/chat", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({
                        user_id: "default",
                        message: text,
                        source: "voice"
                    })
                });
                const data = await response.json();
                if (data.response) {
                    addChatMessage(data.response, "bot");
                }
            } catch (e) {
                addChatMessage("❌ Error procesando comando: " + e.message, "bot");
            }
        }
        
        function toggleVoice() {
            voiceActive = !voiceActive;
            
            if (voiceActive) {
                // Start voice recognition
                if (!recognition) {
                    recognition = initVoiceRecognition();
                }
                if (recognition) {
                    try {
                        recognition.start();
                        updateVoiceIndicator(true);
                        addChatMessage("🎤 Voz activada permanentemente. Habla cuando quieras...", "bot");
                    } catch (e) {
                        console.log('Recognition already started');
                    }
                }
                if (ws) ws.send(JSON.stringify({action: "start_voice"}));
            } else {
                stopVoice();
            }
            updateVoiceStatus(voiceActive);
        }
        
        function stopVoice() {
            voiceActive = false;
            
            if (recognition) {
                try {
                    recognition.stop();
                } catch (e) {
                    console.log('Recognition already stopped');
                }
            }
            
            updateVoiceIndicator(false);
            if (ws) ws.send(JSON.stringify({action: "stop_voice"}));
            updateVoiceStatus(false);
            addChatMessage("🔇 Voz desactivada", "bot");
        }
        
        // ============ DASHBOARD FUNCTIONS ============
        
        let dashboardInterval = null;
        
        async function updateDashboard() {
            try {
                const response = await fetch('/api/dashboard/status');
                const data = await response.json();
                
                if (!data.success) {
                    console.error('Error obteniendo estado del dashboard:', data.error);
                    return;
                }
                
                // Actualizar timestamp
                const lastUpdateEl = document.getElementById('last-update');
                if (lastUpdateEl) {
                    lastUpdateEl.textContent = 'Actualizado: ' + new Date().toLocaleTimeString('es-ES');
                }
                
                // Estado de voz
                const voiceEl = document.getElementById('dash-voice');
                const voiceBar = document.getElementById('dash-voice-bar');
                if (voiceEl) {
                    if (data.voice_active) {
                        voiceEl.textContent = 'Activo';
                        voiceEl.classList.add('text-green-600');
                        voiceEl.classList.remove('text-gray-800');
                        if (voiceBar) {
                            voiceBar.style.width = '100%';
                            voiceBar.classList.add('voice-indicator');
                        }
                    } else {
                        voiceEl.textContent = 'Inactivo';
                        voiceEl.classList.remove('text-green-600');
                        voiceEl.classList.add('text-gray-800');
                        if (voiceBar) {
                            voiceBar.style.width = '0%';
                            voiceBar.classList.remove('voice-indicator');
                        }
                    }
                }
                
                // Skills
                const skillsEl = document.getElementById('dash-skills');
                if (skillsEl) skillsEl.textContent = data.skills_count || 0;
                const runningEl = document.getElementById('dash-skills-running');
                if (runningEl) runningEl.textContent = data.running_skills || 0;
                
                // Archivos generados
                const filesEl = document.getElementById('dash-files');
                if (filesEl) filesEl.textContent = data.total_files || 0;
                
                if (data.files_count) {
                    const imgEl = document.getElementById('dash-files-img');
                    if (imgEl) imgEl.textContent = '🖼️ ' + (data.files_count.imagenes || 0);
                    const txtEl = document.getElementById('dash-files-txt');
                    if (txtEl) txtEl.textContent = '📝 ' + (data.files_count.texto || 0);
                }
                
                // Providers IA
                const llmEl = document.getElementById('dash-llm');
                if (llmEl) llmEl.textContent = data.providers_configured || 0;
                
                // Acciones hoy
                const actionsEl = document.getElementById('dash-actions');
                if (actionsEl) actionsEl.textContent = data.today_actions || 0;
                
                // Sistema
                if (data.system) {
                    const cpuEl = document.getElementById('dash-cpu');
                    if (cpuEl) cpuEl.textContent = (data.system.cpu_percent || 0) + '%';
                    const ramEl = document.getElementById('dash-ram');
                    if (ramEl) ramEl.textContent = (data.system.memory_percent || 0) + '%';
                }
                
            } catch (e) {
                console.error('Error actualizando dashboard:', e);
            }
        }
        
        function startDashboardRefresh() {
            updateDashboard();
            dashboardInterval = setInterval(updateDashboard, 5000);
        }
        
        function stopDashboardRefresh() {
            if (dashboardInterval) {
                clearInterval(dashboardInterval);
                dashboardInterval = null;
            }
        }
        
        // Actualizar dashboard cuando se muestra el panel
        const originalShowPanel = showPanel;
        showPanel = function(panel) {
            originalShowPanel(panel);
            if (panel === 'dashboard') {
                startDashboardRefresh();
            } else {
                stopDashboardRefresh();
            }
        };
        
        // Iniciar actualización si dashboard está activo al cargar
        document.addEventListener("DOMContentLoaded", () => {
            if (document.getElementById('panel-dashboard').classList.contains('active')) {
                startDashboardRefresh();
            }
        });
        
        // ============ VOICE FUNCTIONS ============
        
        function updateVoiceStatus(active) {
            const el = document.getElementById("dash-voice");
            el.textContent = active ? "Activo" : "Inactivo";
            el.className = active ? "text-2xl font-bold text-green-600" : "text-2xl font-bold text-gray-800";
        }
        
        // PC Explorer with API integration
        let currentPcPath = "";
        
        async function loadPcFolder(path = "") {
            try {
                const url = path ? `/api/pc/browse?path=${encodeURIComponent(path)}` : "/api/pc/browse";
                const response = await fetch(url);
                const data = await response.json();
                
                if (data.success) {
                    currentPcPath = data.current_path;
                    document.getElementById("current-path").textContent = data.current_path;
                    renderPcItems(data.items, data.parent_path);
                } else {
                    addLog("Error cargando carpeta: " + data.error);
                }
            } catch (e) {
                addLog("Error de conexión: " + e.message);
            }
        }
        
        function renderPcItems(items, parentPath) {
            const fileList = document.getElementById("file-list");
            let html = "";
            
            // Add parent folder button if available
            if (parentPath) {
                html += `
                    <div onclick="loadPcFolder('${parentPath.replace(/\\/g, '\\\\')}')" 
                         class="p-4 border border-gray-200 rounded-lg hover:border-blue-400 cursor-pointer text-center">
                        <i class="fas fa-folder-open text-3xl text-gray-500 mb-2"></i>
                        <p class="text-sm font-medium">..</p>
                    </div>
                `;
            }
            
            items.forEach(item => {
                const icon = item.is_directory ? "fa-folder text-yellow-500" : "fa-file text-blue-500";
                const action = item.is_directory 
                    ? `loadPcFolder('${item.path.replace(/\\/g, '\\\\')}')` 
                    : `openPcItem('${item.path.replace(/\\/g, '\\\\')}')`;
                
                html += `
                    <div onclick="${action}" 
                         class="p-4 border border-gray-200 rounded-lg hover:border-blue-400 cursor-pointer text-center">
                        <i class="fas ${icon} text-3xl mb-2"></i>
                        <p class="text-sm font-medium truncate">${item.name}</p>
                        ${!item.is_directory ? `<p class="text-xs text-gray-400">${formatFileSize(item.size)}</p>` : ''}
                    </div>
                `;
            });
            
            fileList.innerHTML = html || '<p class="text-gray-500 col-span-full text-center">Carpeta vacía</p>';
        }
        
        async function openPcItem(path) {
            try {
                const response = await fetch("/api/pc/open", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({path: path})
                });
                const data = await response.json();
                if (data.success) {
                    addLog("Abierto: " + path);
                } else {
                    addLog("Error: " + data.error);
                }
            } catch (e) {
                addLog("Error abriendo archivo: " + e.message);
            }
        }
        
        function formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
        
        function pcAction(action) {
            addLog("PC: " + action);
            if (action === 'home') {
                loadPcFolder("");
            } else if (action === 'back') {
                if (currentPcPath) {
                    const parent = currentPcPath.substring(0, currentPcPath.lastIndexOf('\\'));
                    loadPcFolder(parent || "");
                }
            } else if (action === 'refresh') {
                loadPcFolder(currentPcPath);
            }
            if (ws) ws.send(JSON.stringify({action: "pc_" + action}));
        }
        
        // Initialize connectivity on page load (do NOT eager-load heavy data)
        document.addEventListener('DOMContentLoaded', () => {
            connectWS();
        });

        // Avoid leaving WS/voice running on refresh/navigation
        window.addEventListener('beforeunload', () => {
            wsEnabled = false;
            wsManualClose = true;
            try {
                if (wsReconnectTimer) {
                    clearTimeout(wsReconnectTimer);
                    wsReconnectTimer = null;
                }
            } catch (e) {
                // ignore
            }
            try {
                if (ws) ws.close();
            } catch (e) {
                // ignore
            }
            try {
                if (typeof stopVoice === 'function') stopVoice();
            } catch (e) {
                // ignore
            }
        });
        
        // LLM
        function checkOllama() {
            document.getElementById("ollama-status").textContent = "Verificando...";
            setTimeout(() => {
                document.getElementById("ollama-status").textContent = "No detectado";
                document.getElementById("ollama-status").className = "px-3 py-1 bg-red-100 text-red-600 rounded-full text-sm";
            }, 1000);
        }

        function toggleCloudConfig(provider) {
            const el = document.getElementById(`cloud-config-${provider}`);
            if (!el) return;
            el.classList.toggle('hidden');
        }

        async function saveCloudKey(provider) {
            const fieldMap = {
                openai: 'openai-api-key',
                groq: 'groq-api-key',
                gemini: 'gemini-api-key'
            };
            const fieldId = fieldMap[provider];
            const key = (document.getElementById(fieldId)?.value || '').trim();
            if (!key) {
                alert('❌ Debes ingresar la API key');
                return;
            }
            try {
                const r = await fetch('/api/llm/configure', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ provider, api_key: key })
                });
                const data = await r.json();
                if (data.success) {
                    alert('✅ Key guardada');
                } else {
                    alert('❌ ' + (data.error || 'No se pudo guardar'));
                }
            } catch (e) {
                alert('❌ Error de conexión: ' + e.message);
            }
        }

        async function activateProvider(provider) {
            try {
                const r = await fetch('/api/llm/activate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ provider })
                });
                const data = await r.json();
                if (data.success) {
                    selectedProvider = provider;
                    try { localStorage.setItem('miia_llm_provider', provider); } catch (e) {}
                    alert('✅ Provider activo: ' + provider);
                } else {
                    alert('❌ ' + (data.error || 'No se pudo activar'));
                }
            } catch (e) {
                alert('❌ Error de conexión: ' + e.message);
            }
        }
        
        // Logs
        function addLog(msg) {
            const logs = document.getElementById("system-logs");
            const time = new Date().toLocaleTimeString();
            const entry = document.createElement("div");
            entry.className = "log-entry";
            entry.textContent = `[${time}] ${msg}`;
            logs.appendChild(entry);
            logs.scrollTop = logs.scrollHeight;
        }
        
        function clearLogs() {
            document.getElementById("system-logs").innerHTML = "";
        }
        
        async function loadEvents() {
            try {
                const r = await fetch("/api/events?limit=50");
                const data = await r.json();
                data.items.forEach(item => addLog(JSON.stringify(item)));
            } catch (e) {
                addLog("Error cargando eventos: " + e);
            }
        }
        
        // Chat functions
        let currentSessionId = null;
        let menuSessionId = null;
        let selectedProvider = null;

        function getSelectedProvider() {
            try {
                return selectedProvider || localStorage.getItem('miia_llm_provider') || '';
            } catch (e) {
                return selectedProvider || '';
            }
        }
        
        async function sendChat() {
            const input = document.getElementById("chat-input");
            const text = input.value.trim();
            if (!text) return;
            
            // Agregar mensaje del usuario
            addChatMessage(text, "user");
            input.value = "";
            
            // Mostrar "pensando..."
            addChatMessage("🤔 Pensando...", "bot");
            
            try {
                // Llamar al backend
                const provider = getSelectedProvider();
                const response = await fetch("/api/chat", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({
                        user_id: "default",
                        message: text,
                        session_id: currentSessionId,
                        menu_session_id: menuSessionId,
                        provider: provider
                    })
                });
                
                const data = await response.json();
                
                // Quitar "pensando..."
                const messages = document.getElementById("chat-messages");
                if (messages.lastChild && messages.lastChild.textContent.includes("Pensando")) {
                    messages.removeChild(messages.lastChild);
                }
                
                if (data.menu_available) {
                    // Mostrar menú de APIs configuradas
                    menuSessionId = data.session_id;
                    addApiMenuMessage(data.message, data.options, data.session_id);
                } else if (data.requires_approval) {
                    // Necesita aprobación del usuario (formato antiguo)
                    currentSessionId = data.session_id;
                    addApprovalMessage(data.message, data.session_id);
                } else if (data.success && data.response) {
                    // Respuesta normal
                    addChatMessage(data.response, "bot");
                    currentSessionId = null;
                    menuSessionId = null;
                } else if (data.success && data.provider) {
                    // API seleccionada, proceder
                    addChatMessage(`✅ Usarás ${data.provider_name}. Procesando...`, "bot");
                    currentSessionId = data.session_id;
                    menuSessionId = null;
                    // Reenviar para ejecutar
                    await sendChat();
                } else {
                    // Error o mensaje
                    addChatMessage(data.message || data.error || "No pude procesar tu solicitud.", "bot");
                }
                
            } catch (e) {
                addChatMessage("❌ Error de conexión: " + e.message, "bot");
            }
        }
        
        async function selectApiFromMenu(apiId, sessionId) {
            try {
                const response = await fetch("/api/chat", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({
                        user_id: "default",
                        menu_session_id: sessionId,
                        api_selection: apiId
                    })
                });
                
                const data = await response.json();
                
                // Quitar el menú
                const menuEl = document.getElementById(`api-menu-${sessionId}`);
                if (menuEl) menuEl.remove();
                
                if (data.success) {
                    addChatMessage(`✅ Seleccionaste ${data.provider_name}. Ejecutando...`, "bot");
                    currentSessionId = data.session_id;
                    menuSessionId = null;
                    // Continuar con la ejecución
                    await sendChat();
                } else {
                    addChatMessage("❌ " + (data.error || "Error al seleccionar API"), "bot");
                }
            } catch (e) {
                addChatMessage("❌ Error seleccionando API: " + e.message, "bot");
            }
        }
        
        function addApiMenuMessage(message, options, sessionId) {
            const container = document.getElementById("chat-messages");
            const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            
            // Construir botones para cada API
            let buttonsHtml = options.map(opt => `
                <button onclick="selectApiFromMenu('${opt.id}', '${sessionId}')" 
                        class="px-4 py-2 bg-blue-100 hover:bg-blue-200 text-blue-800 rounded-lg text-sm font-medium transition-colors">
                    ${opt.number}. ${opt.name}
                    <span class="block text-xs text-blue-600">${opt.description}</span>
                </button>
            `).join('');
            
            const html = `
                <div class="flex gap-3" id="api-menu-${sessionId}">
                    <div class="w-10 h-10 bg-purple-500 rounded-full flex items-center justify-center flex-shrink-0">
                        <i class="fas fa-brain text-white"></i>
                    </div>
                    <div class="bg-purple-100 rounded-lg p-3 max-w-[85%]">
                        <p class="text-sm text-purple-800 font-medium mb-2">${escapeHtml(message)}</p>
                        <div class="grid grid-cols-1 gap-2 mb-3">
                            ${buttonsHtml}
                        </div>
                        <div class="flex gap-2">
                            <button onclick="cancelApiMenu('${sessionId}')" class="px-3 py-1 bg-gray-300 hover:bg-gray-400 text-gray-700 rounded text-sm">
                                ❌ Cancelar
                            </button>
                        </div>
                        <p class="text-xs text-purple-600 mt-2">💡 También puedes decir por voz: "usar la número 1" o "usar openai"</p>
                        <span class="text-xs text-purple-400 mt-1 block">${time}</span>
                    </div>
                </div>
            `;
            
            container.insertAdjacentHTML("beforeend", html);
            container.scrollTop = container.scrollHeight;
        }
        
        function cancelApiMenu(sessionId) {
            const el = document.getElementById(`api-menu-${sessionId}`);
            if (el) el.remove();
            addChatMessage("❌ Cancelado. No se usó API externa.", "bot");
            menuSessionId = null;
        }
        
        async function approveSession(sessionId) {
            try {
                const response = await fetch("/api/chat/approve", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({
                        user_id: "default",
                        session_id: sessionId
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Reenviar el mensaje ahora con sesión aprobada
                    await sendChat();
                } else {
                    addChatMessage("❌ No se pudo aprobar: " + (data.error || "Error desconocido"), "bot");
                }
            } catch (e) {
                addChatMessage("❌ Error aprobando: " + e.message, "bot");
            }
        }
        
        function addApprovalMessage(message, sessionId) {
            const container = document.getElementById("chat-messages");
            const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            
            const html = `
                <div class="flex gap-3" id="approval-${sessionId}">
                    <div class="w-10 h-10 bg-yellow-500 rounded-full flex items-center justify-center flex-shrink-0">
                        <i class="fas fa-lock text-white"></i>
                    </div>
                    <div class="bg-yellow-100 rounded-lg p-3 max-w-[80%]">
                        <p class="text-sm text-yellow-800">${escapeHtml(message)}</p>
                        <div class="mt-3 flex gap-2">
                            <button onclick="approveSession('${sessionId}')" class="px-3 py-1 bg-green-500 hover:bg-green-600 text-white rounded text-sm">
                                ✅ Sí, usar API
                            </button>
                            <button onclick="rejectSession('${sessionId}')" class="px-3 py-1 bg-red-500 hover:bg-red-600 text-white rounded text-sm">
                                ❌ Cancelar
                            </button>
                        </div>
                        <span class="text-xs text-yellow-600 mt-1 block">${time}</span>
                    </div>
                </div>
            `;
            
            container.insertAdjacentHTML("beforeend", html);
            container.scrollTop = container.scrollHeight;
        }
        
        function rejectSession(sessionId) {
            const el = document.getElementById(`approval-${sessionId}`);
            if (el) {
                el.remove();
            }
            addChatMessage("❌ Cancelado. No se usó API externa.", "bot");
            currentSessionId = null;
        }
        
        function startVoiceChat() {
            toggleVoice();
            addChatMessage("🎤 Modo voz activado. Di tu mensaje...", "bot");
        }
        
        function addChatMessage(text, sender) {
            const container = document.getElementById("chat-messages");
            const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            
            let html = "";
            if (sender === "user") {
                html = `
                    <div class="flex gap-3 justify-end">
                        <div class="bg-green-100 rounded-lg p-3 max-w-[80%]">
                            <p class="text-sm text-green-800">${escapeHtml(text)}</p>
                            <span class="text-xs text-green-400 mt-1 block text-right">${time}</span>
                        </div>
                        <div class="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0">
                            <i class="fas fa-user text-white"></i>
                        </div>
                    </div>
                `;
            } else {
                html = `
                    <div class="flex gap-3">
                        <div class="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
                            <i class="fas fa-robot text-white"></i>
                        </div>
                        <div class="bg-blue-100 rounded-lg p-3 max-w-[80%]">
                            <p class="text-sm text-blue-800">${escapeHtml(text)}</p>
                            <span class="text-xs text-blue-400 mt-1 block">${time}</span>
                        </div>
                    </div>
                `;
            }
            
            container.insertAdjacentHTML("beforeend", html);
            container.scrollTop = container.scrollHeight;
        }
        
        function escapeHtml(text) {
            const div = document.createElement("div");
            div.textContent = text;
            return div.innerHTML;
        }
        
        // ============ BOT CONFIGURATION FUNCTIONS ============
        
        function showBotTab(tab) {
            // Ocultar todos los tabs
            document.querySelectorAll('.bot-tab').forEach(el => el.classList.add('hidden'));
            document.getElementById(`bot-tab-${tab}`).classList.remove('hidden');
            
            // Actualizar botones
            const telegramBtn = document.getElementById('tab-telegram');
            const whatsappBtn = document.getElementById('tab-whatsapp');
            
            if (tab === 'telegram') {
                telegramBtn.classList.replace('bg-gray-200', 'bg-blue-500');
                telegramBtn.classList.replace('text-gray-700', 'text-white');
                whatsappBtn.classList.replace('bg-green-500', 'bg-gray-200');
                whatsappBtn.classList.replace('text-white', 'text-gray-700');
            } else {
                whatsappBtn.classList.replace('bg-gray-200', 'bg-green-500');
                whatsappBtn.classList.replace('text-gray-700', 'text-white');
                telegramBtn.classList.replace('bg-blue-500', 'bg-gray-200');
                telegramBtn.classList.replace('text-white', 'text-gray-700');
            }
        }
        
        function togglePassword(fieldId) {
            const field = document.getElementById(fieldId);
            const type = field.type === 'password' ? 'text' : 'password';
            field.type = type;
        }
        
        // Telegram functions
        async function saveTelegramConfig() {
            const token = document.getElementById('telegram-token').value.trim();
            const chatId = document.getElementById('telegram-chat-id').value.trim();
            const botName = document.getElementById('telegram-bot-name').value.trim();
            
            if (!token || !chatId) {
                showTelegramMessage('❌ Token y Chat ID son requeridos', 'error');
                return;
            }
            
            try {
                const response = await fetch('/api/bot/telegram', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token, chat_id: chatId, bot_name: botName })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showTelegramMessage('✅ ' + data.message, 'success');
                    updateTelegramUI(true);
                } else {
                    showTelegramMessage('❌ ' + data.error, 'error');
                }
            } catch (e) {
                showTelegramMessage('❌ Error de conexión: ' + e.message, 'error');
            }
        }
        
        async function updateTelegramToken() {
            const newToken = prompt('Ingresa el nuevo Bot Token:');
            if (!newToken) return;
            
            try {
                const response = await fetch('/api/bot/telegram/update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token: newToken })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showTelegramMessage('✅ Token actualizado correctamente', 'success');
                } else {
                    showTelegramMessage('❌ ' + data.error, 'error');
                }
            } catch (e) {
                showTelegramMessage('❌ Error: ' + e.message, 'error');
            }
        }
        
        async function deleteTelegramConfig() {
            if (!confirm('¿Estás seguro de eliminar la configuración de Telegram?\n\nEsta acción no se puede deshacer.')) {
                return;
            }
            
            try {
                const response = await fetch('/api/bot/telegram', { method: 'DELETE' });
                const data = await response.json();
                
                if (data.success) {
                    showTelegramMessage('🗑️ ' + data.message, 'success');
                    updateTelegramUI(false);
                    // Limpiar campos
                    document.getElementById('telegram-token').value = '';
                    document.getElementById('telegram-chat-id').value = '';
                    document.getElementById('telegram-bot-name').value = '';
                } else {
                    showTelegramMessage('❌ ' + data.error, 'error');
                }
            } catch (e) {
                showTelegramMessage('❌ Error: ' + e.message, 'error');
            }
        }
        
        function showTelegramMessage(msg, type) {
            const el = document.getElementById('telegram-message');
            el.textContent = msg;
            el.className = `mt-4 p-3 rounded-lg ${type === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`;
            el.classList.remove('hidden');
            setTimeout(() => el.classList.add('hidden'), 5000);
        }
        
        function updateTelegramUI(isConfigured) {
            const statusEl = document.getElementById('telegram-status');
            const actionsEl = document.getElementById('telegram-actions');
            
            if (isConfigured) {
                statusEl.innerHTML = '<span class="px-3 py-1 bg-green-100 text-green-600 rounded-full text-sm"><i class="fas fa-check-circle mr-1"></i>Configurado</span>';
                actionsEl.classList.remove('hidden');
            } else {
                statusEl.innerHTML = '<span class="px-3 py-1 bg-gray-200 text-gray-600 rounded-full text-sm"><i class="fas fa-circle mr-1"></i>No configurado</span>';
                actionsEl.classList.add('hidden');
            }
        }
        
        // WhatsApp functions
        async function saveWhatsAppConfig() {
            const phoneId = document.getElementById('whatsapp-phone-id').value.trim();
            const businessId = document.getElementById('whatsapp-business-id').value.trim();
            const token = document.getElementById('whatsapp-token').value.trim();
            
            if (!phoneId || !businessId || !token) {
                showWhatsAppMessage('❌ Todos los campos son requeridos', 'error');
                return;
            }
            
            try {
                const response = await fetch('/api/bot/whatsapp', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        phone_id: phoneId, 
                        business_id: businessId, 
                        access_token: token 
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showWhatsAppMessage('✅ ' + data.message, 'success');
                    updateWhatsAppUI(true);
                } else {
                    showWhatsAppMessage('❌ ' + data.error, 'error');
                }
            } catch (e) {
                showWhatsAppMessage('❌ Error de conexión: ' + e.message, 'error');
            }
        }
        
        async function updateWhatsAppToken() {
            const newToken = prompt('Ingresa el nuevo Access Token:');
            if (!newToken) return;
            
            try {
                const response = await fetch('/api/bot/whatsapp/update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token: newToken })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showWhatsAppMessage('✅ Token actualizado correctamente', 'success');
                } else {
                    showWhatsAppMessage('❌ ' + data.error, 'error');
                }
            } catch (e) {
                showWhatsAppMessage('❌ Error: ' + e.message, 'error');
            }
        }
        
        async function deleteWhatsAppConfig() {
            if (!confirm('¿Estás seguro de eliminar la configuración de WhatsApp?\n\nEsta acción no se puede deshacer.')) {
                return;
            }
            
            try {
                const response = await fetch('/api/bot/whatsapp', { method: 'DELETE' });
                const data = await response.json();
                
                if (data.success) {
                    showWhatsAppMessage('🗑️ ' + data.message, 'success');
                    updateWhatsAppUI(false);
                    // Limpiar campos
                    document.getElementById('whatsapp-phone-id').value = '';
                    document.getElementById('whatsapp-business-id').value = '';
                    document.getElementById('whatsapp-token').value = '';
                } else {
                    showWhatsAppMessage('❌ ' + data.error, 'error');
                }
            } catch (e) {
                showWhatsAppMessage('❌ Error: ' + e.message, 'error');
            }
        }
        
        function showWhatsAppMessage(msg, type) {
            const el = document.getElementById('whatsapp-message');
            el.textContent = msg;
            el.className = `mt-4 p-3 rounded-lg ${type === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`;
            el.classList.remove('hidden');
            setTimeout(() => el.classList.add('hidden'), 5000);
        }
        
        function updateWhatsAppUI(isConfigured) {
            const statusEl = document.getElementById('whatsapp-status');
            const actionsEl = document.getElementById('whatsapp-actions');
            
            if (isConfigured) {
                statusEl.innerHTML = '<span class="px-3 py-1 bg-green-100 text-green-600 rounded-full text-sm"><i class="fas fa-check-circle mr-1"></i>Configurado</span>';
                actionsEl.classList.remove('hidden');
            } else {
                statusEl.innerHTML = '<span class="px-3 py-1 bg-gray-200 text-gray-600 rounded-full text-sm"><i class="fas fa-circle mr-1"></i>No configurado</span>';
                actionsEl.classList.add('hidden');
            }
        }
        
        // Cargar estado al iniciar
        async function loadBotStatus() {
            try {
                const response = await fetch('/api/bot/status');
                const data = await response.json();
                
                if (data.telegram && data.telegram.is_configured) {
                    updateTelegramUI(true);
                }
                if (data.whatsapp && data.whatsapp.is_configured) {
                    updateWhatsAppUI(true);
                }
            } catch (e) {
                console.log('Error cargando estado de bots:', e);
            }
        }
        
        // ============ UPDATE FUNCTIONS ============
        
        async function checkForUpdates() {
            const btn = document.getElementById('btn-check-update');
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Buscando...';
            
            try {
                const response = await fetch('/api/update/check');
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('current-version').textContent = data.current_version;
                    document.getElementById('latest-version').textContent = data.latest_version || data.current_version;
                    
                    if (data.update_available) {
                        document.getElementById('update-available-badge').classList.remove('hidden');
                        document.getElementById('action-buttons').classList.remove('hidden');
                        document.getElementById('changelog-content').innerHTML = `<pre class="whitespace-pre-wrap">${data.changelog}</pre>`;
                        showUpdateMessage('✅ Hay una actualización disponible', 'success');
                    } else {
                        document.getElementById('update-available-badge').classList.add('hidden');
                        document.getElementById('action-buttons').classList.add('hidden');
                        showUpdateMessage('✓ Tienes la última versión', 'success');
                    }
                } else {
                    showUpdateMessage('❌ ' + data.error, 'error');
                }
            } catch (e) {
                showUpdateMessage('❌ Error de conexión', 'error');
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-search mr-2"></i>Buscar Actualizaciones';
            }
        }
        
        async function downloadUpdate() {
            const progressDiv = document.getElementById('download-progress');
            const progressBar = document.getElementById('progress-bar');
            const progressText = document.getElementById('progress-text');
            const btn = document.getElementById('btn-download');
            
            progressDiv.classList.remove('hidden');
            btn.disabled = true;
            
            try {
                const response = await fetch('/api/update/download', { method: 'POST' });
                const data = await response.json();
                
                if (data.success) {
                    // Simular progreso
                    let progress = 0;
                    const interval = setInterval(() => {
                        progress += 10;
                        progressBar.style.width = progress + '%';
                        progressText.textContent = progress + '%';
                        
                        if (progress >= 100) {
                            clearInterval(interval);
                            document.getElementById('action-buttons').classList.add('hidden');
                            document.getElementById('install-section').classList.remove('hidden');
                            showUpdateMessage('✅ Descarga completada', 'success');
                        }
                    }, 300);
                } else {
                    showUpdateMessage('❌ ' + data.error, 'error');
                    btn.disabled = false;
                }
            } catch (e) {
                showUpdateMessage('❌ Error de conexión', 'error');
                btn.disabled = false;
            }
        }
        
        async function installUpdate() {
            const btn = document.getElementById('btn-install');
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Instalando...';
            
            try {
                const response = await fetch('/api/update/install', { method: 'POST' });
                const data = await response.json();
                
                if (data.success) {
                    showUpdateMessage('✅ ' + data.message + ' Reinicia MiIA para completar.', 'success');
                    document.getElementById('install-section').classList.add('hidden');
                    
                    // Recargar lista de backups
                    loadBackups();
                } else {
                    showUpdateMessage('❌ ' + data.error, 'error');
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fas fa-rocket mr-2"></i>Instalar Actualización';
                }
            } catch (e) {
                showUpdateMessage('❌ Error de conexión', 'error');
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-rocket mr-2"></i>Instalar Actualización';
            }
        }
        
        async function createBackup() {
            try {
                const response = await fetch('/api/update/backup', { method: 'POST' });
                const data = await response.json();
                
                if (data.success) {
                    showUpdateMessage('✅ Backup creado: ' + data.backup_path, 'success');
                    loadBackups();
                } else {
                    showUpdateMessage('❌ ' + data.error, 'error');
                }
            } catch (e) {
                showUpdateMessage('❌ Error de conexión', 'error');
            }
        }
        
        async function loadBackups() {
            try {
                const response = await fetch('/api/update/backups');
                const data = await response.json();
                
                const list = document.getElementById('backups-list');
                if (data.backups && data.backups.length > 0) {
                    list.innerHTML = data.backups.map(b => `
                        <div class="flex justify-between items-center p-2 bg-gray-50 rounded">
                            <span class="text-sm">${b.name}</span>
                            <span class="text-xs text-gray-500">${b.date}</span>
                        </div>
                    `).join('');
                } else {
                    list.innerHTML = '<p class="text-gray-500 text-sm">No hay backups disponibles.</p>';
                }
            } catch (e) {
                console.log('Error cargando backups:', e);
            }
        }
        
        function showUpdateMessage(msg, type) {
            const el = document.getElementById('update-message');
            el.textContent = msg;
            el.className = `mt-4 p-3 rounded-lg ${type === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`;
            el.classList.remove('hidden');
            setTimeout(() => el.classList.add('hidden'), 5000);
        }
        
        // ============ BACKUP CONFIGURATION FUNCTIONS ============
        
        function showProviderConfig() {
            const provider = document.getElementById('backup-provider').value;
            
            // Ocultar todos
            document.getElementById('google-drive-config').classList.add('hidden');
            document.getElementById('dropbox-config').classList.add('hidden');
            document.getElementById('onedrive-config').classList.add('hidden');
            
            // Mostrar el seleccionado
            if (provider === 'google_drive') {
                document.getElementById('google-drive-config').classList.remove('hidden');
            } else if (provider === 'dropbox') {
                document.getElementById('dropbox-config').classList.remove('hidden');
            } else if (provider === 'onedrive') {
                document.getElementById('onedrive-config').classList.remove('hidden');
            }
        }
        
        async function verifyGoogleDrive() {
            const credentials = document.getElementById('google-credentials').value;
            const statusEl = document.getElementById('google-verify-status');
            
            if (!credentials.trim()) {
                statusEl.textContent = '❌ Debes pegar el contenido del archivo JSON de credenciales';
                statusEl.className = 'text-sm p-2 rounded bg-red-100 text-red-700';
                statusEl.classList.remove('hidden');
                return;
            }
            
            statusEl.textContent = '🔄 Verificando conexión...';
            statusEl.className = 'text-sm p-2 rounded bg-blue-100 text-blue-700';
            statusEl.classList.remove('hidden');
            
            try {
                const response = await fetch('/api/backup/verify-cloud', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        provider: 'google_drive',
                        credentials: { credentials_json: credentials }
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    statusEl.textContent = `✅ ${data.message} (${data.account_email})`;
                    statusEl.className = 'text-sm p-2 rounded bg-green-100 text-green-700';
                } else {
                    statusEl.textContent = `${data.error}`;
                    statusEl.className = 'text-sm p-2 rounded bg-red-100 text-red-700';
                }
            } catch (e) {
                statusEl.textContent = '❌ Error de conexión con el servidor';
                statusEl.className = 'text-sm p-2 rounded bg-red-100 text-red-700';
            }
        }
        
        async function verifyDropbox() {
            const token = document.getElementById('dropbox-token').value;
            const statusEl = document.getElementById('dropbox-verify-status');
            
            if (!token.trim()) {
                statusEl.textContent = '❌ Debes ingresar el token de acceso de Dropbox';
                statusEl.className = 'text-sm p-2 rounded bg-red-100 text-red-700';
                statusEl.classList.remove('hidden');
                return;
            }
            
            statusEl.textContent = '🔄 Verificando conexión...';
            statusEl.className = 'text-sm p-2 rounded bg-blue-100 text-blue-700';
            statusEl.classList.remove('hidden');
            
            try {
                const response = await fetch('/api/backup/verify-cloud', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        provider: 'dropbox',
                        credentials: { access_token: token }
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    statusEl.textContent = `✅ ${data.message} (${data.account_email})`;
                    statusEl.className = 'text-sm p-2 rounded bg-green-100 text-green-700';
                } else {
                    statusEl.textContent = `${data.error}`;
                    statusEl.className = 'text-sm p-2 rounded bg-red-100 text-red-700';
                }
            } catch (e) {
                statusEl.textContent = '❌ Error de conexión con el servidor';
                statusEl.className = 'text-sm p-2 rounded bg-red-100 text-red-700';
            }
        }
        
        async function verifyOneDrive() {
            const clientId = document.getElementById('onedrive-client-id').value;
            const clientSecret = document.getElementById('onedrive-client-secret').value;
            const tenantId = document.getElementById('onedrive-tenant-id').value;
            const statusEl = document.getElementById('onedrive-verify-status');
            
            if (!clientId.trim() || !clientSecret.trim()) {
                statusEl.textContent = '❌ Debes ingresar Client ID y Client Secret';
                statusEl.className = 'text-sm p-2 rounded bg-red-100 text-red-700';
                statusEl.classList.remove('hidden');
                return;
            }
            
            statusEl.textContent = '🔄 Verificando conexión...';
            statusEl.className = 'text-sm p-2 rounded bg-blue-100 text-blue-700';
            statusEl.classList.remove('hidden');
            
            try {
                const response = await fetch('/api/backup/verify-cloud', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        provider: 'onedrive',
                        credentials: { 
                            client_id: clientId,
                            client_secret: clientSecret,
                            tenant_id: tenantId || 'common'
                        }
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    statusEl.textContent = `✅ ${data.message}`;
                    statusEl.className = 'text-sm p-2 rounded bg-green-100 text-green-700';
                } else {
                    statusEl.textContent = `${data.error}`;
                    statusEl.className = 'text-sm p-2 rounded bg-red-100 text-red-700';
                }
            } catch (e) {
                statusEl.textContent = '❌ Error de conexión con el servidor';
                statusEl.className = 'text-sm p-2 rounded bg-red-100 text-red-700';
            }
        }
        
        async function saveBackupConfig() {
            const config = {
                provider: document.getElementById('backup-provider').value,
                auto_backup: document.getElementById('auto-backup').checked,
                backup_frequency: document.getElementById('backup-frequency').value,
                backup_time: document.getElementById('backup-time').value,
                max_backups: parseInt(document.getElementById('max-backups').value),
                backup_tokens: document.getElementById('backup-tokens').checked,
                backup_skills: document.getElementById('backup-skills').checked,
                backup_settings: document.getElementById('backup-settings').checked,
                backup_history: document.getElementById('backup-history').checked,
            };
            
            // Credenciales según el proveedor
            if (config.provider === 'google_drive') {
                config.google_credentials = document.getElementById('google-credentials').value;
            } else if (config.provider === 'dropbox') {
                config.dropbox_token = document.getElementById('dropbox-token').value;
            } else if (config.provider === 'onedrive') {
                config.onedrive_client_id = document.getElementById('onedrive-client-id').value;
                config.onedrive_client_secret = document.getElementById('onedrive-client-secret').value;
                config.onedrive_tenant_id = document.getElementById('onedrive-tenant-id').value;
            }
            
            try {
                const response = await fetch('/api/backup/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showBackupMessage('✅ Configuración de backup guardada', 'success');
                } else {
                    showBackupMessage('❌ ' + data.error, 'error');
                }
            } catch (e) {
                showBackupMessage('❌ Error de conexión', 'error');
            }
        }
        
        async function createBackupNow() {
            try {
                showBackupMessage('🔄 Creando backup...', 'success');
                
                const response = await fetch('/api/backup/create', { method: 'POST' });
                const data = await response.json();
                
                if (data.success) {
                    showBackupMessage('✅ ' + data.message, 'success');
                    loadBackupStatus();
                } else {
                    showBackupMessage('❌ ' + data.error, 'error');
                }
            } catch (e) {
                showBackupMessage('❌ Error de conexión', 'error');
            }
        }
        
        async function exportConfig() {
            try {
                const response = await fetch('/api/backup/export', { method: 'POST' });
                const data = await response.json();
                
                if (data.success) {
                    showBackupMessage('✅ Configuración exportada. Descarga: ' + data.file_name, 'success');
                } else {
                    showBackupMessage('❌ ' + data.error, 'error');
                }
            } catch (e) {
                showBackupMessage('❌ Error de conexión', 'error');
            }
        }
        
        async function loadBackupStatus() {
            try {
                const response = await fetch('/api/backup/status');
                const data = await response.json();
                
                // Actualizar campos
                if (data.config) {
                    document.getElementById('backup-provider').value = data.config.provider || 'local';
                    document.getElementById('auto-backup').checked = data.config.auto_backup;
                    document.getElementById('backup-frequency').value = data.config.backup_frequency || 'weekly';
                    document.getElementById('backup-time').value = data.config.backup_time || '02:00';
                    document.getElementById('max-backups').value = data.config.max_backups || 5;
                    document.getElementById('backup-tokens').checked = data.config.backup_tokens;
                    document.getElementById('backup-skills').checked = data.config.backup_skills;
                    document.getElementById('backup-settings').checked = data.config.backup_settings;
                    document.getElementById('backup-history').checked = data.config.backup_history;
                }
                
                // Mostrar proveedor conectado
                showProviderConfig();
                
                // Actualizar estado
                const statusEl = document.getElementById('backup-status');
                if (data.config.last_backup) {
                    const lastBackup = new Date(data.config.last_backup);
                    const nextBackup = data.config.next_backup ? new Date(data.config.next_backup) : null;
                    
                    statusEl.innerHTML = `
                        <p class="text-green-600 font-medium">✅ Backup configurado</p>
                        <p class="text-sm text-gray-600">Último backup: ${lastBackup.toLocaleString()}</p>
                        ${nextBackup ? `<p class="text-sm text-gray-600">Próximo backup: ${nextBackup.toLocaleString()}</p>` : ''}
                        <p class="text-sm text-gray-600">Proveedor: ${data.config.provider === 'local' ? '💻 Local' : data.config.provider === 'google_drive' ? '📁 Google Drive' : data.config.provider === 'dropbox' ? '📦 Dropbox' : data.config.provider}</p>
                    `;
                } else {
                    statusEl.innerHTML = `
                        <p class="text-gray-600">⚙️ Backup no configurado</p>
                        <p class="text-sm text-gray-500">Selecciona las opciones y guarda la configuración</p>
                    `;
                }
                
                // Mostrar backups locales
                const listEl = document.getElementById('backup-list');
                if (data.local_backups && data.local_backups.length > 0) {
                    listEl.innerHTML = data.local_backups.map(b => `
                        <div class="flex justify-between items-center p-2 bg-gray-50 rounded">
                            <div class="flex flex-col">
                                <span class="text-sm font-medium">${b.name}</span>
                                <span class="text-xs text-gray-500">${b.date}</span>
                            </div>
                            <span class="text-xs text-gray-600">${(b.size / 1024).toFixed(1)} KB</span>
                        </div>
                    `).join('');
                } else {
                    listEl.innerHTML = '<p class="text-gray-500 text-sm">No hay backups locales disponibles.</p>';
                }
            } catch (e) {
                console.log('Error cargando estado de backup:', e);
            }
        }
        
        function showBackupMessage(msg, type) {
            const el = document.getElementById('backup-message');
            el.textContent = msg;
            el.className = `mt-4 p-3 rounded-lg ${type === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`;
            el.classList.remove('hidden');
            setTimeout(() => el.classList.add('hidden'), 5000);
        }
        
        // ============ AI CHAT FUNCTIONS FOR SKILL EDITOR ============
        
        let aiChatHistory = [];
        let pendingCodeChanges = null;
        
        async function sendAIChatMessage() {
            const input = document.getElementById('ai-chat-input');
            const provider = document.getElementById('ai-provider-select').value;
            const message = input.value.trim();
            
            if (!message) return;
            
            // Agregar mensaje del usuario al chat
            addAIMessage(message, 'user');
            input.value = '';
            
            // Mostrar "pensando..."
            const thinkingId = addAIMessage('🤔 Pensando...', 'ai');
            
            try {
                // Obtener código actual
                const currentCode = document.getElementById('advanced-code-editor').value;
                
                const response = await fetch('/api/skills/ai-assist', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: message,
                        provider: provider,
                        current_code: currentCode,
                        history: aiChatHistory
                    })
                });
                
                const data = await response.json();
                
                // Quitar "pensando..."
                removeAIMessage(thinkingId);
                
                if (data.error) {
                    if (data.needs_config) {
                        addAIMessage(`⚠️ <strong>${data.error}</strong><br><br>Ve a <strong>Configuración → IA APIs</strong> para configurar esta IA.`, 'ai');
                    } else {
                        addAIMessage('❌ Error: ' + data.error, 'ai');
                    }
                    return;
                }
                
                function stripPythonCodeBlocks(text) {
                    try {
                        return String(text || '').replace(/```python\s*[\s\S]*?```/gi, '').replace(/```[\s\S]*?```/g, '').trim();
                    } catch (e) {
                        return String(text || '');
                    }
                }

                // Agregar respuesta de la IA (sin ensuciar el chat con el skill completo)
                const displayText = data.suggested_code ? stripPythonCodeBlocks(data.response) : data.response;
                addAIMessage(displayText || data.response, 'ai');
                
                // Si hay cambios de código sugeridos
                if (data.suggested_code) {
                    pendingCodeChanges = data.suggested_code;
                    showPendingChanges(data.changes_description || 'Cambios sugeridos por la IA');
                }
                
                // Guardar en historial
                aiChatHistory.push({ role: 'user', content: message });
                aiChatHistory.push({ role: 'assistant', content: data.response });
                
                // Limitar historial
                if (aiChatHistory.length > 20) {
                    aiChatHistory = aiChatHistory.slice(-20);
                }
                
            } catch (e) {
                removeAIMessage(thinkingId);
                addAIMessage('❌ Error de conexión: ' + e.message, 'ai');
            }
        }
        
        function askAI(prompt) {
            document.getElementById('ai-chat-input').value = prompt;
            sendAIChatMessage();
        }

        // Actualizar badge del provider seleccionado en el asistente IA
        try {
            const sel = document.getElementById('ai-provider-select');
            if (sel) {
                sel.addEventListener('change', () => {
                    const v = sel.value;
                    const badge = document.getElementById('ai-provider-badge');
                    if (!badge) return;
                    const map = {
                        ollama: '🦙 Ollama',
                        openai: '🧠 OpenAI',
                        gemini: '🔷 Gemini',
                        groq: '⚡ Groq',
                    };
                    badge.textContent = map[v] || v;
                });
            }
        } catch (e) {
            // ignore
        }
        
        function addAIMessage(text, sender) {
            const container = document.getElementById('ai-chat-messages');
            const id = 'msg-' + Date.now();
            
            const div = document.createElement('div');
            div.id = id;
            div.className = `ai-message ${sender === 'user' ? 'bg-blue-100 ml-8' : 'bg-purple-100'} rounded-lg p-3 text-sm`;
            
            const senderText = sender === 'user' ? 'Tú' : '🤖 Asistente';
            const senderColor = sender === 'user' ? 'text-blue-700' : 'text-purple-700';
            
            div.innerHTML = `
                <p class="font-medium ${senderColor} mb-1">${senderText}</p>
                <div class="text-gray-700">${formatMarkdown(text)}</div>
            `;
            
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
            
            return id;
        }
        
        function removeAIMessage(id) {
            const msg = document.getElementById(id);
            if (msg) msg.remove();
        }
        
        function formatMarkdown(text) {
            // Formato básico de markdown a HTML
            return text
                .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.+?)\*/g, '<em>$1</em>')
                .replace(/`(.+?)`/g, '<code class="bg-gray-200 px-1 rounded text-xs">$1</code>')
                .replace(/```([\s\S]+?)```/g, '<pre class="bg-gray-800 text-green-400 p-2 rounded text-xs overflow-x-auto mt-2"><code>$1</code></pre>')
                .replace(/\n/g, '<br>');
        }
        
        function showPendingChanges(description) {
            const container = document.getElementById('pending-changes');
            const list = document.getElementById('pending-changes-list');
            
            list.innerHTML = `
                <div class="p-2 bg-white rounded border">
                    <p class="text-sm text-gray-700 mb-2">${description}</p>
                    <div class="flex gap-2">
                        <button onclick="applyAIChange()" class="px-3 py-1 bg-green-500 text-white rounded text-xs hover:bg-green-600">
                            ✅ Aplicar
                        </button>
                        <button onclick="rejectAIChange()" class="px-3 py-1 bg-red-500 text-white rounded text-xs hover:bg-red-600">
                            ❌ Descartar
                        </button>
                    </div>
                </div>
            `;
            
            container.classList.remove('hidden');
        }
        
        function applyAIChange() {
            if (pendingCodeChanges) {
                document.getElementById('advanced-code-editor').value = pendingCodeChanges;
                addAIMessage('✅ Cambios aplicados al editor', 'ai');
                pendingCodeChanges = null;
                document.getElementById('pending-changes').classList.add('hidden');
            }
        }
        
        function rejectAIChange() {
            pendingCodeChanges = null;
            document.getElementById('pending-changes').classList.add('hidden');
            addAIMessage('❌ Cambios descartados', 'ai');
        }
        
        // Permitir Ctrl+Enter para enviar
        document.addEventListener('DOMContentLoaded', function() {
            const chatInput = document.getElementById('ai-chat-input');
            if (chatInput) {
                chatInput.addEventListener('keydown', function(e) {
                    if (e.ctrlKey && e.key === 'Enter') {
                        sendAIChatMessage();
                    }
                });
            }
        });
        
        // ============ SKILL WIZARD FUNCTIONS ============
        
        let currentWizardTemplate = null;
        let currentWizardStep = 1;
        
        function showSkillsTab(tab) {
            // Ocultar todos los contenidos
            document.querySelectorAll('.skills-tab-content').forEach(el => el.classList.add('hidden'));
            document.getElementById(`skills-content-${tab}`).classList.remove('hidden');
            
            // Actualizar botones
            const tabs = ['my-skills', 'wizard', 'editor', 'marketplace', 'creaciones'];
            tabs.forEach(t => {
                const btn = document.getElementById(t === 'my-skills' ? 'skills-tab-my' : `skills-tab-${t}`);
                if (!btn) return; // Skip if button doesn't exist
                if (t === tab) {
                    btn.classList.replace('bg-gray-200', 'bg-blue-500');
                    btn.classList.replace('text-gray-700', 'text-white');
                } else {
                    btn.classList.replace('bg-blue-500', 'bg-gray-200');
                    btn.classList.replace('text-white', 'text-gray-700');
                }
            });
            
            // Cargar skills si es la pestaña de mis skills
            if (tab === 'my-skills') {
                loadUserSkills();
            }
            // Cargar marketplace si es esa pestaña
            if (tab === 'marketplace') {
                loadMarketplace();
            }
            // Cargar creaciones si es esa pestaña
            if (tab === 'creaciones') {
                loadCreaciones();
            }
        }
        
        function selectTemplate(template) {
            currentWizardTemplate = template;
            document.querySelectorAll('.template-btn').forEach(btn => {
                btn.classList.remove('border-blue-500', 'bg-blue-50');
            });
            event.currentTarget.classList.add('border-blue-500', 'bg-blue-50');
            
            // Cargar configuración por defecto según template
            const configs = {
                'echo': { name: 'saludo', description: 'Responde con un mensaje personalizado', message: '¡Hola! Soy MiIA. ¿En qué puedo ayudarte?' },
                'calculator': { name: 'calculadora', description: 'Realiza operaciones matemáticas', message: 'Ingresa la operación (ej: 2+2)' },
                'reminder': { name: 'recordatorio', description: 'Crea recordatorios', message: '¿Qué debo recordarte?' },
                'web_search': { name: 'buscador', description: 'Busca información en la web', message: '¿Qué deseas buscar?', network: true }
            };
            
            const config = configs[template] || configs['echo'];
            document.getElementById('skill-name').value = config.name;
            document.getElementById('skill-description').value = config.description;
            document.getElementById('skill-message').value = config.message;
            document.getElementById('perm-network').checked = config.network || false;
            
            validateSkillId();
            wizardNextStep(2);
        }
        
        function validateSkillId() {
            const name = document.getElementById('skill-name').value;
            const id = name.toLowerCase().replace(/[^a-z0-9_]/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '');
            document.getElementById('skill-id-preview').textContent = id || 'mi_skill';
        }
        
        function wizardNextStep(step) {
            document.querySelectorAll('.wizard-step').forEach(el => el.classList.add('hidden'));
            document.getElementById(`wizard-step-${step}`).classList.remove('hidden');
            currentWizardStep = step;
            
            if (step === 3) {
                generateSkillCode();
            }
        }
        
        function wizardPrevStep(step) {
            wizardNextStep(step);
        }
        
        // Escapar string para Python (evita errores de sintaxis con parentesis, comillas, etc)
        function escapePythonString(str) {
            if (!str) return '';
            // Escapar backslashes primero
            let result = str.replace(/\\/g, '\\\\');
            // Escapar comillas dobles
            result = result.replace(/"/g, '\\"');
            return result;
        }
        
        // Escapar para triple quotes en Python
        function escapePythonTripleString(str) {
            if (!str) return '';
            // Para triple quotes, solo necesitamos escapar los backslashes
            return str.replace(/\\/g, '\\\\');
        }
        
        function generateSkillCode() {
            const name = document.getElementById('skill-name').value || 'mi_skill';
            const description = document.getElementById('skill-description').value || '';
            const message = document.getElementById('skill-message').value || '';
            const template = currentWizardTemplate || 'echo';
            
            // Escapar valores para Python
            const safeDescription = escapePythonTripleString(description);
            const safeMessage = escapePythonTripleString(message);
            const safeName = escapePythonString(name);
            
            let code = `def execute(context):
    """${safeDescription}"""
    task = context.get('task', '')
    user_id = context.get('user_id', 'unknown')
    
    # Skill: ${safeName}
    # Template: ${template}
    
`;
            
            if (template === 'echo') {
                code += `    response = """${safeMessage}"""
    
    return {
        "success": True,
        "message": response,
        "type": "echo"
    }`;
            } else if (template === 'calculator') {
                code += `    # Extraer numeros y operacion
    import re
    numbers = re.findall(r'\\d+', task)
    
    if len(numbers) >= 2:
        try:
            a, b = int(numbers[0]), int(numbers[1])
            if '+' in task:
                result = a + b
                operation = 'suma'
            elif '-' in task:
                result = a - b
                operation = 'resta'
            elif '*' in task or 'x' in task or 'por' in task.lower():
                result = a * b
                operation = 'multiplicacion'
            elif '/' in task:
                result = a / b if b != 0 else 'infinito'
                operation = 'division'
            else:
                result = a + b
                operation = 'operacion'
            
            response = f"El resultado de la {operation} es: {result}"
        except:
            response = "No pude calcular eso. Intenta con: 2+2, 5*3, etc."
    else:
        response = """${safeMessage}"""
    
    return {
        "success": True,
        "message": response,
        "type": "calculator"
    }`;
            } else if (template === 'reminder') {
                code += `    import time
    
    # Guardar recordatorio (en memoria)
    reminder = {
        "task": task,
        "user_id": user_id,
        "created_at": time.time(),
        "message": """${safeMessage}"""
    }
    
    # Aqui podrias guardar en archivo si tienes permiso fs_write
    
    response = f"Recordatorio guardado: {task}"
    
    return {
        "success": True,
        "message": response,
        "reminder": reminder,
        "type": "reminder"
    }`;
            } else if (template === 'web_search') {
                code += `    # Nota: Requiere permiso 'network'
    query = task.replace('busca', '').replace('buscar', '').strip()
    
    try:
        import urllib.request
        import urllib.parse
        import json
        
        # Usar DuckDuckGo Instant Answer API (no requiere key)
        url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'MININA-Bot/1.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            
            if data.get('AbstractText'):
                result = data['AbstractText']
            elif data.get('RelatedTopics') and len(data['RelatedTopics']) > 0:
                result = data['RelatedTopics'][0].get('Text', 'No encontre resultados')
            else:
                result = "No encontre informacion sobre eso."
    except Exception as e:
        result = f"Error buscando: {str(e)}"
    
    return {
        "success": True,
        "message": result,
        "query": query,
        "type": "web_search"
    }`;
            }
            
            document.getElementById('skill-code-preview').textContent = code;
        }
        
        async function testSkillInSandbox() {
            const code = document.getElementById('skill-code-preview').textContent;
            const resultsDiv = document.getElementById('sandbox-results');
            const outputDiv = document.getElementById('sandbox-output');
            
            resultsDiv.classList.remove('hidden');
            outputDiv.innerHTML = '<p class="text-yellow-600"><i class="fas fa-spinner fa-spin mr-2"></i>Probando en sandbox...</p>';
            
            try {
                const response = await fetch('/api/skills/test-sandbox', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        code: code,
                        skill_id: document.getElementById('skill-id-preview').textContent,
                        name: document.getElementById('skill-name').value,
                        permissions: [
                            document.getElementById('perm-fs-read').checked ? 'fs_read' : '',
                            document.getElementById('perm-fs-write').checked ? 'fs_write' : '',
                            document.getElementById('perm-network').checked ? 'network' : ''
                        ].filter(p => p)
                    })
                });
                
                const data = await response.json();
                
                if (data.sandbox_passed) {
                    outputDiv.innerHTML = `<p class="text-green-600"><i class="fas fa-check-circle mr-2"></i>✅ ${data.message}</p>`;
                } else {
                    outputDiv.innerHTML = `<p class="text-red-600"><i class="fas fa-times-circle mr-2"></i>❌ Falló en sandbox</p>
                        <ul class="mt-2 text-red-500">${(data.reasons || []).map(r => `<li>• ${r}</li>`).join('')}</ul>`;
                }
            } catch (e) {
                outputDiv.innerHTML = `<p class="text-red-600">❌ Error: ${e.message}</p>`;
            }
        }
        
        async function validateSkillCode() {
            const code = document.getElementById('skill-code-preview').textContent;
            
            try {
                const response = await fetch('/api/skills/validate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        code: code,
                        skill_id: document.getElementById('skill-id-preview').textContent,
                        name: document.getElementById('skill-name').value
                    })
                });
                
                const data = await response.json();
                
                if (data.valid) {
                    alert('✅ Código válido y seguro');
                } else {
                    alert('❌ Problemas encontrados:\n' + (data.reasons || []).join('\n'));
                }
            } catch (e) {
                alert('❌ Error validando: ' + e.message);
            }
        }
        
        async function saveWizardSkill() {
            const code = document.getElementById('skill-code-preview').textContent;
            const skillId = document.getElementById('skill-id-preview').textContent;
            const name = document.getElementById('skill-name').value;
            const description = document.getElementById('skill-description').value;
            
            // Verificar si requiere credenciales
            const requiresCredentials = document.getElementById('perm-credentials').checked;
            
            try {
                const response = await fetch('/api/skills/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        skill_id: skillId,
                        name: name,
                        code: code,
                        description: description,
                        permissions: [
                            document.getElementById('perm-fs-read').checked ? 'fs_read' : '',
                            document.getElementById('perm-fs-write').checked ? 'fs_write' : '',
                            document.getElementById('perm-network').checked ? 'network' : '',
                            requiresCredentials ? 'credentials' : ''
                        ].filter(p => p)
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    if (requiresCredentials) {
                        alert('✅ Skill guardado. Esta skill requiere credenciales. El sistema las solicitará cuando se ejecute y las eliminará automáticamente después.');
                    } else {
                        alert('✅ Skill guardado correctamente');
                    }
                    showSkillsTab('my-skills');
                } else {
                    alert('❌ Error: ' + (data.error || 'No se pudo guardar'));
                }
            } catch (e) {
                alert('❌ Error guardando: ' + e.message);
            }
        }
        
        async function loadExample(example) {
            const examples = {
                'hola': { template: 'echo', name: 'saludo', desc: 'Saludo amigable', msg: '¡Hola! ¿Cómo estás? Soy MiIA, tu asistente virtual.' },
                'hora': { template: 'echo', name: 'hora_actual', desc: 'Dice la hora', msg: 'La hora actual es: ' + new Date().toLocaleTimeString() },
                'clima': { template: 'web_search', name: 'clima_hoy', desc: 'Busca el clima', msg: '¿De qué ciudad quieres saber el clima?', network: true }
            };
            
            const ex = examples[example];
            if (ex) {
                currentWizardTemplate = ex.template;
                document.getElementById('skill-name').value = ex.name;
                document.getElementById('skill-description').value = ex.desc;
                document.getElementById('skill-message').value = ex.msg;
                document.getElementById('perm-network').checked = ex.network || false;
                validateSkillId();
                wizardNextStep(2);
            }
        }
        
        // ============ ADVANCED EDITOR FUNCTIONS ============
        
        async function loadUserSkills() {
            try {
                const response = await fetch('/api/skills');
                const data = await response.json();
                
                const listEl = document.getElementById('user-skills-list');
                const countEl = document.getElementById('skills-count');
                
                if (!data.success) {
                    console.error('Error cargando skills:', data.error);
                    listEl.innerHTML = `
                        <div class="glass-panel rounded-xl p-5 text-center">
                            <p class="text-red-500">Error cargando skills: ${data.error || 'Error desconocido'}</p>
                        </div>
                        <div class="glass-panel rounded-xl p-5 card-hover border-dashed border-2 border-gray-300 cursor-pointer hover:border-blue-400" onclick="showSkillsTab('wizard')">
                            <div class="flex items-center justify-center h-20 text-gray-400">
                                <div class="text-center">
                                    <i class="fas fa-plus-circle text-3xl mb-2"></i>
                                    <p>Crear nuevo skill</p>
                                </div>
                            </div>
                        </div>
                    `;
                    if (countEl) countEl.textContent = '0';
                    return;
                }
                
                if (data.skills && data.skills.length > 0) {
                    let html = '';
                    data.skills.forEach(skill => {
                        html += `
                            <div class="glass-panel rounded-xl p-5 card-hover">
                                <div class="flex items-start justify-between">
                                    <div class="flex items-center gap-3">
                                        <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                                            <i class="fas fa-robot text-blue-600"></i>
                                        </div>
                                        <div>
                                            <h4 class="font-bold">${skill.id}</h4>
                                            <p class="text-sm text-gray-500">${skill.name || skill.id}</p>
                                            <p class="text-xs text-gray-400">v${skill.version || '1.0'}</p>
                                        </div>
                                    </div>
                                    <div class="flex gap-2">
                                        <button onclick="runSkill('${skill.id}')" class="px-2 py-1 bg-green-100 text-green-600 rounded text-xs hover:bg-green-200" title="Ejecutar skill">
                                            <i class="fas fa-play"></i>
                                        </button>
                                        <span class="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">Activo</span>
                                        <button onclick="deleteSkill('${skill.id}')" class="px-2 py-1 bg-red-100 text-red-600 rounded text-xs hover:bg-red-200" title="Eliminar skill">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </div>
                                </div>
                                ${skill.permissions ? `<p class="text-xs text-gray-500 mt-2">Permisos: ${skill.permissions.join(', ')}</p>` : ''}
                            </div>
                        `;
                    });
                    html += `
                        <div class="glass-panel rounded-xl p-5 card-hover border-dashed border-2 border-gray-300 cursor-pointer hover:border-blue-400" onclick="showSkillsTab('wizard')">
                            <div class="flex items-center justify-center h-20 text-gray-400">
                                <div class="text-center">
                                    <i class="fas fa-plus-circle text-3xl mb-2"></i>
                                    <p>Crear nuevo skill</p>
                                </div>
                            </div>
                        </div>
                    `;
                    listEl.innerHTML = html;
                    if (countEl) countEl.textContent = data.skills.length;
                } else {
                    // No hay skills - mostrar mensaje
                    listEl.innerHTML = `
                        <div class="glass-panel rounded-xl p-5 text-center">
                            <p class="text-gray-500 mb-4">No tienes skills guardadas</p>
                            <p class="text-sm text-gray-400">Las skills se guardan en: C:\MiIA-Product-20-Data\</p>
                        </div>
                        <div class="glass-panel rounded-xl p-5 card-hover border-dashed border-2 border-gray-300 cursor-pointer hover:border-blue-400" onclick="showSkillsTab('wizard')">
                            <div class="flex items-center justify-center h-20 text-gray-400">
                                <div class="text-center">
                                    <i class="fas fa-plus-circle text-3xl mb-2"></i>
                                    <p>Crear nuevo skill</p>
                                </div>
                            </div>
                        </div>
                    `;
                    if (countEl) countEl.textContent = '0';
                }
            } catch (e) {
                console.error('Error cargando skills:', e);
                const listEl = document.getElementById('user-skills-list');
                listEl.innerHTML = `
                    <div class="glass-panel rounded-xl p-5 text-center">
                        <p class="text-red-500">Error de conexión: ${e.message}</p>
                    </div>
                    <div class="glass-panel rounded-xl p-5 card-hover border-dashed border-2 border-gray-300 cursor-pointer hover:border-blue-400" onclick="showSkillsTab('wizard')">
                        <div class="flex items-center justify-center h-20 text-gray-400">
                            <div class="text-center">
                                <i class="fas fa-plus-circle text-3xl mb-2"></i>
                                <p>Crear nuevo skill</p>
                            </div>
                        </div>
                    </div>
                `;
            }
        }
        
        async function deleteSkill(skillId) {
            if (!confirm(`¿Eliminar el skill "${skillId}"?`)) return;
            
            try {
                const response = await fetch(`/api/skills/${skillId}`, { method: 'DELETE' });
                const data = await response.json();
                
                if (data.success) {
                    loadUserSkills();
                } else {
                    alert('Error: ' + (data.error || 'No se pudo eliminar'));
                }
            } catch (e) {
                alert('Error: ' + e.message);
            }
        }
        
        async function runSkill(skillId) {
            // Ejecutar directamente sin preguntar
            const task = "Ejecutar skill";
            
            // Mostrar en panel de ejecución
            addToRunningSkills(skillId, "Ejecutando...");
            
            try {
                const response = await fetch('/api/skills/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        skill_id: skillId,
                        task: task,
                        user_id: 'webui_user'
                    })
                });
                
                const data = await response.json();
                
                // Actualizar panel
                updateRunningSkill(skillId, data.success ? 'completed' : 'error', data);
                
                // Mostrar resultado
                if (data.success) {
                    const msg = data.result?.result?.message || data.result?.message || 'Skill completado';
                    const files = data.result?.result?.files || [];
                    let fileInfo = '';
                    if (files.length > 0) {
                        fileInfo = '\n\n📁 Archivos generados:\n' + files.map(f => `  • ${f}`).join('\n');
                    }
                    alert('✅ SKILL COMPLETADO\n\n' + msg + fileInfo);
                } else {
                    alert('❌ SKILL FALLÓ\n\nError: ' + (data.error || 'Error desconocido'));
                }
            } catch (e) {
                updateRunningSkill(skillId, 'error', {error: e.message});
                alert('❌ ERROR: ' + e.message);
            }
        }
        
        // Panel de skills en ejecución
        const runningSkills = new Map();
        
        function addToRunningSkills(skillId, status) {
            runningSkills.set(skillId, {status, startTime: Date.now(), data: null});
            updateRunningSkillsPanel();
        }
        
        function updateRunningSkill(skillId, status, data) {
            const skill = runningSkills.get(skillId);
            if (skill) {
                skill.status = status;
                skill.data = data;
                skill.endTime = Date.now();
            }
            updateRunningSkillsPanel();
        }
        
        function updateRunningSkillsPanel() {
            const panel = document.getElementById('running-skills-panel');
            const countBadge = document.getElementById('running-count');
            if (!panel) return;
            
            // Actualizar contador
            if (countBadge) {
                countBadge.textContent = runningSkills.size;
            }
            
            if (runningSkills.size === 0) {
                panel.innerHTML = '<p class="text-gray-400 text-sm">No hay skills en ejecución</p>';
                return;
            }
            
            let html = '';
            runningSkills.forEach((info, skillId) => {
                const statusColor = info.status === 'completed' ? 'text-green-500' : 
                                   info.status === 'error' ? 'text-red-500' : 'text-yellow-500';
                const statusIcon = info.status === 'completed' ? '✅' : 
                                  info.status === 'error' ? '❌' : '⏳';
                const duration = info.endTime ? 
                    ((info.endTime - info.startTime) / 1000).toFixed(1) + 's' :
                    ((Date.now() - info.startTime) / 1000).toFixed(1) + 's';
                
                // Extraer información del resultado
                let resultInfo = '';
                if (info.data && info.data.success) {
                    const result = info.data.result?.result || info.data.result || {};
                    const message = result.message || info.data.message || 'Completado';
                    const files = result.files || [];
                    
                    resultInfo = `<div class="mt-1 text-xs text-gray-300">${message}</div>`;
                    if (files.length > 0) {
                        resultInfo += `<div class="mt-1 text-xs text-blue-300">📁 ${files.length} archivo(s)</div>`;
                    }
                } else if (info.data && !info.data.success) {
                    const error = info.data.error || 'Error desconocido';
                    resultInfo = `<div class="mt-1 text-xs text-red-400">❌ ${error.substring(0, 50)}</div>`;
                }
                
                html += `
                    <div class="p-2 bg-gray-800 rounded mb-2">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <span class="${statusColor}">${statusIcon}</span>
                                <span class="text-sm text-white font-medium">${skillId}</span>
                            </div>
                            <span class="text-xs text-gray-400">${duration}</span>
                        </div>
                        ${resultInfo}
                    </div>
                `;
            });
            
            panel.innerHTML = html;
        }
        
        function formatCode() {
            // Simple formatter - could be enhanced
            const editor = document.getElementById('advanced-code-editor');
            let code = editor.value;
            
            // Basic formatting
            code = code.replace(/\\n\\s*\\n\\s*\\n/g, '\\n\\n');  // Remove extra blank lines
            code = code.replace(/:\\s*\\n\\s*\\n/g, ':\\n');  // Remove blank after colon
            
            editor.value = code;
        }
        
        function clearEditor() {
            if (confirm('¿Limpiar el editor? Se perderá el código actual.')) {
                document.getElementById('advanced-code-editor').value = '';
            }
        }
        
        async function validateAdvancedCode() {
            const code = document.getElementById('advanced-code-editor').value;
            const resultsDiv = document.getElementById('validation-results');
            const issuesDiv = document.getElementById('validation-issues');
            
            try {
                const response = await fetch('/api/skills/validate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        code: code,
                        skill_id: document.getElementById('advanced-skill-id').value || 'temp_skill',
                        name: document.getElementById('advanced-skill-name').value || 'Temp'
                    })
                });
                
                const data = await response.json();
                
                resultsDiv.classList.remove('hidden');
                
                if (data.valid) {
                    issuesDiv.innerHTML = '<p class="text-green-600"><i class="fas fa-check-circle mr-2"></i>✅ Código válido - No se detectaron problemas de seguridad</p>';
                } else {
                    issuesDiv.innerHTML = '<p class="text-red-600 font-medium mb-2"><i class="fas fa-exclamation-triangle mr-2"></i>Problemas encontrados:</p>' +
                        (data.reasons || []).map(r => `<p class="text-red-500">• ${r}</p>`).join('');
                }
            } catch (e) {
                issuesDiv.innerHTML = `<p class="text-red-600">❌ Error: ${e.message}</p>`;
            }
        }
        
        async function testAdvancedInSandbox() {
            const code = document.getElementById('advanced-code-editor').value;
            
            try {
                const response = await fetch('/api/skills/test-sandbox', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        code: code,
                        skill_id: document.getElementById('advanced-skill-id').value || 'test_skill',
                        name: document.getElementById('advanced-skill-name').value || 'Test',
                        permissions: [
                            document.getElementById('adv-perm-fs-read').checked ? 'fs_read' : '',
                            document.getElementById('adv-perm-fs-write').checked ? 'fs_write' : '',
                            document.getElementById('adv-perm-network').checked ? 'network' : '',
                            document.getElementById('adv-perm-ui').checked ? 'ui_access' : ''
                        ].filter(p => p)
                    })
                });
                
                const data = await response.json();
                
                const resultsDiv = document.getElementById('validation-results');
                const issuesDiv = document.getElementById('validation-issues');
                resultsDiv.classList.remove('hidden');
                
                if (data.sandbox_passed) {
                    issuesDiv.innerHTML = `<p class="text-green-600"><i class="fas fa-flask mr-2"></i>✅ ${data.message}</p>`;
                } else {
                    issuesDiv.innerHTML = `<p class="text-red-600"><i class="fas fa-flask mr-2"></i>❌ Falló en sandbox:</p>
                        <ul class="mt-2 text-red-500">${(data.reasons || data.error || ['Error desconocido']).map(r => `<li>• ${r}</li>`).join('')}</ul>`;
                }
            } catch (e) {
                alert('Error: ' + e.message);
            }
        }
        
        async function saveAdvancedSkill() {
            const code = document.getElementById('advanced-code-editor').value;
            const skillId = document.getElementById('advanced-skill-id').value;
            const name = document.getElementById('advanced-skill-name').value;
            
            if (!skillId || !name) {
                alert('❌ Debes ingresar ID y nombre del skill');
                return;
            }
            
            try {
                const response = await fetch('/api/skills/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        skill_id: skillId,
                        name: name,
                        code: code,
                        version: document.getElementById('advanced-skill-version').value || '1.0',
                        permissions: [
                            document.getElementById('adv-perm-fs-read').checked ? 'fs_read' : '',
                            document.getElementById('adv-perm-fs-write').checked ? 'fs_write' : '',
                            document.getElementById('adv-perm-network').checked ? 'network' : '',
                            document.getElementById('adv-perm-ui').checked ? 'ui_access' : ''
                        ].filter(p => p)
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert('✅ Skill guardado correctamente');
                    showSkillsTab('my-skills');
                } else {
                    alert('❌ Error: ' + (data.error || 'No se pudo guardar'));
                }
            } catch (e) {
                alert('❌ Error: ' + e.message);
            }
        }
        
        // ============ MIS CREACIONES FUNCTIONS ============
        
        const categoryIcons = {
            'Imagenes': { icon: 'fa-image', color: 'text-pink-500', bg: 'bg-pink-100' },
            'Texto': { icon: 'fa-file-alt', color: 'text-green-500', bg: 'bg-green-100' },
            'Video': { icon: 'fa-video', color: 'text-red-500', bg: 'bg-red-100' },
            'Audio': { icon: 'fa-music', color: 'text-yellow-500', bg: 'bg-yellow-100' },
            'Documentos': { icon: 'fa-file-word', color: 'text-blue-500', bg: 'bg-blue-100' },
            'Trabajos': { icon: 'fa-briefcase', color: 'text-purple-500', bg: 'bg-purple-100' }
        };
        
        const categoryNames = {
            'Imagenes': '🖼️ Imágenes',
            'Texto': '📝 Texto',
            'Video': '🎬 Video',
            'Audio': '🎵 Audio',
            'Documentos': '📄 Documentos',
            'Trabajos': '💼 Trabajos'
        };
        
        async function loadCreaciones() {
            const container = document.getElementById('creaciones-container');
            
            try {
                const response = await fetch('/api/output/files');
                const data = await response.json();
                
                if (!data.success) {
                    container.innerHTML = `
                        <div class="glass-panel rounded-xl p-4 text-center">
                            <p class="text-red-500">Error cargando archivos: ${data.error || 'Error desconocido'}</p>
                        </div>
                    `;
                    return;
                }
                
                // Actualizar contadores
                for (const [cat, files] of Object.entries(data.categories)) {
                    const countEl = document.getElementById(`count-${cat.toLowerCase()}`);
                    if (countEl) countEl.textContent = files.length;
                }
                
                // Renderizar categorías
                let html = '';
                let hasFiles = false;
                
                for (const [category, files] of Object.entries(data.categories)) {
                    if (files.length === 0) continue;
                    hasFiles = true;
                    
                    const catInfo = categoryIcons[category];
                    const catName = categoryNames[category];
                    
                    html += `
                        <div class="glass-panel rounded-xl overflow-hidden">
                            <div class="p-4 bg-gray-50 border-b flex items-center justify-between">
                                <div class="flex items-center gap-3">
                                    <div class="w-8 h-8 ${catInfo.bg} rounded-lg flex items-center justify-center">
                                        <i class="fas ${catInfo.icon} ${catInfo.color}"></i>
                                    </div>
                                    <h4 class="font-bold text-gray-800">${catName}</h4>
                                    <span class="px-2 py-1 bg-gray-200 text-gray-600 rounded text-xs">${files.length} archivo(s)</span>
                                </div>
                            </div>
                            <div class="p-4">
                                <div class="space-y-2">
                                    ${files.map(file => {
                                        const date = new Date(file.created * 1000).toLocaleString('es-ES');
                                        const size = formatFileSize(file.size);
                                        return `
                                            <div class="flex items-center justify-between p-3 bg-white rounded-lg border hover:shadow-sm transition-all">
                                                <div class="flex items-center gap-3 min-w-0">
                                                    <i class="fas ${catInfo.icon} ${catInfo.color} text-lg"></i>
                                                    <div class="min-w-0">
                                                        <p class="font-medium text-gray-800 truncate" title="${file.name}">${file.name}</p>
                                                        <p class="text-xs text-gray-500">${size} • ${date}</p>
                                                    </div>
                                                </div>
                                                <div class="flex gap-2 flex-shrink-0">
                                                    <a href="/api/output/download/${category}/${encodeURIComponent(file.name)}" 
                                                       download 
                                                       class="px-3 py-1 bg-blue-100 text-blue-600 rounded text-sm hover:bg-blue-200">
                                                        <i class="fas fa-download"></i>
                                                    </a>
                                                    <button onclick="deleteCreacion('${category}', '${file.name.replace(/'/g, "\'")}')" 
                                                            class="px-3 py-1 bg-red-100 text-red-600 rounded text-sm hover:bg-red-200">
                                                        <i class="fas fa-trash"></i>
                                                    </button>
                                                </div>
                                            </div>
                                        `;
                                    }).join('')}
                                </div>
                            </div>
                        </div>
                    `;
                }
                
                if (!hasFiles) {
                    html = `
                        <div class="glass-panel rounded-xl p-8 text-center">
                            <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                                <i class="fas fa-folder-open text-gray-400 text-2xl"></i>
                            </div>
                            <h4 class="text-lg font-medium text-gray-600 mb-2">No hay archivos generados</h4>
                            <p class="text-sm text-gray-500 mb-4">Ejecuta una skill para crear archivos</p>
                            <button onclick="showSkillsTab('my-skills')" class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600">
                                Ir a Mis Skills
                            </button>
                        </div>
                    `;
                }
                
                container.innerHTML = html;
                
            } catch (e) {
                container.innerHTML = `
                    <div class="glass-panel rounded-xl p-4 text-center">
                        <p class="text-red-500">Error de conexión: ${e.message}</p>
                    </div>
                `;
            }
        }
        
        function formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
        
        async function deleteCreacion(category, filename) {
            if (!confirm(`¿Eliminar "${filename}"?`)) return;
            
            try {
                const response = await fetch(`/api/output/${category}/${encodeURIComponent(filename)}`, {
                    method: 'DELETE'
                });
                const data = await response.json();
                
                if (data.success) {
                    loadCreaciones();
                } else {
                    alert('Error: ' + (data.error || 'No se pudo eliminar'));
                }
            } catch (e) {
                alert('Error: ' + e.message);
            }
        }
        
        // ============ MARKETPLACE FUNCTIONS ============
        
        async function loadMarketplace() {
            const listEl = document.getElementById('marketplace-list');
            const loadingEl = document.getElementById('marketplace-loading');
            
            listEl.innerHTML = '';
            loadingEl.classList.remove('hidden');
            
            try {
                const response = await fetch('/api/marketplace/skills');
                const data = await response.json();
                
                loadingEl.classList.add('hidden');
                
                if (data.success && data.skills) {
                    let html = '';
                    data.skills.forEach(skill => {
                        const stars = '★'.repeat(Math.floor(skill.rating || 0)) + '☆'.repeat(5 - Math.floor(skill.rating || 0));
                        html += `
                            <div class="glass-panel rounded-xl p-5 card-hover">
                                <div class="flex items-start justify-between mb-3">
                                    <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                                        <i class="fas fa-cube text-purple-600 text-xl"></i>
                                    </div>
                                    <span class="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">v${skill.version}</span>
                                </div>
                                <h4 class="font-bold mb-1">${skill.name}</h4>
                                <p class="text-sm text-gray-500 mb-2">${skill.description}</p>
                                <div class="flex items-center gap-2 text-sm text-gray-600 mb-2">
                                    <span class="text-yellow-500">${stars}</span>
                                    <span>(${skill.rating})</span>
                                </div>
                                <div class="flex items-center justify-between text-xs text-gray-500 mb-3">
                                    <span><i class="fas fa-user mr-1"></i>${skill.author}</span>
                                    <span><i class="fas fa-download mr-1"></i>${skill.downloads}</span>
                                </div>
                                <div class="flex flex-wrap gap-1 mb-3">
                                    ${(skill.permissions || []).map(p => `<span class="px-2 py-1 bg-gray-100 rounded text-xs">${p}</span>`).join('')}
                                </div>
                                <button onclick="installMarketplaceSkill('${skill.id}')" class="w-full px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg text-sm">
                                    <i class="fas fa-download mr-2"></i>Instalar
                                </button>
                            </div>
                        `;
                    });
                    listEl.innerHTML = html;
                } else {
                    listEl.innerHTML = '<p class="text-gray-500 text-center col-span-3">No se pudieron cargar las skills del marketplace.</p>';
                }
            } catch (e) {
                loadingEl.classList.add('hidden');
                listEl.innerHTML = `<p class="text-red-500 text-center col-span-3">Error cargando marketplace: ${e.message}</p>`;
            }
        }
        
        async function installMarketplaceSkill(skillId) {
            if (!confirm(`¿Instalar la skill "${skillId}"?`)) return;
            
            try {
                const response = await fetch('/api/marketplace/install', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ skill_id: skillId })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert('✅ ' + data.message);
                } else {
                    alert('❌ Error: ' + (data.error || 'No se pudo instalar'));
                }
            } catch (e) {
                alert('❌ Error: ' + e.message);
            }
        }
        
        // ============ INIT ============
        
        // Init (keep light to avoid refresh freezes)
        document.addEventListener("DOMContentLoaded", () => {
            // Default panel is dashboard; load heavy panels only when opened
        });
    </script>
</body>
</html>'''

def create_app() -> FastAPI:
    app = FastAPI(title="MiIA Product-20", version="1.0")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/", response_class=HTMLResponse)
    async def index():
        return HTML_TEMPLATE
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        ws_connections.append(websocket)
        try:
            await websocket.send_json({"type": "status", "voice_active": ui_state["voice_active"]})
            while True:
                data = await websocket.receive_json()
                if data.get("action") == "start_voice":
                    ui_state["voice_active"] = True
                    # Notificar al sistema principal via bus
                    try:
                        await bus.publish("user.SPEAK", {"message": "Activando micrófono...", "priority": "low"}, sender="WebUI")
                        await bus.publish("voice.START_LISTENING", {"source": "webui"}, sender="WebUI")
                    except Exception as e:
                        logger.error(f"Error activando voz: {e}")
                    await broadcast_message({"type": "voice_status", "active": True})
                elif data.get("action") == "stop_voice":
                    ui_state["voice_active"] = False
                    # Notificar al sistema principal via bus
                    try:
                        await bus.publish("voice.STOP_LISTENING", {"source": "webui"}, sender="WebUI")
                    except Exception as e:
                        logger.error(f"Error deteniendo voz: {e}")
                    await broadcast_message({"type": "voice_status", "active": False})
                elif data.get("action") == "pc_back":
                    await bus.publish("pc_control.ACTION", {"action": "go_back"}, sender="WebUI")
                elif data.get("action") == "pc_home":
                    await bus.publish("pc_control.ACTION", {"action": "go_home"}, sender="WebUI")
                elif data.get("action") == "pc_refresh":
                    await bus.publish("pc_control.ACTION", {"action": "refresh"}, sender="WebUI")
        except WebSocketDisconnect:
            if websocket in ws_connections:
                ws_connections.remove(websocket)
    
    @app.get("/api/pc/browse")
    async def browse_pc_folder(path: str = ""):
        """Browse PC folders - list contents of a directory"""
        try:
            from pathlib import Path
            import os
            
            # Default to user home if no path provided
            if not path:
                path = str(Path.home())
            
            # Security: prevent accessing system directories
            blocked_paths = ["C:\\Windows", "C:\\Program Files", "C:\\ProgramData"]
            for blocked in blocked_paths:
                if path.lower().startswith(blocked.lower()):
                    return {"success": False, "error": "Access to system directories is restricted"}
            
            target_path = Path(path)
            if not target_path.exists():
                return {"success": False, "error": f"Path does not exist: {path}"}
            
            if not target_path.is_dir():
                return {"success": False, "error": f"Not a directory: {path}"}
            
            items = []
            try:
                for item in target_path.iterdir():
                    items.append({
                        "name": item.name,
                        "is_directory": item.is_dir(),
                        "path": str(item),
                        "size": item.stat().st_size if item.is_file() else 0,
                        "modified": item.stat().st_mtime
                    })
            except PermissionError:
                return {"success": False, "error": "Permission denied"}
            
            # Sort: directories first, then files
            items.sort(key=lambda x: (not x["is_directory"], x["name"].lower()))
            
            return {
                "success": True,
                "current_path": str(target_path),
                "parent_path": str(target_path.parent) if target_path.parent != target_path else None,
                "items": items
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.post("/api/pc/open")
    async def open_pc_file(data: dict):
        """Open a file or folder on the PC"""
        try:
            import subprocess
            import os
            from pathlib import Path
            
            path = data.get("path", "")
            if not path:
                return {"success": False, "error": "No path provided"}
            
            target = Path(path)
            if not target.exists():
                return {"success": False, "error": f"Path does not exist: {path}"}
            
            # Open with default application
            if os.name == "nt":
                os.startfile(str(target))
            else:
                subprocess.Popen(["xdg-open", str(target)])
            
            return {"success": True, "message": f"Opened: {path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.get("/api/dashboard/status")
    async def get_dashboard_status():
        """Obtener estado real del dashboard"""
        try:
            from core.SkillVault import vault
            from core.AgentLifecycleManager import agent_manager
            from pathlib import Path
            import psutil
            
            # Contar archivos por categoría
            output_dir = vault.data_dir / "output"
            files_count = {
                "imagenes": len(list((output_dir / "Imagenes").glob("*")) if (output_dir / "Imagenes").exists() else []),
                "texto": len(list((output_dir / "Texto").glob("*")) if (output_dir / "Texto").exists() else []),
                "video": len(list((output_dir / "Video").glob("*")) if (output_dir / "Video").exists() else []),
                "audio": len(list((output_dir / "Audio").glob("*")) if (output_dir / "Audio").exists() else []),
                "documentos": len(list((output_dir / "Documentos").glob("*")) if (output_dir / "Documentos").exists() else []),
                "trabajos": len(list((output_dir / "Trabajos").glob("*")) if (output_dir / "Trabajos").exists() else []),
            }
            total_files = sum(files_count.values())
            
            # Contar skills
            skills = vault.list_user_skills()
            skills_count = len(skills)
            
            # Skills en ejecución
            running_skills = len(agent_manager.active_agents)
            
            # Estado de voz desde ui_state
            voice_active = ui_state.get("voice_active", False)
            
            # Estado de LLM
            try:
                from core.SecureLLMGateway import secure_gateway
                llm_status = secure_gateway.get_user_api_status("default")
                providers_configured = len([p for p in llm_status.get("providers", {}).values() if p.get("configured")])
            except:
                providers_configured = 0
            
            # Uso de recursos
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
            except:
                cpu_percent = 0
                memory_percent = 0
            
            # Últimos eventos (acciones de hoy)
            try:
                from datetime import datetime, timedelta
                today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
                recent_events = store.get_recent_events(limit=100)
                today_actions = len([e for e in recent_events if e.get("timestamp", 0) >= today_start])
            except:
                today_actions = 0
            
            return {
                "success": True,
                "voice_active": voice_active,
                "skills_count": skills_count,
                "running_skills": running_skills,
                "files_count": files_count,
                "total_files": total_files,
                "providers_configured": providers_configured,
                "today_actions": today_actions,
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "status": "online"
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.get("/api/dashboard/status")
    async def get_dashboard_status():
        """Obtener estado real del dashboard"""
        try:
            from core.SkillVault import vault
            from core.AgentLifecycleManager import agent_manager
            from pathlib import Path
            import psutil
            from datetime import datetime
            
            # Contar archivos por categoría
            output_dir = vault.data_dir / "output"
            files_count = {
                "imagenes": len(list((output_dir / "Imagenes").glob("*")) if (output_dir / "Imagenes").exists() else []),
                "texto": len(list((output_dir / "Texto").glob("*")) if (output_dir / "Texto").exists() else []),
                "video": len(list((output_dir / "Video").glob("*")) if (output_dir / "Video").exists() else []),
                "audio": len(list((output_dir / "Audio").glob("*")) if (output_dir / "Audio").exists() else []),
                "documentos": len(list((output_dir / "Documentos").glob("*")) if (output_dir / "Documentos").exists() else []),
                "trabajos": len(list((output_dir / "Trabajos").glob("*")) if (output_dir / "Trabajos").exists() else []),
            }
            total_files = sum(files_count.values())
            
            # Contar skills
            skills = vault.list_user_skills()
            skills_count = len(skills)
            
            # Skills en ejecución
            running_skills = len(agent_manager.active_agents)
            
            # Estado de voz desde ui_state
            voice_active = ui_state.get("voice_active", False)
            
            # Estado de LLM
            try:
                from core.SecureLLMGateway import secure_gateway
                llm_status = secure_gateway.get_user_api_status("default")
                providers_configured = len([p for p in llm_status.get("providers", {}).values() if p.get("configured")])
            except:
                providers_configured = 0
            
            # Uso de recursos
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
            except:
                cpu_percent = 0
                memory_percent = 0
            
            # Últimos eventos (acciones de hoy)
            try:
                from datetime import datetime
                today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
                recent_events = store.get_recent_events(limit=100)
                today_actions = len([e for e in recent_events if e.get("timestamp", 0) >= today_start])
            except:
                today_actions = 0
            
            return {
                "success": True,
                "voice_active": voice_active,
                "skills_count": skills_count,
                "running_skills": running_skills,
                "files_count": files_count,
                "total_files": total_files,
                "providers_configured": providers_configured,
                "today_actions": today_actions,
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "status": "online"
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.get("/api/events")
    async def api_events(limit: int = 80):
        items = store.get_recent_events(limit=max(1, min(limit, 500)))
        return {"items": items}
    
    @app.get("/api/llm/status")
    async def get_llm_status(user_id: str = "default"):
        """Obtener estado de APIs LLM para el usuario"""
        try:
            from core.SecureLLMGateway import secure_gateway
            status = secure_gateway.get_user_api_status(user_id)
            return status
        except Exception as e:
            return {"error": str(e)}

    @app.post("/api/llm/configure")
    async def configure_llm_provider(data: dict):
        """Guardar API key para un provider (Groq/OpenAI/Gemini)"""
        try:
            from core.llm_extension import credential_store

            provider = str(data.get("provider") or "").strip().lower()
            api_key = str(data.get("api_key") or "").strip()
            if provider not in {"groq", "openai", "gemini"}:
                return {"success": False, "error": "Provider inválido"}
            if not api_key:
                return {"success": False, "error": "API key requerida"}

            ok = credential_store.set_api_key(provider, api_key)
            return {"success": bool(ok)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @app.post("/api/llm/activate")
    async def activate_llm_provider(data: dict):
        """Activar provider en LLMManager (si está configurado o es local)."""
        try:
            from core.LLMManager import llm_manager, ProviderType
            from core.llm_extension import credential_store

            provider = str(data.get("provider") or "").strip().lower()

            mapping = {
                "ollama": ProviderType.OLLAMA,
                "groq": ProviderType.GROQ,
                "openai": ProviderType.OPENAI,
                "gemini": ProviderType.GEMINI,
            }
            if provider not in mapping:
                return {"success": False, "error": "Provider inválido"}

            ptype = mapping[provider]

            # Cargar api key desde el vault seguro cuando aplique
            if provider in {"groq", "openai", "gemini"}:
                key = credential_store.get_api_key(provider)
                if not key:
                    return {"success": False, "error": "Primero guarda la API key"}
                llm_manager.set_api_key(ptype, key)

            ok = llm_manager.set_active_provider(ptype)
            if not ok:
                return {"success": False, "error": "No se pudo activar (falta configuración)"}
            return {"success": True, "active_provider": provider}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.post("/api/chat")
    async def chat_endpoint(data: dict):
        """Endpoint para chat con integración segura de LLMs"""
        try:
            # Nuevo flujo: si hay provider configurado/activo, usar LLMManager directamente
            from core.LLMManager import llm_manager, ProviderType
            from core.llm_extension import credential_store
            from core.SecureLLMGateway import secure_gateway
            
            user_id = data.get("user_id", "default")
            message = data.get("message", "")
            session_id = data.get("session_id")
            requested_provider = str(data.get("provider") or "").strip().lower()

            provider_map = {
                "ollama": ProviderType.OLLAMA,
                "groq": ProviderType.GROQ,
                "openai": ProviderType.OPENAI,
                "gemini": ProviderType.GEMINI,
            }

            # Si el frontend envía provider (ej groq) y hay key, activarlo para esta respuesta.
            if requested_provider in {"groq", "openai", "gemini"} and credential_store.has_key(requested_provider):
                ptype = provider_map[requested_provider]
                try:
                    llm_manager.set_api_key(ptype, credential_store.get_api_key(requested_provider) or "")
                    llm_manager.set_active_provider(ptype)
                except Exception:
                    pass

            active = llm_manager.active_provider
            active_is_callable = active is not None and (llm_manager.get_active_config() is not None)

            if active_is_callable and (requested_provider or credential_store.has_key("groq") or credential_store.has_key("openai") or credential_store.has_key("gemini")):
                # Generar respuesta con el provider activo
                out = ""
                async for chunk in llm_manager.generate(prompt=str(message), system="", stream=False):
                    out += chunk
                if out.strip():
                    return {"success": True, "response": out, "used_api": True, "provider": (active.value if active else None)}

            # Si hay sesión de ejecución aprobada, ejecutar con API
            if session_id:
                result = await secure_gateway.execute_with_api(
                    user_id=user_id,
                    session_id=session_id,
                    query=message,
                    provider=data.get("provider", "openai")
                )
                return result
            
            # Si es selección de API desde menú
            menu_session_id = data.get("menu_session_id")
            api_selection = data.get("api_selection")
            if menu_session_id and api_selection:
                result = await secure_gateway.select_api_from_menu(
                    user_id=user_id,
                    session_id=menu_session_id,
                    selection=api_selection
                )
                return result
            
            # Si no hay sesión, detectar si necesita API y mostrar menú
            if len(message) > 50 or any(kw in message.lower() for kw in ["código", "programar", "explicar", "analizar", "resumir", "gpt", "claude", "ia", "inteligencia artificial"]):
                # Mostrar menú de APIs configuradas
                menu_result = await secure_gateway.request_api_menu(
                    user_id=user_id,
                    query_preview=message[:100]
                )
                return menu_result
            
            # Respuesta simple (sin API)
            return {
                "success": True,
                "response": f"Recibí: {message}",
                "used_api": False
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.post("/api/chat/approve")
    async def chat_approve(data: dict):
        """Aprobar una sesión de chat pendiente"""
        try:
            from core.SecureLLMGateway import secure_gateway
            
            user_id = data.get("user_id", "default")
            session_id = data.get("session_id")
            
            result = await secure_gateway.approve_session(user_id, session_id)
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ============== BOT CONFIGURATION ENDPOINTS ==============
    
    @app.post("/api/command")
    async def command_endpoint(data: dict):
        """Endpoint para ejecutar comandos de voz/texto"""
        try:
            import re
            from pathlib import Path
            from core.CommandEngine.engine import CommandEngine
            from core.AgentLifecycleManager import agent_manager
            
            command_text = data.get("command", "")
            user_id = data.get("user_id", "default")
            source = data.get("source", "voice")
            
            if not command_text:
                return {"success": False, "error": "No command provided"}
            
            def _extract_pc_intent(text: str):
                t = (text or "").strip().lower()
                if not t:
                    return None

                # Abrir aplicaciones de Windows
                apps = {
                    "bloc de notas": "notepad",
                    "block de notas": "notepad", 
                    "notepad": "notepad",
                    "calculadora": "calc",
                    "calc": "calc",
                    "paint": "mspaint",
                    "pintura": "mspaint",
                    "explorador": "explorer",
                    "navegador": "explorer",
                    "cmd": "cmd",
                    "terminal": "cmd",
                    "consola": "cmd",
                }
                
                # Buscar comando "abrir/abre X"
                m = re.search(r"\b(abre|abrir|abre la|abrir la|abre el|abrir el)\b\s+(.+)$", t)
                if m:
                    app_name = m.group(2).strip().strip('"').strip("'")
                    # Buscar coincidencia exacta o parcial
                    for key, exe in apps.items():
                        if key in app_name or app_name in key:
                            return ("open_app", exe)
                    # Si no coincide con apps conocidas, podría ser carpeta
                    return ("enter_dir", app_name)
                
                # Comando directo sin "abrir" (ej: "calculadora")
                for key, exe in apps.items():
                    if key in t:
                        return ("open_app", exe)

                if re.search(r"\b(lista|listar|muestra|mostrar|ver|ls|qué hay|que hay|muéstrame|muestrame|dime qué hay|dime que hay)\b", t):
                    return ("list_dir", "")

                if re.search(r"\b(atras|atrás|volver|back|sube|subir|regresa|vamos atrás|volver atrás)\b", t):
                    return ("go_back", "")

                m = re.search(
                    r"\b(abre|abrir|ve a|ir a|navega a|muévete a|muevete a|entra en|entrar en)\b.*\b(carpeta|folder|directorio)?\b(?:\s+de)?\s+(descargas|downloads|escritorio|desktop|documentos|documents|inicio|home|imagenes|imágenes|pictures|galeria|galería|videos|música|musica|music)\b",
                    t,
                )
                if m:
                    return ("open_folder", m.group(3))

                m = re.search(
                    r"\b(entra|entrar|abre|abrir|entra en|entrar en)\b\s+(?:a|en|la\s+carpeta\s+|el\s+directorio\s+)?(.+?)(?:\s+(?:por favor|pls|please))?$",
                    t,
                )
                if m:
                    name = m.group(1).strip().strip('"').strip("'")
                    if name and len(name) <= 180:
                        return ("enter_dir", name)

                m = re.search(r"\b(abr[eí]|abrir|open)\b\s+(?:el\s+archivo\s+)?(.+)$", t)
                if m and ("archivo" in t or "file" in t):
                    name = m.group(2).strip().strip('"').strip("'")
                    if name and len(name) <= 180:
                        return ("open_file", name)

                return None

            def _home_folder(alias: str) -> str:
                h = Path.home()
                a = (alias or "").strip().lower()
                mapping = {
                    "home": h,
                    "inicio": h,
                    "downloads": h / "Downloads",
                    "descargas": h / "Downloads",
                    "desktop": h / "Desktop",
                    "escritorio": h / "Desktop",
                    "documents": h / "Documents",
                    "documentos": h / "Documents",
                    "pictures": h / "Pictures",
                    "imagenes": h / "Pictures",
                    "imágenes": h / "Pictures",
                    "galeria": h / "Pictures",
                    "galería": h / "Pictures",
                    "videos": h / "Videos",
                    "music": h / "Music",
                    "musica": h / "Music",
                    "música": h / "Music",
                }
                return str(mapping.get(a, h))

            async def _browse(path: str) -> dict:
                from pathlib import Path as _Path

                if not path:
                    path = str(_Path.home())

                blocked_paths = ["C:\\Windows", "C:\\Program Files", "C:\\ProgramData"]
                for blocked in blocked_paths:
                    if path.lower().startswith(blocked.lower()):
                        return {"success": False, "error": "Access to system directories is restricted"}

                target_path = _Path(path)
                if not target_path.exists():
                    return {"success": False, "error": f"Path does not exist: {path}"}

                if not target_path.is_dir():
                    return {"success": False, "error": f"Not a directory: {path}"}

                items = []
                try:
                    for item in target_path.iterdir():
                        try:
                            stat = item.stat()
                            size = stat.st_size if item.is_file() else 0
                            modified = stat.st_mtime
                        except Exception:
                            size = 0
                            modified = 0
                        items.append(
                            {
                                "name": item.name,
                                "is_directory": item.is_dir(),
                                "path": str(item),
                                "size": size,
                                "modified": modified,
                            }
                        )
                except PermissionError:
                    return {"success": False, "error": "Permission denied"}

                items.sort(key=lambda x: (not x["is_directory"], x["name"].lower()))

                ui_state["current_path"] = str(target_path)
                return {
                    "success": True,
                    "current_path": str(target_path),
                    "parent_path": str(target_path.parent) if target_path.parent != target_path else None,
                    "items": items,
                }

            pc_intent = _extract_pc_intent(command_text)
            if pc_intent is not None:
                action, arg = pc_intent

                if action == "list_dir":
                    path = ui_state.get("current_path") or str(Path.home())
                    browse = await _browse(path)
                    if browse.get("success"):
                        return {"success": True, "executed": True, "response": "📁 Aquí tienes el contenido.", "pc_browse": browse}
                    return {"success": False, "executed": False, "error": browse.get("error", "Error")}

                if action == "go_back":
                    cur = ui_state.get("current_path") or str(Path.home())
                    parent = str(Path(cur).parent)
                    browse = await _browse(parent)
                    if browse.get("success"):
                        return {"success": True, "executed": True, "response": "↩️ Volviendo atrás...", "pc_browse": browse}
                    return {"success": False, "executed": False, "error": browse.get("error", "Error")}

                if action == "open_folder":
                    path = _home_folder(arg)
                    browse = await _browse(path)
                    if browse.get("success"):
                        return {"success": True, "executed": True, "response": f"📂 Abriendo {arg}...", "pc_browse": browse}
                    return {"success": False, "executed": False, "error": browse.get("error", "Error")}

                if action == "enter_dir":
                    cur = ui_state.get("current_path") or str(Path.home())
                    target = str(Path(cur) / arg)
                    browse = await _browse(target)
                    if browse.get("success"):
                        return {"success": True, "executed": True, "response": f"📂 Entrando a {arg}...", "pc_browse": browse}
                    return {"success": False, "executed": False, "error": browse.get("error", "Error")}

                if action == "open_file":
                    import os

                    cur = ui_state.get("current_path") or str(Path.home())
                    candidate = Path(arg)
                    target = candidate if candidate.is_absolute() else (Path(cur) / candidate)
                    if not target.exists():
                        return {"success": False, "executed": False, "error": f"No existe: {target}"}
                    try:
                        os.startfile(str(target))
                        return {"success": True, "executed": True, "response": f"✅ Abriendo: {target}"}
                    except Exception as e:
                        return {"success": False, "executed": False, "error": str(e)}

                if action == "open_app":
                    import os
                    import subprocess
                    
                    app = arg
                    try:
                        # Mapeo de apps comunes
                        app_commands = {
                            "notepad": "notepad.exe",
                            "calc": "calc.exe",
                            "mspaint": "mspaint.exe",
                            "explorer": "explorer.exe",
                            "cmd": "cmd.exe",
                        }
                        
                        cmd = app_commands.get(app, app)
                        subprocess.Popen(cmd, shell=True)
                        return {"success": True, "executed": True, "response": f"🖥️ Abriendo {app}..."}
                    except Exception as e:
                        return {"success": False, "executed": False, "error": str(e)}

            # Parse command (skills / otros)
            ce = CommandEngine()
            cmd = ce.parse(command_text)

            if not cmd:
                return {"success": False, "executed": False, "message": "No es un comando reconocido"}
            
            # Execute based on intent
            if cmd.intent == "use_skill" and cmd.skill_name:
                result = await agent_manager.use_and_kill(cmd.skill_name, cmd.task, user_id=user_id)
                return {
                    "success": True, 
                    "executed": True,
                    "response": f"✅ Ejecutando skill: {cmd.skill_name}",
                    "result": result
                }
            elif cmd.intent == "list_skills":
                skills = agent_manager.list_available_skills()
                return {
                    "success": True,
                    "executed": True,
                    "response": "Skills disponibles: " + ", ".join(skills) if skills else "(ninguna)"
                }
            elif cmd.intent == "status":
                return {
                    "success": True,
                    "executed": True,
                    "response": "Estado: MiIA operativa"
                }
            elif cmd.intent == "pc_control":
                # Execute PC control command
                action = cmd.action if hasattr(cmd, 'action') else command_text
                await bus.publish("pc_control.ACTION", {"action": action, "source": source}, sender="WebUI")
                return {
                    "success": True,
                    "executed": True,
                    "response": f"🖥️ Ejecutando: {action}"
                }
            else:
                return {"success": False, "executed": False, "message": f"Comando no implementado: {cmd.intent}"}
                
        except Exception as e:
            logger.error(f"Error ejecutando comando: {e}")
            return {"success": False, "error": str(e)}
    
    @app.get("/api/bot/status")
    async def bot_status():
        """Obtener estado de configuración de bots"""
        try:
            from core.BotConfigManager import bot_config_manager
            return bot_config_manager.get_all_status()
        except Exception as e:
            return {"error": str(e)}
    
    # Telegram endpoints
    @app.post("/api/bot/telegram")
    async def save_telegram(data: dict):
        """Guardar configuración de Telegram"""
        try:
            from core.BotConfigManager import bot_config_manager
            result = bot_config_manager.save_telegram_config(
                token=data.get("token", ""),
                chat_id=data.get("chat_id", ""),
                bot_name=data.get("bot_name", "")
            )
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.post("/api/bot/telegram/update")
    async def update_telegram_token(data: dict):
        """Actualizar token de Telegram"""
        try:
            from core.BotConfigManager import bot_config_manager
            result = bot_config_manager.update_telegram_token(data.get("token", ""))
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.delete("/api/bot/telegram")
    async def delete_telegram():
        """Eliminar configuración de Telegram"""
        try:
            from core.BotConfigManager import bot_config_manager
            return bot_config_manager.delete_telegram_config()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # WhatsApp endpoints
    @app.post("/api/bot/whatsapp")
    async def save_whatsapp(data: dict):
        """Guardar configuración de WhatsApp"""
        try:
            from core.BotConfigManager import bot_config_manager
            result = bot_config_manager.save_whatsapp_config(
                phone_id=data.get("phone_id", ""),
                business_id=data.get("business_id", ""),
                access_token=data.get("access_token", "")
            )
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.post("/api/bot/whatsapp/update")
    async def update_whatsapp_token(data: dict):
        """Actualizar token de WhatsApp"""
        try:
            from core.BotConfigManager import bot_config_manager
            result = bot_config_manager.update_whatsapp_token(data.get("token", ""))
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.delete("/api/bot/whatsapp")
    async def delete_whatsapp():
        """Eliminar configuración de WhatsApp"""
        try:
            from core.BotConfigManager import bot_config_manager
            return bot_config_manager.delete_whatsapp_config()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ============== UPDATE SYSTEM ENDPOINTS ==============
    
    @app.get("/api/update/check")
    async def check_updates():
        """Verificar actualizaciones disponibles"""
        try:
            from core.MININAUpdater import check_updates
            return await check_updates()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.post("/api/update/download")
    async def download_update():
        """Descargar actualización"""
        try:
            from core.MININAUpdater import download_update
            return await download_update()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.post("/api/update/install")
    async def install_update():
        """Instalar actualización"""
        try:
            from core.MININAUpdater import install_update
            return await install_update()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.post("/api/update/backup")
    async def create_backup():
        """Crear backup manual"""
        try:
            from core.MININAUpdater import updater
            return updater.backup_current_installation()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.get("/api/update/backups")
    async def list_backups():
        """Listar backups disponibles"""
        try:
            from core.MININAUpdater import updater
            backup_dir = updater.BACKUP_DIR
            backups = []
            if backup_dir.exists():
                for item in backup_dir.iterdir():
                    if item.is_dir():
                        backups.append({
                            "name": item.name,
                            "date": datetime.fromtimestamp(item.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
                        })
            return {"success": True, "backups": sorted(backups, key=lambda x: x["date"], reverse=True)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ============== BACKUP SYSTEM ENDPOINTS ==============
    
    @app.get("/api/backup/status")
    async def get_backup_status():
        """Obtener estado de configuración de backup"""
        try:
            from core.BackupManager import get_backup_status
            return get_backup_status()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.post("/api/backup/config")
    async def update_backup_config(data: dict):
        """Actualizar configuración de backup"""
        try:
            from core.BackupManager import update_backup_config
            return update_backup_config(data)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.post("/api/backup/create")
    async def create_backup_endpoint():
        """Crear backup manual"""
        try:
            from core.BackupManager import create_backup
            return await create_backup(manual=True)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.post("/api/backup/export")
    async def export_backup():
        """Exportar configuración para descarga"""
        try:
            from core.BackupManager import export_config
            return await export_config()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.post("/api/backup/verify-cloud")
    async def verify_cloud_backup_connection(data: dict):
        """Verificar conexión con Google Drive, Dropbox o OneDrive"""
        try:
            from core.CloudStorageIntegrations import verify_cloud_connection
            
            provider = data.get("provider", "")
            credentials = data.get("credentials", {})
            
            result = await verify_cloud_connection(provider, credentials)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.get("/api/output/files")
    async def list_output_files():
        """Listar archivos generados por el usuario organizados por categoría (dinámico)"""
        try:
            from core.SkillVault import vault
            from pathlib import Path
            
            output_base = vault.data_dir / "output"
            
            # Descubrir categorías dinámicamente desde carpetas existentes
            categories = {}
            
            if output_base.exists():
                for cat_path in output_base.iterdir():
                    if cat_path.is_dir():
                        category_name = cat_path.name
                        categories[category_name] = []
                        
                        for f in cat_path.iterdir():
                            if f.is_file():
                                try:
                                    stat = f.stat()
                                    categories[category_name].append({
                                        "name": f.name,
                                        "path": str(f),
                                        "size": stat.st_size,
                                        "created": stat.st_mtime,
                                        "category": category_name
                                    })
                                except:
                                    pass
            
            # Ordenar por fecha de creación (más reciente primero)
            for cat in categories:
                categories[cat].sort(key=lambda x: x["created"], reverse=True)
            
            total_files = sum(len(files) for files in categories.values())
            
            return {
                "success": True,
                "categories": categories,
                "total_files": total_files,
                "output_path": str(output_base)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.get("/api/output/download/{category}/{filename}")
    async def download_output_file(category: str, filename: str):
        """Descargar un archivo generado"""
        try:
            from core.SkillVault import vault
            from fastapi.responses import FileResponse
            from pathlib import Path
            
            # Sanitizar inputs
            safe_category = Path(category).name
            safe_filename = Path(filename).name
            
            file_path = vault.data_dir / "output" / safe_category / safe_filename
            
            if not file_path.exists() or not file_path.is_file():
                return {"success": False, "error": "Archivo no encontrado"}
            
            return FileResponse(
                path=str(file_path),
                filename=safe_filename,
                media_type="application/octet-stream"
            )
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.delete("/api/output/{category}/{filename}")
    async def delete_output_file(category: str, filename: str):
        """Eliminar un archivo generado"""
        try:
            from core.SkillVault import vault
            from pathlib import Path
            
            safe_category = Path(category).name
            safe_filename = Path(filename).name
            
            file_path = vault.data_dir / "output" / safe_category / safe_filename
            
            if not file_path.exists():
                return {"success": False, "error": "Archivo no encontrado"}
            
            file_path.unlink()
            return {"success": True, "message": f"Archivo '{safe_filename}' eliminado"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ============== SKILL WIZARD & SANDBOX ENDPOINTS ==============
    
    @app.get("/api/skills")
    async def list_user_skills():
        """Listar skills del usuario"""
        try:
            from core.SkillVault import vault
            skills = vault.list_user_skills()
            return {"success": True, "skills": skills}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.post("/api/skills/validate")
    async def validate_skill(data: dict):
        """Validar código de skill con AST check"""
        try:
            from core.SkillSafetyGate import SkillSafetyGate
            
            code = data.get("code", "")
            gate = SkillSafetyGate()
            
            # Crear directorio temporal para validación
            import re
            import tempfile
            import os
            
            # Detectar y corregir rutas absolutas en el código (igual que en test-sandbox)
            code_corrected = code
            abs_path_pattern = r"['\"]([A-Za-z]:[/\\\\][^'\"]+)['\"]"
            matches = re.findall(abs_path_pattern, code)
            
            if matches:
                for match in matches:
                    filename = os.path.basename(match.replace('\\', '/').replace('\\\\', '/'))
                    if not filename:
                        filename = "output.png"
                    code_corrected = code_corrected.replace(match, filename)
            
            with tempfile.TemporaryDirectory() as tmpdir:
                skill_dir = os.path.join(tmpdir, "skill")
                os.makedirs(skill_dir)
                
                # Escribir el código CORREGIDO
                with open(os.path.join(skill_dir, "skill.py"), "w") as f:
                    f.write(code_corrected)
                
                # Escribir manifest
                import json
                manifest = {
                    "id": data.get("skill_id", "temp_skill"),
                    "name": data.get("name", "Temp Skill"),
                    "version": data.get("version", "1.0"),
                    "permissions": data.get("permissions", [])
                }
                with open(os.path.join(skill_dir, "manifest.json"), "w") as f:
                    json.dump(manifest, f)
                
                # Validar
                from pathlib import Path
                report = gate.validate_extracted_dir(Path(skill_dir))
                
                # Preparar respuesta con warning si se corrigieron rutas
                response = {
                    "success": report.ok,
                    "valid": report.ok,
                    "skill_id": report.skill_id,
                    "reasons": report.reasons,
                    "permissions": report.permissions
                }
                
                if matches and report.ok:
                    response["warning"] = f"Se detectaron rutas absolutas y se convirtieron a relativas: {', '.join([os.path.basename(m) for m in matches])}"
                
                return response
        except Exception as e:
            return {"success": False, "valid": False, "error": str(e)}
    
    @app.post("/api/skills/test-sandbox")
    async def test_skill_sandbox(data: dict):
        """Probar skill en sandbox aislado"""
        try:
            from core.SkillSafetyGate import SkillSafetyGate
            
            code = data.get("code", "")
            test_context = data.get("context", {"task": "test", "user_id": "test"})
            
            # Detectar y corregir rutas absolutas en el código
            import re
            import tempfile
            import os
            
            # Reemplazar rutas absolutas comunes con rutas relativas para el sandbox
            # Patrón: 'C:/Users/.../Desktop/...' o 'C:\\Users\\...\\Desktop\\...'
            code_corrected = code
            
            # Detectar rutas absolutas de Windows (C:/ o C:\)
            abs_path_pattern = r"['\"]([A-Za-z]:[/\\\\][^'\"]+)['\"]"
            matches = re.findall(abs_path_pattern, code)
            
            if matches:
                # Reemplazar todas las rutas absolutas con nombres simples de archivo
                for match in matches:
                    # Extraer solo el nombre del archivo
                    filename = os.path.basename(match.replace('\\', '/').replace('\\\\', '/'))
                    if not filename:
                        filename = "output.png"
                    code_corrected = code_corrected.replace(match, filename)
            
            with tempfile.TemporaryDirectory() as tmpdir:
                skill_dir = os.path.join(tmpdir, "skill")
                sandbox_dir = os.path.join(tmpdir, "sandbox")
                output_dir = os.path.join(sandbox_dir, "output")
                os.makedirs(skill_dir)
                os.makedirs(sandbox_dir)
                os.makedirs(output_dir)
                
                # Corregir rutas 'output/' hardcoded para usar ruta absoluta del sandbox
                # Reemplazar 'output/' o 'output\\' con la ruta absoluta al output del sandbox
                output_dir_escaped = output_dir.replace('\\', '/')
                code_corrected = code_corrected.replace("'output/", f"'{output_dir_escaped}/")
                code_corrected = code_corrected.replace('"output/', f'"{output_dir_escaped}/')
                code_corrected = code_corrected.replace("'output\\", f"'{output_dir_escaped}/")
                code_corrected = code_corrected.replace('"output\\', f'"{output_dir_escaped}/')
                
                # Escribir el código CORREGIDO
                with open(os.path.join(skill_dir, "skill.py"), "w") as f:
                    f.write(code_corrected)
                
                import json
                manifest = {
                    "id": data.get("skill_id", "test_skill"),
                    "name": data.get("name", "Test"),
                    "version": "1.0",
                    "permissions": data.get("permissions", [])
                }
                with open(os.path.join(skill_dir, "manifest.json"), "w") as f:
                    json.dump(manifest, f)
                
                from pathlib import Path
                gate = SkillSafetyGate()
                report = gate.validate_extracted_dir(Path(skill_dir), sandbox_dir=Path(sandbox_dir))
                
                if report.ok:
                    message = "Skill ejecutado correctamente en sandbox"
                    if matches:
                        message += f"\n⚠️ Nota: Se detectaron rutas absolutas y se convirtieron a relativas para la prueba: {', '.join([os.path.basename(m) for m in matches])}"
                    return {
                        "success": True,
                        "sandbox_passed": True,
                        "skill_id": report.skill_id,
                        "message": message
                    }
                else:
                    return {
                        "success": False,
                        "sandbox_passed": False,
                        "reasons": report.reasons
                    }
        except Exception as e:
            return {"success": False, "sandbox_passed": False, "error": str(e)}
    
    @app.post("/api/skills/save")
    async def save_user_skill(data: dict):
        """Guardar skill del usuario"""
        try:
            from core.SkillVault import vault
            
            result = vault.save_skill(
                skill_id=data.get("skill_id"),
                name=data.get("name"),
                code=data.get("code"),
                version=data.get("version", "1.0"),
                permissions=data.get("permissions", []),
                description=data.get("description", "")
            )
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.delete("/api/skills/{skill_id}")
    async def delete_user_skill(skill_id: str):
        """Eliminar skill del usuario"""
        try:
            from core.SkillVault import vault
            return vault.delete_skill(skill_id)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.post("/api/skills/run")
    async def run_user_skill(data: dict):
        """Ejecutar skill guardado del usuario"""
        try:
            from core.AgentLifecycleManager import agent_manager
            from core.SkillVault import vault
            from core.llm_extension import credential_store
            import time
            import json
            
            skill_id = data.get("skill_id")
            task = data.get("task", "Ejecutar skill")
            user_id = data.get("user_id", "webui_user")
            
            if not skill_id:
                return {"success": False, "error": "skill_id requerido"}
            
            # Verificar que el skill existe
            skills = vault.list_user_skills()
            skill = next((s for s in skills if s["id"] == skill_id), None)
            if not skill:
                return {"success": False, "error": f"Skill '{skill_id}' no encontrado"}
            
            # Leer manifest para obtener permisos
            permissions = skill.get("permissions", [])
            
            # Preparar contexto con output_dir, permisos y API keys
            output_dir = str(vault.data_dir / "output" / "Imagenes")
            
            # Construir contexto completo
            context = {
                "task": task,
                "user_id": user_id,
                "timestamp": time.time(),
                "sandbox_dir": str(vault.live_dir / skill_id),
                "output_dir": output_dir,
                "permissions": permissions,
            }
            
            # Si la skill necesita API keys, agregarlas al contexto
            if "network" in permissions or "credentials" in permissions:
                api_keys = {}
                for provider in ["groq", "openai", "gemini"]:
                    key = credential_store.get_api_key(provider)
                    if key:
                        api_keys[provider] = key
                if api_keys:
                    context["api_keys"] = api_keys
            
            # Ejecutar el skill
            result = await agent_manager.execute_skill(skill_id, context)
            
            return {
                "success": True,
                "result": result,
                "skill_id": skill_id,
                "message": result.get("message", "Skill ejecutado") if isinstance(result, dict) else "Skill ejecutado"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.get("/api/skills/sandbox-status")
    async def get_sandbox_status():
        """Obtener estado del sandbox"""
        try:
            return {
                "success": True,
                "sandbox_active": True,
                "ast_check": True,
                "network_blocked": True,
                "timeout_seconds": 4,
                "max_zip_mb": 15
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.post("/api/skills/ai-assist")
    async def ai_assist_skill(data: dict):
        """Asistente IA para ayudar con código de skills"""
        try:
            message = data.get("message", "")
            provider = str(data.get("provider", "ollama") or "ollama").strip().lower()
            current_code = data.get("current_code", "")
            history = data.get("history", [])

            if provider not in {"ollama", "openai", "gemini", "groq"}:
                return {"error": f"Provider no soportado: {provider}", "needs_config": False}

            from core.LLMManager import llm_manager, ProviderType
            from core.llm_extension import credential_store

            if provider != "ollama" and not credential_store.has_key(provider):
                label = {"openai": "OpenAI", "gemini": "Gemini", "groq": "Groq"}.get(provider, provider)
                return {"error": f"{label} no configurado. Agrega la API key en Configuración → IA.", "needs_config": True}

            system_prompt = """Eres un asistente experto en programación Python para MiIA, un sistema de asistente virtual.
Tu trabajo es ayudar a los usuarios a crear y mejorar "skills" (habilidades) para MiIA.

ESTRUCTURA DE UN SKILL:
- Un skill es un archivo Python con una función `execute(context)` que recibe un dict con:
  - task: la tarea que el usuario solicitó (string)
  - user_id: ID del usuario (string)
  - timestamp: tiempo actual (float)
- La función debe retornar un dict con:
  - success: bool
  - message: string (respuesta al usuario)
  - data: dict opcional con datos adicionales

🚨 REGLAS DE SEGURIDAD DEL SANDBOX - OBLIGATORIAS:
El código se ejecuta en un sandbox seguro que PROHÍBE ciertos módulos. DEBES respetar estas reglas:

❌ MÓDULOS ABSOLUTAMENTE PROHIBIDOS (nunca los uses):
- pyautogui (control de mouse/teclado)
- ctypes (acceso a funciones de sistema)
- subprocess, os.system (ejecución de comandos)
- socket (red cruda)
- importlib, inspect (introspección peligrosa)
- win32api, win32con, win32gui (API de Windows)
- keyring, getpass (acceso a contraseñas)
- shutil (operaciones de archivos peligrosas)

❌ TAMBIÉN PROHIBIDO:
- eval(), exec(), compile() - funciones de ejecución dinámica
- Acceso a archivos fuera del directorio del skill
- Requests HTTP sin permiso 'network' explícito

✅ MÓDULOS PERMITIDOS Y RECOMENDADOS:
- PIL / Pillow (imágenes, gráficos) - USA ESTO en vez de pyautogui
- numpy, pandas (procesamiento de datos)
- json, csv, xml (manipulación de datos)
- datetime, time, random, math
- pathlib (manejo de rutas seguro)
- re (expresiones regulares)
- hashlib, base64 (codificación)
- io, tempfile (archivos temporales)

📝 ALTERNATIVAS SEGURAS PARA TAREAS COMUNES:

1. Para gráficos/imágenes (en vez de pyautogui):
   - Usa PIL/Pillow: Image, ImageDraw, ImageFont
   - Puedes crear imágenes, dibujar, guardar PNG/JPG
   - Ejemplo: img = Image.new('RGB', (800, 600)); ImageDraw.Draw(img).rectangle(...)

2. Para automatización de UI (NO permitida):
   - No está permitido por seguridad
   - Ofrece alternativas de visualización (generar imágenes de resultado)

3. Para archivos:
   - Usa pathlib.Path en vez de os.path
   - Rutas relativas al directorio del skill
   - Permisos: fs_read (leer), fs_write (escribir)

4. Para red/APIs:
   - Solo con permiso 'network' en manifest
   - Usa urllib (básico) o requests (si disponible)

📋 FORMATO OBLIGATORIO:
- SIEMPRE incluye exactamente UN bloque ```python``` con el archivo completo skill.py
- La función principal debe ser execute(context)
- Fuera del bloque ```python``` solo escribe explicación breve
- NUNCA sugieras código que viole las reglas de seguridad

🔴 REGLAS DE SINTAXIS PYTHON - ABSOLUTAMENTE OBLIGATORIAS:
- El código DEBE ser Python 100% válido sintácticamente
- Todas las comillas de strings DEBEN estar balanceadas (abrir y cerrar)
- Strings multilínea: usa triple comillas correctamente (\"\"\"texto\"\"\" o '''texto''')
- Nunca dejes un string sin cerrar (error: "unterminated string literal")
- Indentación consistente: 4 espacios por nivel
- Paréntesis, corchetes y llaves DEBEN estar balanceados
- Punto y coma al final de línea: opcional pero consistente
- Codificación: UTF-8 siempre

✅ VERIFICACIÓN ANTES DE ENTREGAR:
Antes de devolver el código, verifica mentalmente:
1. ¿Todas las comillas están cerradas?
2. ¿La indentación es correcta (4 espacios)?
3. ¿No hay strings rotos o truncados?
4. ¿Los paréntesis están balanceados?
5. ¿Incluiste los imports necesarios? (import random, import datetime, etc. si los usas)
Si hay error de sintaxis, regenéralo completamente hasta que sea válido.

📦 REGLA DE IMPORTS Y ARCHIVOS:
- SIEMPRE incluye los imports necesarios al INICIO del archivo
- Si usas random: agrega `import random` al inicio
- Si usas datetime: agrega `from datetime import datetime` o `import datetime`
- Si usas PIL: agrega `from PIL import Image, ImageDraw`
- Si usas json: agrega `import json`
- **IMPORTANTE**: Usa RUTAS RELATIVAS para guardar archivos (ej: `'mi_archivo.png'` o `'output/resultado.txt'`)
- **IMPORTANTE**: Crea los directorios antes de guardar: `os.makedirs('output', exist_ok=True)`
- **NUNCA** uses rutas absolutas tipo `'C:/Users/.../Desktop/...'` porque pueden no existir
- El código debe ser completamente autocontenido y ejecutable

⚠️ SI EL USUARIO PIDE ALGO QUE REQUIERE UN MÓDULO PROHIBIDO:
- Explica amablemente que no está permitido por seguridad
- Ofrece inmediatamente una alternativa segura
- Nunca intentes "saltarte" las restricciones
"""

            user_prompt = f"""Código actual del skill:
```python
{current_code}
```

Solicitud del usuario: {message}

Por favor, ayuda con este skill. Explica los cambios y proporciona el código completo si es necesario."""

            provider_map = {
                "ollama": ProviderType.OLLAMA,
                "openai": ProviderType.OPENAI,
                "gemini": ProviderType.GEMINI,
                "groq": ProviderType.GROQ,
            }

            ptype = provider_map[provider]
            if provider != "ollama":
                llm_manager.set_api_key(ptype, credential_store.get_api_key(provider) or "")
            llm_manager.set_active_provider(ptype)

            def _extract_suggested_code(text: str):
                import re
                t = str(text or "")
                code_blocks = re.findall(r"```python\s*([\s\S]*?)```", t)
                if code_blocks:
                    return code_blocks[-1].strip(), "Se sugirió código modificado. Revisa antes de aplicar."

                m = re.search(r"(^|\n)(def\s+execute\s*\(.*?\)\s*:\s*[\s\S]*)$", t)
                if m:
                    return (m.group(2) or "").strip(), "Se extrajo código desde la respuesta (sin bloque ```python```). Revisa antes de aplicar."

                return None, None

            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response_text = ""
            async for chunk in llm_manager.generate(prompt=full_prompt, system="", stream=False):
                response_text += chunk

            if not response_text.strip():
                return {"error": "No se recibió respuesta del modelo", "needs_config": False}

            suggested_code, changes_description = _extract_suggested_code(response_text)

            # Segundo intento automático si el modelo respondió solo con explicación.
            if not suggested_code:
                retry_prompt = (
                    "IMPORTANTE: Devuelve SOLO el archivo completo skill.py (sin explicación, sin markdown, sin encabezados).\n"
                    "Debe contener def execute(context): y ser código Python válido.\n\n"
                    "Reescribe el skill completo ahora."
                )
                response_text_2 = ""
                async for chunk in llm_manager.generate(prompt=retry_prompt + "\n\n" + full_prompt, system="", stream=False):
                    response_text_2 += chunk

                code2, desc2 = _extract_suggested_code(response_text_2)
                if code2:
                    suggested_code = code2
                    changes_description = desc2 or "Código generado en segundo intento. Revisa antes de aplicar."
                    # Mantener respuesta original (explicación) y usar el código del segundo intento

            return {
                "success": True,
                "response": response_text,
                "suggested_code": suggested_code,
                "changes_description": changes_description,
                "provider": provider,
                "history": history,
            }
        except Exception as e:
            return {"error": str(e), "needs_config": False}
    
    @app.get("/api/marketplace/skills")
    async def get_marketplace_skills():
        """Obtener skills disponibles en el marketplace"""
        try:
            # Skills de ejemplo para el marketplace
            return {
                "success": True,
                "skills": [
                    {
                        "id": "weather_check",
                        "name": "Consultar Clima",
                        "description": "Obtiene el clima actual de cualquier ciudad",
                        "author": "MiIA Team",
                        "version": "1.0",
                        "downloads": 1234,
                        "rating": 4.5,
                        "permissions": ["network"],
                        "installed": False
                    },
                    {
                        "id": "task_manager",
                        "name": "Gestor de Tareas",
                        "description": "Crea y gestiona tareas pendientes",
                        "author": "MiIA Team", 
                        "version": "1.2",
                        "downloads": 892,
                        "rating": 4.8,
                        "permissions": ["fs_write", "fs_read"],
                        "installed": False
                    },
                    {
                        "id": "system_monitor",
                        "name": "Monitor de Sistema",
                        "description": "Muestra uso de CPU, RAM y disco",
                        "author": "Community",
                        "version": "0.9",
                        "downloads": 567,
                        "rating": 4.2,
                        "permissions": ["fs_read"],
                        "installed": False
                    },
                    {
                        "id": "crypto_price",
                        "name": "Precio Criptomonedas",
                        "description": "Consulta precios de BTC, ETH y más",
                        "author": "CryptoDev",
                        "version": "2.0",
                        "downloads": 2156,
                        "rating": 4.6,
                        "permissions": ["network"],
                        "installed": False
                    }
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.post("/api/marketplace/install")
    async def install_marketplace_skill(data: dict):
        """Instalar skill desde el marketplace"""
        try:
            skill_id = data.get("skill_id")
            if not skill_id:
                return {"success": False, "error": "Skill ID requerido"}
            
            # Por ahora solo simulamos la instalación
            return {
                "success": True,
                "message": f"Skill '{skill_id}' instalada correctamente",
                "skill_id": skill_id
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ============== CREDENTIAL VAULT ENDPOINTS ==============
    
    @app.post("/api/credentials/store")
    async def store_skill_credentials(data: dict):
        """Almacenar credenciales temporales para una skill"""
        try:
            from core.SkillCredentialVault import credential_vault
            
            skill_id = data.get("skill_id")
            credentials = data.get("credentials", {})
            ttl_seconds = data.get("ttl_seconds", 300)
            
            if not skill_id or not credentials:
                return {"success": False, "error": "skill_id y credentials son requeridos"}
            
            session_id = credential_vault.store_credentials(skill_id, credentials, ttl_seconds)
            
            return {
                "success": True,
                "session_id": session_id,
                "message": "Credenciales almacenadas temporalmente",
                "expires_in": ttl_seconds
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.post("/api/credentials/release")
    async def release_skill_credentials(data: dict):
        """Liberar y limpiar credenciales de forma segura"""
        try:
            from core.SkillCredentialVault import credential_vault
            
            session_id = data.get("session_id")
            if not session_id:
                return {"success": False, "error": "session_id requerido"}
            
            result = credential_vault.release_credentials(session_id)
            
            return {
                "success": result,
                "message": "Credenciales liberadas" if result else "No se pudieron liberar las credenciales"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.get("/api/credentials/stats")
    async def get_credential_vault_stats():
        """Obtener estadísticas del vault de credenciales"""
        try:
            from core.SkillCredentialVault import credential_vault
            
            stats = credential_vault.get_stats()
            return {"success": True, "stats": stats}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.post("/api/credentials/validate-request")
    async def validate_credential_request(data: dict):
        """Validar si una skill puede solicitar credenciales"""
        try:
            from core.SkillCredentialVault import credential_vault
            
            skill_id = data.get("skill_id")
            permissions = data.get("permissions", [])
            
            result = credential_vault.validate_skill_credential_request(skill_id, permissions)
            return {"success": True, "validation": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    return app

app = create_app()

async def run_web_server(host: str = "127.0.0.1", port: int = 8765):
    import uvicorn
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

def start_web_server_background(host: str = "127.0.0.1", port: int = 8765):
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(run_web_server(host=host, port=port))
        logger.info(f"MININA WebUI iniciada en http://{host}:{port}")
    except RuntimeError:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)
