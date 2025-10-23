#!/usr/bin/env python3
"""
debug_mic.py – Validate and test ONNX wake-word model
Checks ONNX integrity and monitors live mic confidence.
"""

import sounddevice as sd
import numpy as np
import time
import signal
import queue
import logging
from pathlib import Path
import onnx
from onnxruntime import InferenceSession
from openwakeword.model import Model

# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------
MODELS_DIR = Path(__file__).parent / "models"
ONNX_FILE = MODELS_DIR / "hey_jarvis.onnx"

# ------------------------------------------------------------
# Step 1 – Verify ONNX model integrity
# ------------------------------------------------------------
try:
    model = onnx.load(ONNX_FILE)
    onnx.checker.check_model(model)
    print("✅ ONNX structure is valid")

    session = InferenceSession(str(ONNX_FILE))
    print("✅ Model loaded successfully into ONNXRuntime\n")
except Exception as e:
    print(f"❌ ONNX validation failed: {e}")
    exit(1)

# ------------------------------------------------------------
# Step 2 – Initialize OpenWakeWord model
# ------------------------------------------------------------
try:
    oww_model = Model(
        wakeword_models=[str(ONNX_FILE)],
        inference_framework="onnx"
    )
    print(f"✅ Using ONNX model: {ONNX_FILE.name}\n")
except Exception as e:
    print(f"❌ Failed to initialize OpenWakeWord model: {e}")
    exit(1)

# ------------------------------------------------------------
# Step 3 – Setup mic stream
# ------------------------------------------------------------
SAMPLE_RATE = 16000
BLOCK_SIZE = 512
q = queue.Queue()
running = True

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")
log = logging.getLogger("mic-debug")

def audio_callback(indata, frames, time_info, status):
    if status:
        log.warning(status)
    q.put(indata.copy())

def stop_handler(sig, frame):
    global running
    running = False
    print("\n🛑 Stopping mic test...")
signal.signal(signal.SIGINT, stop_handler)

# ------------------------------------------------------------
# Step 4 – Stream & evaluate
# ------------------------------------------------------------
def mic_test():
    last_print = 0
    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        blocksize=BLOCK_SIZE,
        dtype="float32",
        callback=audio_callback
    ):
        log.info("🎤 Listening – say 'Hey Jarvis' (Ctrl+C to stop)...")
        while running:
            try:
                audio = q.get(timeout=0.5)
            except queue.Empty:
                continue

            # compute RMS volume
            rms = np.sqrt(np.mean(audio ** 2))
            db = 20 * np.log10(max(rms, 1e-7))

            # get model prediction
            try:
                pred = oww_model.predict(audio.flatten())
                score = list(pred.values())[0] if isinstance(pred, dict) else 0.0
            except Exception as e:
                log.warning(f"Predict error: {e}")
                score = 0.0

            now = time.time()
            if now - last_print > 0.1:
                print(f"\r🎚 Volume: {db:6.1f} dB   Score: {score:.3f}", end="")
                last_print = now

            if score > 0.6:
                print(f"\n🎤 Wake word detected! (score={score:.2f})")
                time.sleep(1.0)

# ------------------------------------------------------------
# Run
# ------------------------------------------------------------
mic_test()
