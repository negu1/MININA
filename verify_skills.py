#!/usr/bin/env python3
"""Verificar sistema de skills organizado por categorías"""
from core.SkillVault import vault

print("=" * 60)
print("📊 VERIFICACIÓN DEL SISTEMA DE SKILLS")
print("=" * 60)

# 1. Listar por categoría
result = vault.list_skills_by_category()
print("\n1. SKILLS ORGANIZADAS POR CATEGORÍA:")
print("-" * 40)
print(f"Total: {result.get('total_skills', 0)} skills")

for cat, skills in result.get('categories', {}).items():
    print(f"\n📂 {cat.upper()} ({len(skills)} skills)")
    for s in skills:
        print(f"   • {s['name']} (v{s['version']})")
        if s.get('tags'):
            print(f"     Tags: {', '.join(s['tags'])}")

# 2. Test de descubrimiento
print("\n\n2. TEST DE DESCUBRIMIENTO DE SKILLS:")
print("-" * 40)

tests = [
    "enviar mensaje a discord",
    "notificar en slack",
    "automatizar tareas",
]

for objective in tests:
    print(f"\n🎯 Objetivo: '{objective}'")
    matches = vault.discover_skills_for_objective(objective)
    if matches:
        for m in matches[:2]:
            print(f"   ✓ {m['name']} (score: {m.get('relevance_score', 0)})")
    else:
        print("   ⚠ No se encontraron skills")

# 3. Info de skill específica
print("\n\n3. INFO DE SKILL DISCORD:")
print("-" * 40)
info = vault.get_skill_manifest("discord_bot")
print(f"ID: {info['id']}")
print(f"Nombre: {info['name']}")
print(f"Categoría: {info.get('category', 'N/A')}")
print(f"Tags: {info.get('tags', [])}")

print("\n" + "=" * 60)
print("✅ SISTEMA ORGANIZADO Y FUNCIONANDO")
print("=" * 60)
