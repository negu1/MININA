# MiIA WebUI - Sistema de Protección contra Errores

## ¿Qué es esto?

Sistema completo de validación y diagnóstico para prevenir errores estructurales en `WebUI.py`.

## Herramientas Creadas

### 1. 🔍 Validador Estructural (`tools/validate_webui.py`)

**Uso:**
```bash
python tools/validate_webui.py
```

**Qué detecta:**
- ❌ Tags HTML desbalanceados (divs extras o faltantes)
- ❌ Paneles duplicados
- ❌ Errores de sintaxis Python
- ❌ Funciones JavaScript críticas faltantes
- ⚠️ Indentación incorrecta

**Salida:**
- Línea exacta del error
- Contexto del problema
- Sugerencia de corrección

---

### 2. 🏥 Diagnóstico Completo (`tools/webui_diagnostics.py`)

**Uso:**
```bash
python tools/webui_diagnostics.py
```

**Qué verifica:**
1. ✅ Estructura HTML_TEMPLATE
2. ✅ Balance de tags HTML
3. ✅ Paneles duplicados
4. ✅ Funciones JavaScript críticas
5. ✅ Sintaxis Python
6. ✅ Importaciones necesarias

**Genera:**
- Reporte detallado en consola
- Archivo `webui_diagnostics_report.txt`

---

### 3. 🚨 Pre-Commit Hook (`tools/pre_commit_hook.py`)

**Instalación:**
```bash
# Copiar a .git/hooks/pre-commit
copy tools\pre_commit_hook.py .git\hooks\pre-commit
```

**Función:**
- Ejecuta validación automática antes de cada commit
- Bloquea commits si hay errores
- Permite `--no-verify` para forzar (no recomendado)

---

## Flujo de Trabajo Recomendado

### Antes de Editar WebUI.py

1. **Ejecutar diagnóstico base:**
   ```bash
   python tools/webui_diagnostics.py
   ```

2. **Verificar estado actual:**
   ```bash
   python tools/validate_webui.py
   ```

### Durante la Edición

1. **Guardar cambios frecuentemente**

2. **Validar después de cada cambio mayor:**
   ```bash
   python tools/validate_webui.py
   ```

### Después de Editar

1. **Diagnóstico final:**
   ```bash
   python tools/webui_diagnostics.py
   ```

2. **Revisar reporte:**
   ```
   webui_diagnostics_report.txt
   ```

3. **Si todo pasa → Commit:**
   ```bash
   git add core/WebUI.py
   git commit -m "Cambios en WebUI"
   # El hook validará automáticamente
   ```

---

## Interpretar Errores

### Ejemplo 1: Tag div desbalanceado

```
❌ ERRORES (1):
-------------------------------------
Línea 283: Tag </div> mal cerrado en línea 283
  Contexto: Se esperaba </ninguno> pero se encontró </div>
  → Revisa la estructura HTML cerca de la línea 283. Posible div extra o faltante.
```

**Causa probable:** Tag `</div>` extra que no corresponde a ninguna apertura.

**Solución:**
- Ir a línea 283
- Verificar la estructura de paneles
- Eliminar el `</div>` sobrante o agregar `<div>` de apertura

---

### Ejemplo 2: Panel duplicado

```
❌ ERRORES (1):
-------------------------------------
Panel 'dashboard' aparece 2 veces (debe ser 1)
  → Elimina las definiciones duplicadas del panel 'dashboard'
```

**Causa probable:** Dos `<div id="panel-dashboard">` en el HTML.

**Solución:**
- Buscar `id="panel-dashboard"`
- Eliminar la definición duplicada

---

### Ejemplo 3: Error de sintaxis Python

```
❌ ERRORES (1):
-------------------------------------
Línea 4215: Error de sintaxis Python: unexpected EOF while parsing
  → Revisa el código Python cerca de esta línea
```

**Causa probable:** Falta cerrar comillas, paréntesis, o indentación incorrecta.

**Solución:**
- Verificar líneas anteriores a 4215
- Buscar strings sin cerrar o paréntesis desbalanceados

---

## Comandos Útiles

### Validación rápida
```bash
python tools/validate_webui.py
```

### Diagnóstico completo con reporte
```bash
python tools/webui_diagnostics.py
```

### Verificar sintaxis Python
```bash
python -m py_compile core/WebUI.py
```

### Forzar commit (ignorar validación) - NO RECOMENDADO
```bash
git commit --no-verify -m "mensaje"
```

---

## Estructura de Archivos

```
MiIA-Product-20/
├── core/
│   └── WebUI.py              # Archivo principal a proteger
├── tools/
│   ├── validate_webui.py      # Validador estructural
│   ├── webui_diagnostics.py   # Diagnóstico completo
│   └── pre_commit_hook.py     # Hook para git
└── webui_diagnostics_report.txt  # Reporte generado
```

---

## Solución de Problemas

### El validador reporta errores falsos

Si el validador detecta errores en código JavaScript válido:

1. Verificar que las template literals usan backticks correctamente
2. Asegurar que los strings JavaScript están bien cerrados
3. Ejecutar diagnóstico para segunda opinión

### Diagnóstico lento en archivos grandes

- Es normal para archivos >5000 líneas
- El validador procesa todo el HTML_TEMPLATE
- Considerar dividir WebUI.py en módulos futuros

### Hooks no se ejecutan

1. Verificar que `.git/hooks/pre-commit` existe
2. Verificar permisos de ejecución (en Linux/Mac)
3. En Windows: usar `pre-commit` sin extensión

---

## Reglas de Oro

1. ✅ **Siempre validar antes de reiniciar el servidor**
2. ✅ **Siempre revisar el reporte de diagnóstico**
3. ✅ **Nunca ignorar errores de sintaxis Python**
4. ✅ **Validar después de cambios en HTML_TEMPLATE**
5. ❌ **Nunca hacer commit sin validar primero**

---

## Soporte

Si encuentras falsos positivos o el validador falla:

1. Revisar `webui_diagnostics_report.txt`
2. Verificar línea específica reportada
3. Corregir manualmente si es necesario
4. Reportar patrones que generan falsos positivos

---

**Versión:** 1.0  
**Creado:** 2026-02-19  
**Para:** MiIA Product-20 v1.0.0
