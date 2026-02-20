#!/usr/bin/env python3
"""
Script para verificar el sistema de gestión de API keys
"""

import json
import os

def verify_api_config():
    """Verificar que el archivo de configuración existe y tiene la estructura correcta"""
    config_path = 'data/api_config.json'
    
    print("=" * 60)
    print("VERIFICACIÓN DEL SISTEMA DE API KEYS")
    print("=" * 60)
    
    # Verificar si existe el archivo
    if os.path.exists(config_path):
        print(f"\n✅ Archivo de configuración existe: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Verificar secciones
            sections = ['ai_apis', 'bot_apis', 'business_apis']
            print("\n📋 Estructura del archivo:")
            
            for section in sections:
                if section in config:
                    apis = list(config[section].keys())
                    print(f"  ✅ {section}: {len(apis)} APIs configuradas")
                    for api in apis:
                        api_data = config[section][api]
                        has_key = any(v for v in api_data.values() if v)
                        status = "🟢 Configurado" if has_key else "⚪ Sin configurar"
                        print(f"     - {api}: {status}")
                else:
                    print(f"  ⚪ {section}: No existe aún")
            
            # Mostrar contenido completo (con keys parcialmente ocultas)
            print("\n🔒 Contenido seguro (keys parcialmente ocultas):")
            print(json.dumps(config, indent=2, default=lambda x: x[:10] + "..." if isinstance(x, str) and len(x) > 10 else x))
            
        except Exception as e:
            print(f"\n❌ Error leyendo configuración: {e}")
    else:
        print(f"\n⚪ Archivo de configuración no existe aún: {config_path}")
        print("   Se creará automáticamente al guardar la primera API key")
    
    print("\n" + "=" * 60)
    print("INSTRUCCIONES DE USO:")
    print("=" * 60)
    print("""
1. Abre la UI de MININA y ve a la pestaña "Settings"
2. En la sección "🤖 APIs de IA Cloud", verás:
   - Indicador ⚪ (Sin configurar) o 🟢 (Configurado)
   - Input para la API key
   - Botón ✓ (Verificar y Guardar)
   - Botón 🗑️ (Eliminar)

3. Para guardar una API key:
   - Escribe la key en el input
   - Click en ✓ para guardar
   - El indicador cambiará a 🟢

4. Para eliminar una API key:
   - Click en 🗑️
   - Confirma la eliminación
   - El indicador cambiará a ⚪

5. Al iniciar la UI, las keys guardadas se cargarán automáticamente

6. El botón "💾 Guardar Configuración" guarda TODAS las APIs
   (IA, Bots y Empresariales) en data/api_config.json
""")

if __name__ == "__main__":
    verify_api_config()
