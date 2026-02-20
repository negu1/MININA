"""
MININA v3.0 - Skill Pura Template
Plantilla para crear skills que cumplen con el principio de pureza

PRINCIPIO DE PUREZA:
- Skill = Caja negra: INPUT -> ACCIÓN -> OUTPUT
- Skill NO piensa, NO sabe del usuario, NO sabe del objetivo final
- Skill NO llama a otras skills (eso lo hace el Orchestrator)
- Contexto vive en el Agente, NO en la Skill
- Orquestación SIEMPRE externa

TEST DE PUREZA:
"Si ejecuto esta skill sola, sin IA, ¿funciona igual?"
Si SÍ -> Skill pura ✓
Si NO -> Skill está pensando, está mal ✗

FLUJO CORRECTO:
HUMANO -> AGENTE ORQUESTADOR -> SKILL PURA -> SUPERVISOR
"""


def execute(context: dict) -> dict:
    """
    Función principal de la skill - DEBE ser pura
    
    Args:
        context: {
            "action": str,      # Qué acción ejecutar (REQUERIDO)
            "param1": any,      # Parámetros específicos de la acción
            "param2": any,
            # ...
        }
    
    Returns:
        {
            "success": bool,           # True si la acción se ejecutó correctamente
            "result": any (opcional),  # Resultado de la acción (si success=True)
            "error": str (opcional)    # Mensaje de error (si success=False)
        }
    
    REGLAS:
    1. NO accedas a información del usuario (user_id, user_name, etc.)
    2. NO accedas al historial de conversación
    3. NO llames a otras skills
    4. NO uses lógica condicional compleja (máx 2-3 niveles de if)
    5. NO llames a APIs de IA (OpenAI, Claude, etc.)
    6. SIEMPRE retorna {"success": bool, ...}
    7. SIEMPRE maneja errores graceful (no crashes)
    """
    try:
        # Extraer acción del contexto
        action = context.get("action", "")
        
        # Validar que tenemos una acción
        if not action:
            return {
                "success": False,
                "error": "Falta 'action' en el contexto. Debes especificar qué acción ejecutar."
            }
        
        # ===== EJECUCIÓN DE ACCIONES =====
        # Aquí implementas las acciones específicas de tu skill
        # Cada acción debe ser simple y directa
        
        if action == "ejemplo":
            # Obtener parámetros específicos
            param1 = context.get("param1", "")
            param2 = context.get("param2", 0)
            
            # Ejecutar la acción
            resultado = _ejecutar_ejemplo(param1, param2)
            
            return {
                "success": True,
                "result": resultado
            }
        
        elif action == "otra_accion":
            # Otra acción simple
            return {
                "success": True,
                "result": "Resultado de otra acción"
            }
        
        else:
            # Acción no reconocida - NO intentar adivinar o improvisar
            return {
                "success": False,
                "error": f"Acción '{action}' no reconocida. Acciones válidas: ejemplo, otra_accion"
            }
            
    except Exception as e:
        # Error inesperado - reportar gracefulmente
        return {
            "success": False,
            "error": f"Error en skill: {str(e)}"
        }


def _ejecutar_ejemplo(param1: str, param2: int) -> dict:
    """
    Función auxiliar - también debe ser pura
    
    Esta función:
    - NO accede a variables globales
    - NO llama a otras skills
    - NO usa IA/LLM
    - Solo procesa los parámetros y retorna un resultado
    """
    # Procesamiento simple y directo
    resultado = {
        "param1_procesado": param1.upper(),
        "param2_doblado": param2 * 2,
        "mensaje": f"Procesado: {param1} con valor {param2}"
    }
    
    return resultado


# ===== EJEMPLOS DE USO =====
"""
Ejemplo de uso desde el Orchestrator:

    # El Orchestrator decide qué skill usar y con qué contexto
    contexto = {
        "action": "ejemplo",
        "param1": "hola mundo",
        "param2": 42
    }
    
    # El Orchestrator ejecuta la skill
    resultado = execute(contexto)
    
    # El Orchestrator procesa el resultado
    if resultado["success"]:
        print(f"Éxito: {resultado['result']}")
    else:
        print(f"Error: {resultado['error']}")

¿Por qué esto es puro?
- La skill no sabe quién es el usuario
- La skill no sabe por qué se llamó
- La skill solo recibe action + params y retorna result/error
- Si la ejecutas 100 veces con los mismos inputs, da el mismo output
- No hay efectos secundarios ocultos
"""
