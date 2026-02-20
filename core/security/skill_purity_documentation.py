"""
MININA v3.0 - Sistema de Validación de Pureza de Skills
Documentación del Sistema de 3 Capas de Seguridad

================================================================================
                    ARQUITECTURA DE SEGURIDAD DE SKILLS
================================================================================

PRINCIPIO FUNDAMENTAL:
"Una Skill es una Caja Negra Pura: INPUT -> ACCIÓN -> OUTPUT"

FLUJO CORRECTO:
┌─────────┐     ┌──────────────────┐     ┌─────────────┐     ┌──────────┐
│ HUMANO  │ --> │ ORCHESTRATOR   │ --> │ SKILL PURA  │ --> │ SUPERVISOR│
└─────────┘     │ (Piensa y      │     │ (No piensa, │     │ (Valida)  │
                │  Decide)       │     │  Solo hace) │     └──────────┘
                └──────────────────┘     └─────────────┘

================================================================================
                         LAS 3 CAPAS DE PROTECCIÓN
================================================================================

┌─────────────────────────────────────────────────────────────────────────────┐
│ CAPA 1: SKILL PURITY VALIDATOR                                               │
│ Ubicación: core/security/skill_purity_validator.py                          │
│                                                                              │
│ Propósito: Detectar skills "impuras" mediante análisis AST estático          │
│                                                                              │
│ Detecta:                                                                     │
│ ✗ Llamadas a APIs de IA (OpenAI, Claude, etc.)                              │
│ ✗ Intentos de llamar otras skills                                           │
│ ✗ Patrones de escape del sandbox                                            │
│ ✗ Lógica condicional excesivamente compleja (>3 niveles de if)              │
│ ✗ Acceso a variables globales                                               │
│ ✗ Uso de funciones peligrosas (eval, exec, compile)                        │
│                                                                              │
│ Test de Pureza:                                                              │
│ "Si ejecuto esta skill sola, sin IA, ¿funciona igual?"                     │
│ Si SÍ → Skill pura ✓                                                        │
│ Si NO → Skill está pensando ✗                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ CAPA 2: SKILL SAFETY GATE (Integrado)                                      │
│ Ubicación: core/SkillSafetyGate.py (validación de pureza añadida)          │
│                                                                              │
│ Propósito: Validar skills antes de instalar/ejecutar                         │
│                                                                              │
│ Ahora incluye:                                                              │
│ ✓ Validación de pureza AST (SkillPurityValidator)                           │
│ ✓ Validación de seguridad tradicional                                      │
│ ✓ Generación de reporte de pureza (purity_report.json)                     │
│ ✓ Bloqueo de skills impuras en tiempo de instalación                       │
│                                                                              │
│ Flujo:                                                                       │
│ 1. Skill ZIP → Extracción → skill.py                                       │
│ 2. Análisis AST de pureza                                                  │
│ 3. Si impura → RECHAZAR + Reporte de violaciones                           │
│ 4. Si pura → Continuar con validación de seguridad                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ CAPA 3: SKILL EXECUTION VALIDATOR                                            │
│ Ubicación: core/security/skill_execution_validator.py                      │
│                                                                              │
│ Propósito: Validar ejecución en tiempo real en el Orchestrator             │
│                                                                              │
│ Valida:                                                                      │
│ ✓ Contexto de ejecución (sin info de usuario/objetivos)                    │
│ ✓ Pre-validación de pureza antes de ejecutar                               │
│ ✓ Resultado de ejecución (formato {success, result/error})                │
│ ✓ Tiempo de ejecución                                                      │
│ ✓ Intentos de escape durante ejecución                                     │
│                                                                              │
│ Bloquea:                                                                     │
│ ✗ Skills impuras en tiempo de ejecución                                    │
│ ✗ Contextos con información prohibida (user_id, history, goals)          │
│ ✗ Resultados inválidos (no dict, sin success, claves inesperadas)         │
│                                                                              │
│ Flujo:                                                                       │
│ 1. Orchestrator decide usar skill X                                        │
│ 2. Pre-valida pureza (rechaza si impura)                                   │
│ 3. Valida contexto (no user/goals/history)                                 │
│ 4. Ejecuta skill                                                           │
│ 5. Valida resultado                                                        │
│ 6. Retorna al Orchestrator                                                  │
└─────────────────────────────────────────────────────────────────────────────┘

================================================================================
                         CONTRATO INPUT/OUTPUT
================================================================================

INPUT (Contexto) - Solo esto puede recibir una skill pura:
{
    "action": str,        # REQUERIDO: Qué acción ejecutar
    "param1": any,       # Parámetros específicos de la acción
    "param2": any,
    ...
}

PROHIBIDO en contexto:
✗ user, user_id, user_name, user_email
✗ conversation_history, chat_history, previous_messages
✗ goal, objective, intent, objective_final
✗ system_state, orchestrator_state, agent_state
✗ llm, ai, model, openai, anthropic

OUTPUT (Resultado) - Solo esto puede retornar una skill pura:
{
    "success": bool,           # REQUERIDO: True/False
    "result": any (opcional),  # Datos de resultado (si success=True)
    "error": str (opcional)    # Mensaje de error (si success=False)
}

Claves permitidas: success, result, error, data, output, message, status

================================================================================
                         POLÍTICA DE FALLAR
================================================================================

POLÍTICA: FALLAR, NO IMPROVISAR

✗ NO intentar algo "parecido"
✗ NO hacer "más de lo lógico"
✗ NO "resolver como puedas"
✗ NO llamar a otra skill si falla

✓ SI falta un parámetro → retornar error claro
✓ SI acción no existe → retornar error con acciones válidas
✓ SI algo falla → retornar {success: False, error: "razón"}

================================================================================
                         ARCHIVOS CREADOS
================================================================================

1. core/security/skill_purity_validator.py
   - SkillPurityValidator: Clase principal de validación AST
   - PurityReport: Dataclass de reporte de pureza
   - validate_skill_purity(): Función de conveniencia
   - is_skill_pure(): Check rápido
   - get_purity_summary(): Estadísticas de pureza

2. core/security/skill_execution_validator.py
   - SkillExecutionValidator: Validación en tiempo de ejecución
   - ExecutionReport: Reporte de ejecución
   - execute_skill_safely(): Wrapper seguro para ejecutar skills

3. core/templates/skill_pura_template.py
   - Plantilla de skill que cumple con pureza
   - Documentación del contrato input/output
   - Ejemplos de uso correcto

4. Integración en core/SkillSafetyGate.py
   - Import de SkillPurityValidator
   - Validación de pureza en validate_extracted_dir()
   - Generación de purity_report.json
   - Bloqueo de skills impuras

================================================================================
                         USO EN ORQUESTADOR
================================================================================

Ejemplo de integración en Orchestrator:

```python
from core.security.skill_execution_validator import execute_skill_safely
from pathlib import Path

# En el Orchestrator, cuando decides ejecutar una skill:
def ejecutar_skill(skill_id: str, context: dict):
    skill_path = Path(f"skills_user/{skill_id}/skill.py")
    
    # Importar la skill
    import importlib.util
    spec = importlib.util.spec_from_file_location("skill", skill_path)
    skill_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(skill_module)
    
    # Ejecutar con validación de pureza
    report = execute_skill_safely(
        skill_id=skill_id,
        skill_path=skill_path,
        context=context,
        execute_fn=skill_module.execute
    )
    
    if report.success:
        return report.result
    else:
        # La skill era impura o falló
        return {"error": report.error}
```

================================================================================
                         EJEMPLO DE SKILL PURA
================================================================================

```python
def execute(context: dict) -> dict:
    # EXTRAER: Solo action + parámetros
    action = context.get("action", "")
    
    # VALIDAR: Acción requerida
    if not action:
        return {
            "success": False,
            "error": "Falta 'action'"
        }
    
    # EJECUTAR: Simple switch de acciones
    if action == "buscar":
        query = context.get("query", "")
        if not query:
            return {"success": False, "error": "Falta query"}
        
        # Hacer la búsqueda...
        resultados = api.buscar(query)
        
        return {
            "success": True,
            "result": resultados
        }
    
    else:
        # FALLAR: Acción desconocida
        return {
            "success": False,
            "error": f"Acción '{action}' no válida. Usa: buscar"
        }
```

================================================================================
                         BENEFICIOS DEL SISTEMA
================================================================================

1. SEGURIDAD: Skills no pueden escapar del sandbox
2. PREDICTIBILIDAD: Mismo input = mismo output siempre
3. DEBUGGEABILIDAD: Fácil rastrear qué skill falló y por qué
4. AISLAMIENTO: Una skill rota no afecta al sistema
5. AUDITORÍA: Reportes de pureza para cada skill
6. CONFIANZA: Skills de terceros pueden ser validadas automáticamente

================================================================================
                              MANTENIMIENTO
================================================================================

Para auditar skills existentes:
```python
from core.security.skill_purity_validator import get_purity_summary

summary = get_purity_summary(Path("skills_user"))
print(f"Pureza del sistema: {summary['purity_percentage']}%")
print(f"Skills impuras: {summary['impure_skills']}")
```

Para validar una skill específica:
```python
from core.security.skill_purity_validator import validate_skill_purity

report = validate_skill_purity(Path("skills_user/email_sender/skill.py"))
if not report.is_pure:
    print("Violaciones:", report.violations)
```

================================================================================
                             FIN DEL DOCUMENTO
================================================================================
"""
