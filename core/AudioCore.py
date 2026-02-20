import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import pyttsx3

logger = logging.getLogger("AudioCore")

# STT Offline (Vosk) + Micrófono (sounddevice)
_vosk = None
_sounddevice = None

try:
    import vosk
    _vosk = vosk
except Exception as e:
    logger.warning(f"Vosk no disponible: {e}")

try:
    import sounddevice as sd
    _sounddevice = sd
except Exception as e:
    logger.warning(f"sounddevice no disponible: {e}")

from core.CortexBus import bus


def _get_vosk_model_path() -> Optional[Path]:
    """Buscar modelo Vosk español en rutas relativas a la instalación."""
    # 1) Variable de entorno explícita
    env_path = os.environ.get("MIIA_VOSK_MODEL_DIR")
    if env_path:
        p = Path(env_path)
        if p.exists() and p.is_dir():
            return p

    # 2) Relativo al ejecutable (PyInstaller o instalación normal)
    try:
        # sys._MEIPASS es donde PyInstaller descomprime
        base = Path(sys._MEIPASS)  # type: ignore
    except Exception:
        base = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent.parent

    candidates = [
        base / "models" / "vosk-es-large",
        base / "assets" / "models" / "vosk-es-large",
        base / "vosk-es-large",
    ]
    for c in candidates:
        if c.exists() and c.is_dir():
            return c

    # 3) Modo desarrollo (repo local)
    dev_candidates = [
        Path(__file__).resolve().parent.parent / "assets" / "models" / "vosk-es-large",
        Path(__file__).resolve().parent.parent / "models" / "vosk-es-large",
    ]
    for c in dev_candidates:
        if c.exists() and c.is_dir():
            return c

    # 3) Modelo en assets/models (ubicación donde el usuario tiene el modelo)
    assets_candidates = [
        base / "assets" / "models" / "vosk-es-large",
        base / "assets" / "models" / "vosk-model-small-es-0.42",
        base / "assets" / "models" / "vosk-model-es-0.42",
        Path(__file__).resolve().parent.parent / "assets" / "models" / "vosk-es-large",
        Path(__file__).resolve().parent.parent / "assets" / "models" / "vosk-model-small-es-0.42",
    ]
    for c in assets_candidates:
        if c.exists() and c.is_dir():
            return c

    return None


class AudioCore:
    def __init__(self):
        self._tts = pyttsx3.init()
        self._rec: Optional[object] = None
        self._mic: bool = False
        self._model_path: Optional[Path] = None
        self._stt_available = False

        # Inicializar STT si Vosk y sounddevice están disponibles
        if _vosk and _sounddevice:
            self._model_path = _get_vosk_model_path()
            if self._model_path:
                try:
                    self._rec = _vosk.Model(str(self._model_path))
                    self._mic = True
                    self._stt_available = True
                    logger.info(f"STT inicializado con modelo: {self._model_path}")
                except Exception as e:
                    logger.warning(f"No se pudo cargar modelo Vosk: {e}")
            else:
                logger.warning("Modelo Vosk no encontrado. STT desactivado. Fallback a texto.")
        else:
            logger.warning("Vosk o sounddevice no disponibles. STT desactivado. Fallback a texto.")

    async def speak(self, text: str) -> None:
        def _sync_speak():
            self._tts.say(text)
            self._tts.runAndWait()

        await asyncio.get_running_loop().run_in_executor(None, _sync_speak)

    async def listen(self, timeout_s: float = 6.0) -> str:
        # Fallback a texto si no hay STT disponible
        if not self._stt_available or not self._rec or not self._mic:
            try:
                return await asyncio.get_running_loop().run_in_executor(None, lambda: input("> "))
            except Exception:
                return ""

        # Captura con sounddevice + reconocimiento Vosk
        import numpy as np
        import queue

        q: queue.Queue = queue.Queue()
        recognizer = _vosk.KaldiRecognizer(self._rec, 16000)

        def callback(indata, frames, time_info, status):
            if status:
                logger.debug(f"sounddevice status: {status}")
            # Convertir a int16 (lo que espera Vosk)
            data = (indata * 32767).astype(np.int16)
            q.put(data.copy())

        try:
            with _sounddevice.RawInputStream(
                samplerate=16000,
                blocksize=8000,
                dtype=np.int16,
                channels=1,
                callback=callback,
            ):
                end_time = asyncio.get_event_loop().time() + timeout_s
                while asyncio.get_event_loop().time() < end_time:
                    try:
                        data = q.get(timeout=0.1)
                        if recognizer.AcceptWaveform(data.tobytes()):
                            result = recognizer.Result()
                            if result:
                                import json
                                obj = json.loads(result)
                                text = obj.get("text", "")
                                if text:
                                    return text
                    except queue.Empty:
                        await asyncio.sleep(0.01)
                # Intentar obtener resultado parcial al final
                partial = recognizer.PartialResult()
                if partial:
                    import json
                    obj = json.loads(partial)
                    text = obj.get("partial", "")
                    if text:
                        return text
                return ""
        except Exception as e:
            logger.warning(f"Error en captura de voz: {e}")
            # Fallback a texto en caso de error
            try:
                return await asyncio.get_running_loop().run_in_executor(None, lambda: input("> "))
            except Exception:
                return ""


def wire_audio_to_bus(audio: AudioCore) -> None:
    async def _on_speak(data):
        try:
            msg = (data or {}).get("message")
            if msg:
                await audio.speak(msg)
        except Exception:
            pass

    bus.subscribe("user.SPEAK", _on_speak)
