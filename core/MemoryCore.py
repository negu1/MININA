"""
MININA Memory Core
==================
Sistema de Memoria Unificado (STM, MTM, LTM) para MININA.
Adaptado del MemoryCore de MIIA (Diamond UMS).

Tipos de Memoria:
- STM (Short-Term): Sesiones temporales, cache en memoria
- MTM (Medium-Term): Contexto reciente, SQLite volátil
- LTM (Long-Term): Conocimiento persistente, SQLite + opcional vectores

Features:
- Trust scoring (filtrado de calidad)
- Garage system (PRIMARY/SECONDARY/QUARANTINE)
- Búsqueda híbrida (exacta + semántica)
- Consolidación automática STM → LTM
"""
import os
import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from core.logging_config import get_logger
from core.config import get_settings

logger = get_logger("MININA.MemoryCore")


class MemoryTier(Enum):
    """Niveles de memoria según duración."""
    STM = "short_term"      # Sesión actual (minutos)
    MTM = "medium_term"     # Contexto reciente (horas/días)
    LTM = "long_term"       # Conocimiento permanente (persistente)


class Garage(Enum):
    """Clasificación de calidad del conocimiento."""
    PRIMARY = "primary"     # Alta confianza (>=0.99)
    SECONDARY = "secondary" # Confianza media (0.80-0.99)
    QUARANTINE = "quarantine"  # Baja confianza (<0.80), requiere validación


class Stability(Enum):
    """Estabilidad del conocimiento."""
    VOLATILE = "volatile"   # Temporal, puede cambiar
    STABLE = "stable"       # Consolidado, poco cambio
    PERMANENT = "permanent" # Verdad fundamental


@dataclass
class MemoryEntry:
    """Entrada de memoria unificada."""
    id: str
    content: str
    memory_tier: str
    garage: str
    stability: str
    source: str
    timestamp: str
    confidence: float
    access_count: int = 0
    last_accessed: Optional[str] = None
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SessionContext:
    """Contexto de sesión (STM)."""
    session_id: str
    interactions: List[Dict[str, Any]]
    created_at: str
    last_activity: str
    metadata: Dict[str, Any]


