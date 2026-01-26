import sys
import os
import logging
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

try:
    from pipeline.models.ltx2_pro_loader import LTX2ProLoader
except ImportError:
    # Handle case where run from root
    sys.path.append("/app")
    from pipeline.models.ltx2_pro_loader import LTX2ProLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify():
    logger.info("Starting LTX-Video Verification...")
    try:
        # Initialize loader
        # Use CPU for basic loading check if CUDA is not available/configured in build context
        # But we need to test if diffusers loads correctly, which usually requires CUDA for these models
        # However, for loading check, we can try. 
        # The real environment is CUDA.
        loader = LTX2ProLoader(device="cuda")
        
        # Load model
        logger.info("Attempting to load model...")
        loader.load()
        logger.info("SUCCESS: LTX-Video Model loaded successfully!")
        
    except Exception as e:
        logger.error(f"FAILURE: Verification Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    verify()
