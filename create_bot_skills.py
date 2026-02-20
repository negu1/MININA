#!/usr/bin/env python3
"""
Script para crear skills de Discord y Slack con categorización
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.SkillVault import vault

def create_discord_skill():
    """Crear skill para Discord Bot"""
    code = '''"""
Discord Bot Skill - Comunicación y Moderación
Categoría: bots
"""
import os
from typing import Dict, Any

def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    """Ejecutar operaciones de Discord Bot"""
    try:
        import requests
        
        token = os.environ.get("DISCORD_BOT_TOKEN", "")
        if not token:
            return {
                "success": False,
                "error": "DISCORD_BOT_TOKEN no configurado"
            }
        
        action = context.get("action", "send_message")
        base_url = "https://discord.com/api/v10"
        headers = {
            "Authorization": f"Bot {token}",
            "Content-Type": "application/json"
        }
        
        if action == "send_message":
            channel_id = context.get("channel_id", "")
            message = context.get("message", "")
            
            if not channel_id or not message:
                return {"success": False, "error": "channel_id y message requeridos"}
            
            response = requests.post(
                f"{base_url}/channels/{channel_id}/messages",
                headers=headers,
                json={"content": message}
            )
            
            if response.status_code == 200:
                return {"success": True, "result": "Mensaje enviado"}
            else:
                return {"success": False, "error": f"Discord API: {response.status_code}"}
        
        elif action == "get_channels":
            guild_id = context.get("guild_id", "")
            if not guild_id:
                return {"success": False, "error": "guild_id requerido"}
            
            response = requests.get(
                f"{base_url}/guilds/{guild_id}/channels",
                headers=headers
            )
            
            if response.status_code == 200:
                return {"success": True, "channels": response.json()}
            else:
                return {"success": False, "error": f"Discord API: {response.status_code}"}
        
        return {"success": False, "error": f"Acción {action} no soportada"}
        
    except ImportError:
        return {"success": False, "error": "Instala: pip install requests"}
    except Exception as e:
        return {"success": False, "error": str(e)}
'''
    
    result = vault.save_skill(
        skill_id="discord_bot",
        name="Discord Bot",
        code=code,
        version="1.0.0",
        permissions=["network", "os.environ"],
        description="Skill para interactuar con Discord Bot API - enviar mensajes y gestionar canales"
    )
    
    # Agregar categoría al manifest
    manifest_path = vault.live_dir / "discord_bot" / "manifest.json"
    if manifest_path.exists():
        import json
        data = json.loads(manifest_path.read_text())
        data["category"] = "bots"
        data["tags"] = ["discord", "mensajeria", "comunicacion"]
        data["api_integration"] = "discord"
        manifest_path.write_text(json.dumps(data, indent=2))
    
    print(f"✅ Discord Bot skill: {result.get('message', 'Creada')}")
    return result


def create_slack_skill():
    """Crear skill para Slack API"""
    code = '''"""
Slack API Skill - Comunicación de Equipos
Categoría: bots
"""
import os
from typing import Dict, Any

def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    """Ejecutar operaciones de Slack"""
    try:
        import requests
        
        token = os.environ.get("SLACK_BOT_TOKEN", "")
        if not token:
            return {
                "success": False,
                "error": "SLACK_BOT_TOKEN no configurado"
            }
        
        action = context.get("action", "send_message")
        base_url = "https://slack.com/api"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        if action == "send_message":
            channel = context.get("channel", "")
            message = context.get("message", "")
            
            if not channel or not message:
                return {"success": False, "error": "channel y message requeridos"}
            
            response = requests.post(
                f"{base_url}/chat.postMessage",
                headers=headers,
                json={"channel": channel, "text": message}
            )
            
            data = response.json()
            if data.get("ok"):
                return {"success": True, "result": "Mensaje enviado a Slack"}
            else:
                return {"success": False, "error": data.get("error", "Error Slack")}
        
        elif action == "get_channels":
            response = requests.get(
                f"{base_url}/conversations.list",
                headers=headers,
                params={"types": "public_channel,private_channel"}
            )
            
            data = response.json()
            if data.get("ok"):
                return {"success": True, "channels": data.get("channels", [])}
            else:
                return {"success": False, "error": data.get("error", "Error Slack")}
        
        return {"success": False, "error": f"Acción {action} no soportada"}
        
    except ImportError:
        return {"success": False, "error": "Instala: pip install requests"}
    except Exception as e:
        return {"success": False, "error": str(e)}
'''
    
    result = vault.save_skill(
        skill_id="slack_bot",
        name="Slack Bot",
        code=code,
        version="1.0.0",
        permissions=["network", "os.environ"],
        description="Skill para interactuar con Slack API - enviar mensajes y listar canales"
    )
    
    # Agregar categoría al manifest
    manifest_path = vault.live_dir / "slack_bot" / "manifest.json"
    if manifest_path.exists():
        import json
        data = json.loads(manifest_path.read_text())
        data["category"] = "bots"
        data["tags"] = ["slack", "mensajeria", "comunicacion"]
        data["api_integration"] = "slack"
        manifest_path.write_text(json.dumps(data, indent=2))
    
    print(f"✅ Slack Bot skill: {result.get('message', 'Creada')}")
    return result


if __name__ == "__main__":
    print("🚀 Creando skills para APIs de Bots...")
    print("-" * 50)
    
    create_discord_skill()
    create_slack_skill()
    
    print("-" * 50)
    print("✅ Skills creadas exitosamente!")
    print("\n📋 Skills disponibles:")
    
    skills = vault.list_user_skills()
    for skill in skills:
        print(f"  - {skill['id']}: {skill['name']} (v{skill['version']})")
