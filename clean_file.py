import os

# Leer archivo en modo binario
with open('core/ui/views/settings_view.py', 'rb') as f:
    content = f.read()

# Eliminar bytes nulos
content = content.replace(b'\x00', b'')

# Guardar archivo limpio
with open('core/ui/views/settings_view.py', 'wb') as f:
    f.write(content)

print("✅ Archivo limpiado - bytes nulos removidos")
