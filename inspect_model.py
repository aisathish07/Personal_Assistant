import onnx
from onnx import numpy_helper
from pathlib import Path

model_path = Path("models/hey_jarvis.onnx")
m = onnx.load(model_path)
print(f"✅ Model loaded: {model_path}")
print("")

# Show input and output tensors
print("🧩 Inputs:")
for inp in m.graph.input:
    shape = [d.dim_value for d in inp.type.tensor_type.shape.dim]
    print(f"  - {inp.name:30s} shape={shape}")

print("\n🧩 Outputs:")
for out in m.graph.output:
    shape = [d.dim_value for d in out.type.tensor_type.shape.dim]
    print(f"  - {out.name:30s} shape={shape}")
