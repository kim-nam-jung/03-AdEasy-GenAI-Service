
import traceback
import sys
import os

try:
    print("Python version:", sys.version)
    print("HF_HOME:", os.environ.get("HF_HOME", "Not Set"))
    
    from transformers import AutoTokenizer
    print("Attempting to load tokenizer for Lightricks/LTX-Video...")
    
    tokenizer = AutoTokenizer.from_pretrained(
        "Lightricks/LTX-Video",
        trust_remote_code=True
    )
    print("SUCCESS: Tokenizer loaded!")
except Exception as e:
    print(f"FAILURE: {type(e).__name__}: {e}")
    traceback.print_exc()
    sys.exit(1)
