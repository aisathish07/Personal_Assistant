import urllib.request
from pathlib import Path

def ensure_openwakeword_models():
    base = Path(__file__).resolve().parent / "venv" / "Lib" / "site-packages" / "openwakeword" / "resources" / "models"
    base.mkdir(parents=True, exist_ok=True)

    models = {
        "melspectrogram.onnx":  "https://github.com/dscripka/openWakeWord/raw/v0.4.0/openwakeword/resources/models/melspectrogram.onnx",
        "embedding_model.onnx": "https://github.com/dscripka/openWakeWord/raw/v0.4.0/openwakeword/resources/models/embedding_model.onnx",
    }

    for name, url in models.items():
        target = base / name
        if not target.exists():
            print(f"Downloading {name} ...")
            urllib.request.urlretrieve(url, target)
            print(f"✅ Saved to {target}")

if __name__ == "__main__":
    ensure_openwakeword_models()