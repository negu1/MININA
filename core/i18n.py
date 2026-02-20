"""
Sistema de Internacionalización (i18n) para MiIA Product-20
Soporta 3 idiomas: Español (es), English (en), Português (pt)
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class I18n:
    """Gestor de traducciones"""
    
    DEFAULT_LANGUAGE = "es"
    SUPPORTED_LANGUAGES = ["es", "en", "pt"]
    
    def __init__(self):
        self._translations: Dict[str, Dict[str, Any]] = {}
        self._current_lang = self.DEFAULT_LANGUAGE
        self._locales_dir = Path(__file__).parent.parent / "locales"
        self._load_all_translations()
        
        # Intentar cargar idioma guardado
        self._load_saved_language()
    
    def _load_all_translations(self):
        """Cargar todos los archivos de traducción"""
        for lang_code in self.SUPPORTED_LANGUAGES:
            file_path = self._locales_dir / f"{lang_code}.json"
            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        self._translations[lang_code] = json.load(f)
                except Exception as e:
                    print(f"Error cargando traducción {lang_code}: {e}")
    
    def _load_saved_language(self):
        """Cargar idioma guardado en .env o config"""
        # Primero intentar desde .env
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("MIIA_LANGUAGE="):
                            lang = line.strip().split("=", 1)[1].strip('"\'')
                            if lang in self.SUPPORTED_LANGUAGES:
                                self._current_lang = lang
                                return
            except Exception:
                pass
        
        # Intentar desde archivo de config
        config_file = Path(__file__).parent.parent / "config" / "settings.json"
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    lang = data.get("language")
                    if lang in self.SUPPORTED_LANGUAGES:
                        self._current_lang = lang
            except Exception:
                pass
    
    def set_language(self, lang_code: str):
        """Cambiar idioma activo"""
        if lang_code in self.SUPPORTED_LANGUAGES:
            self._current_lang = lang_code
            self._save_language(lang_code)
        else:
            raise ValueError(f"Idioma no soportado: {lang_code}. Use: {self.SUPPORTED_LANGUAGES}")
    
    def _save_language(self, lang_code: str):
        """Guardar idioma en .env"""
        env_file = Path(__file__).parent.parent / ".env"
        try:
            lines = []
            if env_file.exists():
                with open(env_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            
            # Buscar y reemplazar línea existente
            found = False
            for i, line in enumerate(lines):
                if line.startswith("MIIA_LANGUAGE="):
                    lines[i] = f'MIIA_LANGUAGE={lang_code}\n'
                    found = True
                    break
            
            # Si no existe, agregar
            if not found:
                lines.append(f'MIIA_LANGUAGE={lang_code}\n')
            
            with open(env_file, "w", encoding="utf-8") as f:
                f.writelines(lines)
        except Exception as e:
            print(f"Error guardando idioma: {e}")
    
    def get(self, key: str, default: Optional[str] = None) -> str:
        """
        Obtener traducción por clave (notación punto: "webui.title")
        """
        try:
            keys = key.split(".")
            value = self._translations.get(self._current_lang, {})
            for k in keys:
                value = value.get(k, {})
                if not isinstance(value, dict):
                    return str(value)
            return default or key
        except Exception:
            return default or key
    
    def get_language_name(self, lang_code: str = None) -> str:
        """Obtener nombre del idioma"""
        code = lang_code or self._current_lang
        trans = self._translations.get(code, {})
        return trans.get("language_name", code)
    
    def get_current_language(self) -> str:
        """Obtener código de idioma actual"""
        return self._current_lang
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Obtener diccionario de idiomas soportados"""
        return {
            code: self.get_language_name(code)
            for code in self.SUPPORTED_LANGUAGES
        }


# Instancia global
i18n = I18n()


# Funciones de conveniencia
def _(key: str, default: Optional[str] = None) -> str:
    """Función de traducción global"""
    return i18n.get(key, default)


def set_language(lang_code: str):
    """Cambiar idioma global"""
    i18n.set_language(lang_code)


def get_language() -> str:
    """Obtener idioma actual"""
    return i18n.get_current_language()