class MININAMemoryCore:
    """
    Núcleo de memoria unificado para MININA.
    
    Integra:
    1. STM: Cache de sesiones en memoria (interacciones recientes)
    2. MTM: Contexto medio plazo (últimas horas) en SQLite
    3. LTM: Conocimiento permanente con búsqueda semántica
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.data_dir = self.settings.DATA_DIR / "memory"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Paths
        self.stm_file = self.data_dir / "stm_cache.json"
        self.db_path = self.data_dir / "memory_vault.db"
        self.quarantine_file = self.data_dir / "quarantine.json"
        
        # STM: Cache en memoria
        self._stm_cache: Dict[str, SessionContext] = {}
        self._stm_max_size = 50  # Interacciones por sesión
        
        # Inicializar SQLite
        self._init_database()
        
        # Cargar STM previo
        self._load_stm_cache()
        
        logger.info(f"MININAMemoryCore inicializado en {self.data_dir}")
    
    # ==================== INICIALIZACIÓN ====================
    
    def _init_database(self):
        """Inicializa la base de datos SQLite para MTM y LTM."""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        
        # Tabla MTM: Contexto reciente (mediano plazo)
        c.execute('''
            CREATE TABLE IF NOT EXISTS medium_term_memory (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                content TEXT,
                role TEXT,
                timestamp TEXT,
                stability TEXT,
                metadata TEXT,
                expires_at TEXT
            )
        ''')
        
        # Tabla LTM: Conocimiento de largo plazo
        c.execute('''
            CREATE TABLE IF NOT EXISTS long_term_memory (
                id TEXT PRIMARY KEY,
                content TEXT,
                category TEXT,
                garage TEXT,
                stability TEXT,
                source TEXT,
                timestamp TEXT,
                confidence REAL,
                access_count INTEGER DEFAULT 0,
                last_accessed TEXT,
                metadata TEXT
            )
        ''')
        
        # Tabla de Facts: Hechos estructurados (tripletas)
        c.execute('''
            CREATE TABLE IF NOT EXISTS facts (
                id TEXT PRIMARY KEY,
                subject TEXT,
                predicate TEXT,
                object TEXT,
                confidence REAL,
                timestamp TEXT,
                garage TEXT
            )
        ''')
        
        # Índices para búsqueda eficiente
        c.execute('CREATE INDEX IF NOT EXISTS idx_mtm_session ON medium_term_memory(session_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_mtm_expires ON medium_term_memory(expires_at)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_ltm_category ON long_term_memory(category)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_ltm_garage ON long_term_memory(garage)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_facts_subject ON facts(subject)')
        
        conn.commit()
        conn.close()
        logger.debug("Base de datos de memoria inicializada")
    
    # ==================== STM (SHORT-TERM MEMORY) ====================
    
    def _load_stm_cache(self):
        """Carga cache STM desde disco."""
        if self.stm_file.exists():
            try:
                with open(self.stm_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for sid, sdata in data.items():
                        self._stm_cache[sid] = SessionContext(**sdata)
                logger.debug(f"STM cache cargado: {len(self._stm_cache)} sesiones")
            except Exception as e:
                logger.warning(f"Error cargando STM cache: {e}")
    
    def _save_stm_cache(self):
        """Persiste cache STM a disco."""
        try:
            data = {
                sid: {
                    'session_id': sc.session_id,
                    'interactions': sc.interactions,
                    'created_at': sc.created_at,
                    'last_activity': sc.last_activity,
                    'metadata': sc.metadata
                }
                for sid, sc in self._stm_cache.items()
            }
            with open(self.stm_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error guardando STM cache: {e}")
    
    def add_to_stm(self, session_id: str, role: str, content: str, 
                   metadata: Optional[Dict] = None):
        """
        Añade interacción a la memoria de corto plazo.
        
        Args:
            session_id: ID de la sesión
            role: 'user', 'assistant', 'system'
            content: Contenido del mensaje
            metadata: Datos adicionales
        """
        if session_id not in self._stm_cache:
            now = datetime.now().isoformat()
            self._stm_cache[session_id] = SessionContext(
                session_id=session_id,
                interactions=[],
                created_at=now,
                last_activity=now,
                metadata={}
            )
        
        session = self._stm_cache[session_id]
        
        entry = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        session.interactions.append(entry)
        session.last_activity = datetime.now().isoformat()
        
        # Mantener límite de tamaño
        if len(session.interactions) > self._stm_max_size:
            removed = session.interactions.pop(0)
            # Consolidar a MTM automáticamente
            self._consolidate_to_mtm(session_id, removed)
        
        # Persistir periódicamente
        if len(session.interactions) % 10 == 0:
            self._save_stm_cache()
        
        logger.debug(f"Añadido a STM [{session_id}]: {content[:50]}...")
    
    def get_stm_context(self, session_id: str, limit: int = 10) -> List[Dict]:
        """
        Obtiene contexto reciente de la sesión.
        
        Returns:
            Lista de interacciones recientes
        """
        if session_id not in self._stm_cache:
            return []
        
        session = self._stm_cache[session_id]
        return session.interactions[-limit:]
    
    def get_recent_context_str(self, session_id: str, limit: int = 5) -> str:
        """Obtiene contexto reciente formateado como string."""
        interactions = self.get_stm_context(session_id, limit)
        lines = []
        for inter in interactions:
            role = "Usuario" if inter['role'] == 'user' else "MININA"
            lines.append(f"{role}: {inter['content']}")
        return "\n".join(lines)
    
    def clear_session(self, session_id: str):
        """Limpia una sesión de STM."""
        if session_id in self._stm_cache:
            # Consolidar todo a MTM antes de borrar
            session = self._stm_cache[session_id]
            for interaction in session.interactions:
                self._consolidate_to_mtm(session_id, interaction)
            del self._stm_cache[session_id]
            self._save_stm_cache()
            logger.info(f"Sesión {session_id} consolidada y limpiada")
    
    # ==================== MTM (MEDIUM-TERM MEMORY) ====================
    
    def _consolidate_to_mtm(self, session_id: str, interaction: Dict):
        """
        Consolida interacción de STM a MTM.
        
        MTM almacena contexto reciente (últimas horas) que no es
        aún conocimiento permanente pero es relevante para la conversación.
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            c = conn.cursor()
            
            entry_id = hashlib.md5(
                f"{session_id}:{interaction['timestamp']}".encode()
            ).hexdigest()
            
            # Expira en 24 horas por defecto
            expires = (datetime.now() + timedelta(hours=24)).isoformat()
            
            c.execute('''
                INSERT OR REPLACE INTO medium_term_memory
                (id, session_id, content, role, timestamp, stability, metadata, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry_id,
                session_id,
                interaction['content'],
                interaction['role'],
                interaction['timestamp'],
                Stability.VOLATILE.value,
                json.dumps(interaction.get('metadata', {})),
                expires
            ))
            
            conn.commit()
            conn.close()
            logger.debug(f"Consolidado a MTM: {entry_id}")
        except Exception as e:
            logger.error(f"Error consolidando a MTM: {e}")
    
    def get_mtm_context(self, session_id: str, limit: int = 20) -> List[Dict]:
        """Obtiene contexto de mediano plazo para una sesión."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            c = conn.cursor()
            
            c.execute('''
                SELECT content, role, timestamp, metadata
                FROM medium_term_memory
                WHERE session_id = ? AND expires_at > ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (session_id, datetime.now().isoformat(), limit))
            
            results = []
            for row in c.fetchall():
                results.append({
                    'content': row[0],
                    'role': row[1],
                    'timestamp': row[2],
                    'metadata': json.loads(row[3]) if row[3] else {}
                })
            
            conn.close()
            return list(reversed(results))  # Orden cronológico
        except Exception as e:
            logger.error(f"Error leyendo MTM: {e}")
            return []
    
    def cleanup_expired_mtm(self):
        """Limpia entradas MTM expiradas."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            c = conn.cursor()
            
            c.execute('''
                DELETE FROM medium_term_memory
                WHERE expires_at < ?
            ''', (datetime.now().isoformat(),))
            
            deleted = c.rowcount
            conn.commit()
            conn.close()
            
            if deleted > 0:
                logger.info(f"MTM cleanup: {deleted} entradas expiradas eliminadas")
        except Exception as e:
            logger.error(f"Error limpiando MTM: {e}")
    
    # ==================== LTM (LONG-TERM MEMORY) ====================
    
    def _determine_garage(self, confidence: float) -> str:
        """Determina el garage basado en confianza."""
        if confidence >= 0.99:
            return Garage.PRIMARY.value
        elif confidence >= 0.80:
            return Garage.SECONDARY.value
        return Garage.QUARANTINE.value
    
    def _protect_ingestion(self, content: str, source: str) -> Tuple[bool, float, str]:
        """
        Protección contra ingesta de baja calidad.
        
        Returns:
            (allowed, trust_score, reason)
        """
        trust_score = 0.5
        
        # Factor 1: Fuente
        source_reliability = {
            'user_direct': 1.0,
            'skill_execution': 0.9,
            'system': 0.95,
            'llm_inference': 0.6,
            'web_search': 0.4,
            'unknown': 0.3
        }
        trust_score *= source_reliability.get(source, 0.5)
        
        # Factor 2: Calidad del contenido
        if len(content) < 10:
            trust_score *= 0.5  # Muy corto, sospechoso
        
        if content.count('?') > 3:
            trust_score *= 0.8  # Muchas preguntas, incertidumbre
        
        # Verificar si pasa el umbral de cuarentena
        if trust_score < 0.3:
            self._quarantine_content(content, "LOW_TRUST", trust_score)
            return False, trust_score, "Baja confianza, enviado a cuarentena"
        
        return True, trust_score, "Aprobado"
    
    def store_in_ltm(self, content: str, category: str = "general",
                     source: str = "unknown", confidence: float = 0.5,
                     metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Almacena conocimiento en memoria de largo plazo.
        
        Args:
            content: Contenido a almacenar
            category: Categoría (general, skill, user_preference, etc.)
            source: Fuente del conocimiento
            confidence: Confianza (0.0 - 1.0)
            metadata: Datos adicionales
            
        Returns:
            Resultado de la operación
        """
        # Protección
        allowed, trust_score, reason = self._protect_ingestion(content, source)
        if not allowed:
            logger.warning(f"LTM ingesta bloqueada: {reason}")
            return {"success": False, "error": reason, "quarantined": True}
        
        garage = self._determine_garage(trust_score)
        
        # Si es cuarentena, no almacenar en LTM principal
        if garage == Garage.QUARANTINE.value:
            self._quarantine_content(content, "LOW_CONFIDENCE", trust_score)
            return {"success": False, "error": "Enviado a cuarentena", "garage": garage}
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            c = conn.cursor()
            
            entry_id = hashlib.md5(
                f"{content}:{datetime.now().isoformat()}".encode()
            ).hexdigest()
            
            c.execute('''
                INSERT INTO long_term_memory
                (id, content, category, garage, stability, source, timestamp, 
                 confidence, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry_id,
                content,
                category,
                garage,
                Stability.STABLE.value,
                source,
                datetime.now().isoformat(),
                trust_score,
                json.dumps(metadata or {})
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Almacenado en LTM [{garage}]: {content[:60]}...")
            return {
                "success": True,
                "id": entry_id,
                "garage": garage,
                "confidence": trust_score
            }
            
        except Exception as e:
            logger.error(f"Error almacenando en LTM: {e}")
            return {"success": False, "error": str(e)}
    
    def search_ltm(self, query: str, category: Optional[str] = None,
                   limit: int = 5) -> List[Dict]:
        """
        Busca en memoria de largo plazo.
        
        Estrategia:
        1. Búsqueda exacta/keywords
        2. Búsqueda por categoría
        3. Ordenar por confianza y recencia
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            c = conn.cursor()
            
            # Construir query
            sql = '''
                SELECT id, content, category, garage, confidence, timestamp, metadata
                FROM long_term_memory
                WHERE (content LIKE ? OR category LIKE ?)
            '''
            params = [f"%{query}%", f"%{query}%"]
            
            if category:
                sql += " AND category = ?"
                params.append(category)
            
            # Excluir cuarentena
            sql += " AND garage != ?"
            params.append(Garage.QUARANTINE.value)
            
            sql += " ORDER BY confidence DESC, timestamp DESC LIMIT ?"
            params.append(limit)
            
            c.execute(sql, params)
            
            results = []
            for row in c.fetchall():
                results.append({
                    'id': row[0],
                    'content': row[1],
                    'category': row[2],
                    'garage': row[3],
                    'confidence': row[4],
                    'timestamp': row[5],
                    'metadata': json.loads(row[6]) if row[6] else {}
                })
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Error buscando en LTM: {e}")
            return []
    
    def store_fact(self, subject: str, predicate: str, object_: str,
                   confidence: float = 1.0) -> bool:
        """
        Almacena un hecho estructurado (tripleta).
        
        Ejemplo: ("Juan", "prefiere", "Python")
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            c = conn.cursor()
            
            fact_id = hashlib.md5(
                f"{subject}:{predicate}:{object_}".encode()
            ).hexdigest()
            
            garage = self._determine_garage(confidence)
            
            c.execute('''
                INSERT OR REPLACE INTO facts
                (id, subject, predicate, object, confidence, timestamp, garage)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                fact_id,
                subject,
                predicate,
                object_,
                confidence,
                datetime.now().isoformat(),
                garage
            ))
            
            conn.commit()
            conn.close()
            logger.debug(f"Fact almacenado: ({subject}, {predicate}, {object_})")
            return True
            
        except Exception as e:
            logger.error(f"Error almacenando fact: {e}")
            return False
    
    def query_facts(self, subject: Optional[str] = None,
                    predicate: Optional[str] = None,
                    object_: Optional[str] = None) -> List[Dict]:
        """Consulta hechos estructurados."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            c = conn.cursor()
            
            conditions = []
            params = []
            
            if subject:
                conditions.append("subject LIKE ?")
                params.append(f"%{subject}%")
            if predicate:
                conditions.append("predicate LIKE ?")
                params.append(f"%{predicate}%")
            if object_:
                conditions.append("object LIKE ?")
                params.append(f"%{object_}%")
            
            sql = "SELECT subject, predicate, object, confidence FROM facts"
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            sql += " ORDER BY confidence DESC"
            
            c.execute(sql, params)
            
            results = []
            for row in c.fetchall():
                results.append({
                    'subject': row[0],
                    'predicate': row[1],
                    'object': row[2],
                    'confidence': row[3]
                })
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Error consultando facts: {e}")
            return []
    
    # ==================== CUARENTENA ====================
    
    def _quarantine_content(self, content: str, reason: str, score: float):
        """Aísla contenido de baja calidad."""
        try:
            quarantine = []
            if self.quarantine_file.exists():
                with open(self.quarantine_file, 'r', encoding='utf-8') as f:
                    quarantine = json.load(f)
            
            entry = {
                'id': hashlib.md5(f"{content}:{datetime.now().isoformat()}".encode()).hexdigest(),
                'content': content,
                'reason': reason,
                'score': score,
                'timestamp': datetime.now().isoformat(),
                'status': 'quarantined'
            }
            
            quarantine.append(entry)
            
            # Limitar tamaño
            if len(quarantine) > 100:
                quarantine = quarantine[-100:]
            
            with open(self.quarantine_file, 'w', encoding='utf-8') as f:
                json.dump(quarantine, f, indent=2)
            
            logger.warning(f"[CUARENTENA] {reason}: {content[:50]}...")
            
        except Exception as e:
            logger.error(f"Error en cuarentena: {e}")
    
    def get_quarantine(self) -> List[Dict]:
        """Lista contenido en cuarentena."""
        if not self.quarantine_file.exists():
            return []
        
        try:
            with open(self.quarantine_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    
    def release_from_quarantine(self, entry_id: str) -> bool:
        """Libera contenido de cuarentena (manual o juez)."""
        try:
            quarantine = self.get_quarantine()
            entry = next((e for e in quarantine if e['id'] == entry_id), None)
            
            if not entry:
                return False
            
            # Mover a LTM con confianza ajustada
            result = self.store_in_ltm(
                entry['content'],
                source="quarantine_released",
                confidence=0.7,  # Confianza media tras validación
                metadata={'origin': 'quarantine', 'original_reason': entry['reason']}
            )
            
            if result['success']:
                # Remover de cuarentena
                quarantine = [e for e in quarantine if e['id'] != entry_id]
                with open(self.quarantine_file, 'w', encoding='utf-8') as f:
                    json.dump(quarantine, f, indent=2)
                logger.info(f"Liberado de cuarentena: {entry_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error liberando de cuarentena: {e}")
            return False
    
    # ==================== CONSOLIDACIÓN ====================
    
    def consolidate_session(self, session_id: str):
        """
        Consolida toda la sesión STM a LTM.
        Útil al cerrar una conversación importante.
        """
        if session_id not in self._stm_cache:
            return
        
        session = self._stm_cache[session_id]
        consolidated = 0
        
        for interaction in session.interactions:
            # Solo consolidar mensajes del usuario y respuestas importantes
            if interaction['role'] == 'user':
                result = self.store_in_ltm(
                    content=interaction['content'],
                    category="conversation",
                    source="session_consolidation",
                    confidence=0.6,
                    metadata={
                        'session_id': session_id,
                        'role': interaction['role']
                    }
                )
                if result['success']:
                    consolidated += 1
        
        logger.info(f"Sesión {session_id} consolidada: {consolidated} entradas")
        
        # Limpiar STM
        del self._stm_cache[session_id]
        self._save_stm_cache()
    
    # ==================== ESTADÍSTICAS ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """Estadísticas del sistema de memoria."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            c = conn.cursor()
            
            # Conteos
            c.execute("SELECT COUNT(*) FROM medium_term_memory")
            mtm_count = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM long_term_memory")
            ltm_count = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM facts")
            facts_count = c.fetchone()[0]
            
            # Por garage
            c.execute('''
                SELECT garage, COUNT(*) 
                FROM long_term_memory 
                GROUP BY garage
            ''')
            garage_stats = dict(c.fetchall())
            
            conn.close()
            
            return {
                "stm_sessions": len(self._stm_cache),
                "stm_total_interactions": sum(
                    len(s.interactions) for s in self._stm_cache.values()
                ),
                "mtm_entries": mtm_count,
                "ltm_entries": ltm_count,
                "facts": facts_count,
                "garage_distribution": garage_stats,
                "quarantine_count": len(self.get_quarantine())
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo stats: {e}")
            return {"error": str(e)}
    
    # ==================== BACKUP ====================
    
    def backup_memory(self) -> Dict[str, Any]:
        """Crea backup de la memoria."""
        try:
            backup_dir = self.data_dir / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Backup SQLite
            backup_db = backup_dir / f"memory_backup_{timestamp}.db"
            import shutil
            shutil.copy2(self.db_path, backup_db)
            
            # Backup STM
            backup_stm = backup_dir / f"stm_backup_{timestamp}.json"
            self._save_stm_cache()
            shutil.copy2(self.stm_file, backup_stm)
            
            logger.info(f"Backup de memoria creado: {timestamp}")
            return {
                "success": True,
                "timestamp": timestamp,
                "files": [str(backup_db), str(backup_stm)]
            }
            
        except Exception as e:
            logger.error(f"Error en backup: {e}")
            return {"success": False, "error": str(e)}


# Instancia global
memory_core = MININAMemoryCore()
