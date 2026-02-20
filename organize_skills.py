#!/usr/bin/env python3
"""
Script para reorganizar skills existentes por categorías
Audita y organiza el sistema de skills de MININA
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import json
from core.SkillVault import vault

def audit_current_skills():
    """Auditar skills actuales y su organización"""
    print("🔍 AUDITORÍA DEL SISTEMA DE SKILLS")
    print("=" * 60)
    
    # Obtener skills organizadas por categoría
    result = vault.list_skills_by_category()
    
    if not result.get("success"):
        print(f"❌ Error: {result.get('error')}")
        return
    
    categories = result.get("categories", {})
    total = result.get("total_skills", 0)
    
    print(f"\n📊 Total de skills: {total}")
    print(f"📁 Categorías encontradas: {len(categories)}")
    print("-" * 60)
    
    for category, skills in sorted(categories.items()):
        print(f"\n📂 {category.upper()} ({len(skills)} skills)")
        for skill in skills:
            name = skill.get('name', skill.get('id', 'Unknown'))
            version = skill.get('version', '1.0')
            tags = skill.get('tags', [])
            desc = skill.get('description', '')[:50] + '...' if len(skill.get('description', '')) > 50 else skill.get('description', '')
            
            print(f"   └── {name} (v{version})")
            if tags:
                print(f"       Tags: {', '.join(tags)}")
            if desc:
                print(f"       {desc}")
    
    print("\n" + "=" * 60)

def categorize_existing_skills():
    """Categorizar skills existentes que no tienen categoría"""
    print("\n🏷️  CATEGORIZANDO SKILLS EXISTENTES")
    print("=" * 60)
    
    # Mapeo de skills a categorías basado en nombre y descripción
    category_mapping = {
        # Bots y Mensajería
        "discord_bot": "bots",
        "slack_bot": "bots",
        "telegram": "bots",
        "whatsapp": "bots",
        
        # Automatización y Productividad
        "email": "automation",
        "file_manager": "automation",
        "scheduler": "automation",
        
        # IA y Análisis
        "analyzer": "ai",
        "summarizer": "ai",
        "translator": "ai",
        
        # Sistema y Utilidades
        "system": "system",
        "backup": "system",
        "logger": "system",
    }
    
    categorized = 0
    
    # Recorrer todas las skills en live
    for skill_dir in vault.live_dir.iterdir():
        if not skill_dir.is_dir():
            continue
            
        manifest_path = skill_dir / "manifest.json"
        if not manifest_path.exists():
            continue
            
        try:
            data = json.loads(manifest_path.read_text())
            skill_id = data.get("id", skill_dir.name)
            
            # Si ya tiene categoría, saltar
            if data.get("category") and data.get("category") != "general":
                continue
            
            # Determinar categoría
            category = None
            
            # Por mapeo directo
            if skill_id in category_mapping:
                category = category_mapping[skill_id]
            else:
                # Por análisis de nombre/descripción
                name = data.get("name", "").lower()
                desc = data.get("description", "").lower()
                
                if any(word in name or word in desc for word in ["discord", "slack", "telegram", "bot", "mensaje", "mensajeria"]):
                    category = "bots"
                elif any(word in name or word in desc for word in ["email", "correo", "archivo", "file", "automatizar", "automation"]):
                    category = "automation"
                elif any(word in name or word in desc for word in ["analisis", "analysis", "ia", "ai", "inteligencia", "resumen", "summarize"]):
                    category = "ai"
                elif any(word in name or word in desc for word in ["sistema", "system", "backup", "log", "configuracion"]):
                    category = "system"
                else:
                    category = "general"
            
            # Actualizar manifest
            data["category"] = category
            if "tags" not in data:
                data["tags"] = []
            
            # Agregar tags basados en categoría
            if category == "bots" and "mensajeria" not in data["tags"]:
                data["tags"].append("mensajeria")
            elif category == "automation" and "automatizacion" not in data["tags"]:
                data["tags"].append("automatizacion")
            
            # Guardar manifest actualizado
            manifest_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Mover a directorio de categoría
            target_dir = vault.live_dir / category / skill_id
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Copiar archivos
            for f in skill_dir.iterdir():
                if f.is_file():
                    import shutil
                    shutil.copy2(f, target_dir / f.name)
            
            # Eliminar directorio antiguo
            import shutil
            shutil.rmtree(skill_dir, ignore_errors=True)
            
            print(f"✅ {skill_id} → categoría '{category}'")
            categorized += 1
            
        except Exception as e:
            print(f"❌ Error categorizando {skill_dir.name}: {e}")
    
    print(f"\n📊 Skills categorizadas: {categorized}")
    print("=" * 60)

def show_skill_discovery_demo():
    """Demo de descubrimiento de skills para objetivos"""
    print("\n🔮 DEMO: DESCUBRIMIENTO DE SKILLS POR OBJETIVO")
    print("=" * 60)
    
    test_objectives = [
        "Enviar mensaje a Discord",
        "Automatizar emails",
        "Analizar documentos",
        "Hacer backup de archivos",
    ]
    
    for objective in test_objectives:
        print(f"\n🎯 Objetivo: '{objective}'")
        print("-" * 40)
        
        matching = vault.discover_skills_for_objective(objective)
        
        if matching:
            print("   Skills relevantes encontradas:")
            for skill in matching[:3]:  # Top 3
                score = skill.get("relevance_score", 0)
                name = skill.get("name", skill.get("id", "Unknown"))
                category = skill.get("category", "unknown")
                print(f"   • {name} (score: {score}, cat: {category})")
        else:
            print("   No se encontraron skills relevantes")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    print("🚀 ORGANIZADOR DE SKILLS v3.0")
    print("=" * 60)
    
    # 1. Auditar estado actual
    audit_current_skills()
    
    # 2. Preguntar si reorganizar
    response = input("\n¿Reorganizar skills existentes por categorías? (s/n): ").lower().strip()
    
    if response == 's':
        categorize_existing_skills()
        
        # Mostrar resultado final
        print("\n📊 ESTADO FINAL:")
        audit_current_skills()
    else:
        print("⏭️  Saltando reorganización...")
    
    # 3. Demo de descubrimiento
    show_skill_discovery_demo()
    
    print("\n✅ Proceso completado!")
    print("\n💡 El OrchestratorAgent ahora puede:")
    print("   • Descubrir skills relevantes para objetivos")
    print("   • Acceder al catálogo organizado por categorías")
    print("   • Usar skills de Discord, Slack y más APIs de bots")
