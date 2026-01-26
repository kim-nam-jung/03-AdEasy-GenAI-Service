
import torch
from diffusers import DiffusionPipeline
import os

model_id = "Lightricks/LTX-Video"
print(f"Loading {model_id}...")

try:
    # Use float16 which is standard for these GPUs (T4/L4)
    pipe = DiffusionPipeline.from_pretrained(
        model_id, 
        torch_dtype=torch.float16, 
        trust_remote_code=True
    )
    print("SUCCESS: Model loaded!")
except Exception as e:
    print(f"FAILURE: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
