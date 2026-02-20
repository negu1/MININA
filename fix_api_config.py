#!/usr/bin/env python3
"""
Script para verificar y corregir configuración de APIs
"""
import json
import os

def fix_api_config():
    config_path = 'data/api_config.json'
    
    if not os.path.exists(config_path):
        print(f"❌ No existe: {config_path}")
        return
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Verificar Groq
    groq_key = None
    
    # Buscar en formato nuevo (ai.groq)
    if 'ai' in config and 'groq' in config['ai']:
        groq_key = config['ai']['groq'].get('api_key', '')
        print(f"🔍 Encontrada key en formato nuevo: {groq_key[:20]}...")
    
    # Buscar en formato antiguo
    if 'apis' in config and 'Groq API' in config['apis']:
        old_key = config['apis']['Groq API'].get('key', '')
        if old_key and not groq_key:
            groq_key = old_key
            print(f"🔍 Encontrada key en formato antiguo: {groq_key[:20]}...")
        
        # Habilitar Groq si tiene key
        if groq_key:
            config['apis']['Groq API']['key'] = groq_key.replace('\n', '').replace(' ', '')
            config['apis']['Groq API']['enabled'] = True
            print("✅ Groq API habilitada")
    
    # Limpiar key de saltos de línea
    if groq_key:
        clean_key = groq_key.replace('\n', '').replace(' ', '').strip()
        if 'ai' not in config:
            config['ai'] = {}
        if 'groq' not in config['ai']:
            config['ai']['groq'] = {}
        config['ai']['groq']['api_key'] = clean_key
        print(f"✅ Key limpiada: {clean_key[:30]}...")
    
    # Guardar
    config['updated_at'] = "2026-02-20T10:00:00"
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("\n✅ Configuración actualizada")
    print(f"   Groq API: {'CONFIGURADA' if groq_key else 'NO CONFIGURADA'}")
    print(f"   Key: {clean_key[:40]}..." if groq_key else "   Key: N/A")

if __name__ == "__main__":
    fix_api_config()
