# Script para limpiar settings_view.py
with open('core/ui/views/settings_view.py', 'rb') as f:
    content = f.read()

# Remover bytes nulos que causan error de sintaxis
content = content.replace(b'\x00', b'')

with open('core/ui/views/settings_view.py', 'wb') as f:
    f.write(content)

print("Archivo limpiado")
