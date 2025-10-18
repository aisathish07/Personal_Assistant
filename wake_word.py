# wake_word.py  –  async callback, VAD gate, Ctrl-Space hot-key, ONNX downloader
from __future__ import annotations

import asyncio, time, logging, urllib.request, numpy as np, sounddevice as sd, webrtcvad
from pathlib import Path
from queue import Queue
from openwakeword.model import Model
import threading, keyboard   # pip install keyboard

logger = logging.getLogger("AI_Assistant.WakeWord")

def ensure_openwakeword_models() -> None:
    base = Path(__file__).resolve().parent / "venv" / "Lib" / "site-packages" / "openwakeword" / "resources" / "models"
    base.mkdir(parents=True, exist_ok=True)
    models = {
        "melspectrogram.onnx":  "https://github.com/dscripka/openWakeWord/raw/v0.4.0/openwakeword/resources/models/onnx/melspectrogram.onnx",
        "embedding_model.onnx": "https://github.com/dscripka/openWakeWord/raw/v0.4.0/openwakeword/resources/models/onnx/embedding_model.onnx",
    }
    for name, url in models.items():
        target = base / name
        if not target.exists():
            logger.info(f"Downloading {name}")
            urllib.request.urlretrieve(url, target)
            logger.info(f"✅ Saved {name}")

class WakeWordDetector:
    def __init__(self, input_queue: Queue, tts_engine) -> None:
        ensure_openwakeword_models()
        self.input_queue = input_queue
        self.tts_engine  = tts_engine
        self.stop_event  = asyncio.Event()
        self.stream      = None
        self.threshold   = 0.7
        self.debounce    = 1.0
        self.last_fire   = 0.0
        self.vad         = webrtcvad.Vad(1)   # 0-3, 1 = permissive
        model_dir        = Path(__file__).resolve().parent / "venv" / "Lib" / "site-packages" / "openwakeword" / "resources" / "models"
        hey_onnx         = model_dir / "hey_jarvis.onnx"
        
        if not hey_onnx.exists():
            logger.warning("No hey_jarvis.onnx – using embedded tflite")
            wpaths, framework, melspec, embed = ["hey_jarvis"], "tflite", None, None
        else:
            wpaths, framework, melspec, embed = [str(hey_onnx)], "onnx", str(model_dir / "melspectrogram.onnx"), str(model_dir / "embedding_model.onnx")
        try:
            self.model = Model(
    wakeword_models=wpaths,
    inference_framework=framework,
    melspec_model_path=melspec,
    embedding_model_path=embed
)
            logger.info("OpenWakeWord (%s) initialised with VAD pre-filter", framework)
        except Exception as e:
            logger.critical("Failed to initialise OpenWakeWord: %s", e)
            raise
        # global hot-key
        self.hotkey_thread = threading.Thread(target=self._hotkey_worker, daemon=True)
        self.hotkey_thread.start()

    def _hotkey_worker(self) -> None:
        keyboard.add_hotkey("ctrl+space", lambda: self.input_queue.put(("WAKE_WORD_DETECTED", True)))
        keyboard.wait()

    async def run(self) -> None:
        logger.info("Wake-word listener started (callback + VAD)")
        self.stream = sd.InputStream(channels=1, samplerate=16000, dtype="int16", blocksize=512, callback=self._audio_callback)
        self.stream.start()
        await self.stop_event.wait()
        self.stream.stop(); self.stream.close(); logger.info("Wake-word stream closed.")

    def stop(self) -> None:
        self.stop_event.set(); keyboard.unhook_all()

    def _audio_callback(self, indata, frames, time_info, status) -> None:
        if status: logger.warning("Audio callback status: %s", status)
        pcm16 = indata.tobytes()
        if not self.vad.is_speech(pcm16, 16000): return
        try:
            scores = self.model.predict(indata[:, 0])
            for name, prob in scores.items():
                now = time.time()
                if prob > self.threshold and (now - self.last_fire) > self.debounce:
                    self.last_fire = now; logger.info("Wake-word '%s' detected (%.2f)", name, prob)
                    self.input_queue.put(("WAKE_WORD_DETECTED", True))
        except Exception as e:
            logger.error("Error in wake-word callback: %s", e)