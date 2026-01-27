import base64
import logging

logger = logging.getLogger(__name__)

def encode_image(image_path: str) -> str:
    """
    Encode image to base64 string.
    If image has transparency (RGBA), composite it over a high-contrast background (MAGENTA)
    to help GPT-4 Vision identify missing parts or artifacts.
    """
    try:
        from PIL import Image
        import io
        
        with Image.open(image_path) as img:
            # Resize if too large to save tokens/time (optional, max 1024px)
            img.thumbnail((1024, 1024))
            
            # If RGBA, put a high-contrast background
            if img.mode == 'RGBA':
                # Use Magenta (Green might be in food like lettuce, Magenta is rare in food)
                background = Image.new('RGB', img.size, (255, 0, 255)) 
                background.paste(img, mask=img.split()[3]) # Use alpha channel as mask
                img = background
            
            # Convert to RGB if not already (e.g. grayscale)
            if img.mode != 'RGB':
                img = img.convert('RGB')
                
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=85)
            return base64.b64encode(buffered.getvalue()).decode('utf-8')
            
    except Exception as e:
        logger.error(f"Failed to process image {image_path}: {e}")
        # Fallback to simple read
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
