#!/usr/bin/env python3
"""Reorganizar skills en directorios por categoría"""
import shutil
from pathlib import Path
from core.SkillVault import vault

print("📁 Reorganizando skills por categorías...")
print("-" * 50)

# Definir movimientos: (skill_id, categoria)
moves = [
    ("discord_bot", "bots"),
    ("slack_bot", "bots"),
]

for skill_id, category in moves:
    src = vault.live_dir / skill_id
    dst = vault.live_dir / category / skill_id
    
    if src.exists() and src.is_dir():
        # Crear directorio de categoría si no existe
        (vault.live_dir / category).mkdir(parents=True, exist_ok=True)
        
        # Mover skill
        if dst.exists():
            shutil.rmtree(dst)
        shutil.move(str(src), str(dst))
        print(f"✅ {skill_id} → {category}/")
    else:
        print(f"⚠️  {skill_id} no encontrado en live/")

print("-" * 50)
print("\n📊 Verificando reorganización:")

# Verificar resultado
for cat_dir in vault.live_dir.iterdir():
    if cat_dir.is_dir():
        skills = [d.name for d in cat_dir.iterdir() if d.is_dir()]
        if skills:
            print(f"📂 {cat_dir.name}: {', '.join(skills)}")

print("\n✅ Reorganización completada!")
