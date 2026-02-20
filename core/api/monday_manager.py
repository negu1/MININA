"""
MININA v3.0 - Monday.com Manager
API para operaciones con Monday.com (boards, items, columnas)
"""

import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from datetime import datetime


class MondayManager:
    """
    Manager de Monday.com para MININA
    
    Requiere:
    - API Token (de Monday.com Admin)
    
    Para obtener:
    1. Ve a https://monday.com/
    2. Click en tu avatar → Admin → API
    3. Copia el API Token
    """
    
    API_BASE_URL = "https://api.monday.com/v2"
    
    def __init__(self, config_path: str = "data/monday_config.json"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.api_token: Optional[str] = None
        self._load_config()
    
    def _load_config(self):
        """Cargar configuración guardada"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.api_token = data.get("api_token")
            except Exception as e:
                print(f"Error cargando configuración Monday.com: {e}")
    
    def _save_config(self):
        """Guardar configuración"""
        try:
            data = {
                "updated_at": datetime.now().isoformat(),
                "api_token": self.api_token
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando configuración Monday.com: {e}")
    
    def set_token(self, token: str) -> Dict[str, Any]:
        """Configurar token de Monday.com"""
        self.api_token = token
        self._save_config()
        
        # Verificar conexión
        test_result = self._test_auth()
        
        if test_result:
            return {
                "success": True,
                "message": "Token de Monday.com configurado y verificado"
            }
        else:
            return {
                "success": False,
                "error": "No se pudo verificar el token. Verifica que sea un API Token válido."
            }
    
    def _test_auth(self) -> bool:
        """Testear autenticación"""
        if not self.api_token:
            return False
        
        try:
            query = '{ me { id name } }'
            result = self._execute_query(query)
            return result.get("data", {}).get("me") is not None
        except:
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Obtener headers para requests"""
        return {
            "Authorization": self.api_token,
            "Content-Type": "application/json",
            "API-Version": "2024-01"
        }
    
    def _execute_query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Ejecutar query GraphQL"""
        url = self.API_BASE_URL
        
        data = {"query": query}
        if variables:
            data["variables"] = variables
        
        response = requests.post(url, headers=self._get_headers(), json=data, timeout=30)
        return response.json()
    
    def is_configured(self) -> bool:
        """Verificar si está configurado"""
        return bool(self.api_token)
    
    def list_boards(self, limit: int = 25) -> Dict[str, Any]:
        """Listar boards del usuario"""
        if not self.is_configured():
            return {"success": False, "error": "Monday.com no configurado"}
        
        try:
            query = f'''
            query {{
                boards(limit: {limit}) {{
                    id
                    name
                    state
                    board_folder_id
                    owner {{
                        id
                        name
                    }}
                }}
            }}
            '''
            
            result = self._execute_query(query)
            
            if "errors" in result:
                return {"success": False, "error": result["errors"][0]["message"]}
            
            boards = result.get("data", {}).get("boards", [])
            return {
                "success": True,
                "boards": [
                    {
                        "id": b["id"],
                        "name": b["name"],
                        "state": b["state"],
                        "owner": b["owner"]["name"] if b.get("owner") else None
                    }
                    for b in boards
                ]
            }
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_board_items(self, board_id: str, limit: int = 25) -> Dict[str, Any]:
        """Obtener items de un board"""
        if not self.is_configured():
            return {"success": False, "error": "Monday.com no configurado"}
        
        try:
            query = f'''
            query {{
                boards(ids: {board_id}) {{
                    items_page(limit: {limit}) {{
                        items {{
                            id
                            name
                            column_values {{
                                id
                                text
                                value
                            }}
                        }}
                    }}
                }}
            }}
            '''
            
            result = self._execute_query(query)
            
            if "errors" in result:
                return {"success": False, "error": result["errors"][0]["message"]}
            
            boards = result.get("data", {}).get("boards", [])
            if not boards:
                return {"success": False, "error": "Board no encontrado"}
            
            items = boards[0].get("items_page", {}).get("items", [])
            return {
                "success": True,
                "items": [
                    {
                        "id": item["id"],
                        "name": item["name"],
                        "columns": [
                            {
                                "id": col["id"],
                                "text": col["text"]
                            }
                            for col in item.get("column_values", [])
                        ]
                    }
                    for item in items
                ]
            }
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def create_item(self, board_id: str, item_name: str, column_values: Optional[Dict] = None) -> Dict[str, Any]:
        """Crear un item en un board"""
        if not self.is_configured():
            return {"success": False, "error": "Monday.com no configurado"}
        
        try:
            query = '''
            mutation CreateItem($boardId: ID!, $itemName: String!, $columnValues: JSON) {
                create_item(board_id: $boardId, item_name: $itemName, column_values: $columnValues) {
                    id
                    name
                }
            }
            '''
            
            variables = {
                "boardId": board_id,
                "itemName": item_name,
                "columnValues": json.dumps(column_values) if column_values else "{}"
            }
            
            result = self._execute_query(query, variables)
            
            if "errors" in result:
                return {"success": False, "error": result["errors"][0]["message"]}
            
            item = result.get("data", {}).get("create_item", {})
            return {
                "success": True,
                "item_id": item.get("id"),
                "name": item.get("name")
            }
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def update_item(self, item_id: str, column_values: Dict[str, Any]) -> Dict[str, Any]:
        """Actualizar columnas de un item"""
        if not self.is_configured():
            return {"success": False, "error": "Monday.com no configurado"}
        
        try:
            query = '''
            mutation ChangeColumnValue($itemId: ID!, $boardId: ID!, $columnId: String!, $value: JSON!) {
                change_column_value(item_id: $itemId, board_id: $boardId, column_id: $columnId, value: $value) {
                    id
                    name
                }
            }
            '''
            
            # Para simplificar, solo actualizamos la primera columna
            first_col = list(column_values.keys())[0] if column_values else None
            first_val = column_values.get(first_col) if column_values else None
            
            if not first_col:
                return {"success": False, "error": "Debes proporcionar al menos un valor de columna"}
            
            # Necesitamos el board_id del item
            get_item_query = f'''
            query {{
                items(ids: {item_id}) {{
                    board {{
                        id
                    }}
                }}
            }}
            '''
            
            item_result = self._execute_query(get_item_query)
            board_id = item_result.get("data", {}).get("items", [{}])[0].get("board", {}).get("id")
            
            if not board_id:
                return {"success": False, "error": "No se pudo obtener el board del item"}
            
            variables = {
                "itemId": item_id,
                "boardId": board_id,
                "columnId": first_col,
                "value": json.dumps({"text": first_val})
            }
            
            result = self._execute_query(query, variables)
            
            if "errors" in result:
                return {"success": False, "error": result["errors"][0]["message"]}
            
            return {
                "success": True,
                "message": f"Item {item_id} actualizado"
            }
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def delete_item(self, item_id: str) -> Dict[str, Any]:
        """Eliminar un item"""
        if not self.is_configured():
            return {"success": False, "error": "Monday.com no configurado"}
        
        try:
            query = '''
            mutation DeleteItem($itemId: ID!) {
                delete_item(item_id: $itemId) {
                    id
                }
            }
            '''
            
            variables = {"itemId": item_id}
            result = self._execute_query(query, variables)
            
            if "errors" in result:
                return {"success": False, "error": result["errors"][0]["message"]}
            
            return {
                "success": True,
                "message": f"Item {item_id} eliminado"
            }
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_config(self) -> Dict[str, Any]:
        """Obtener configuración actual"""
        return {
            "configured": self.is_configured(),
            "token": "***" if self.api_token else None
        }


# Singleton
monday_manager = MondayManager()
