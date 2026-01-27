import re
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extracts and parses a JSON object from a given text string.
    Handles markdown code blocks (```json ... ```) and raw JSON strings.
    
    Args:
        text (str): The text containing the JSON.
        
    Returns:
        Optional[Dict[str, Any]]: The parsed JSON object, or None if parsing fails.
    """
    if not text:
        return None

    text = text.strip()
    
    # 1. Try to find JSON within markdown code blocks
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # 2. Try to find the first '{' and last '}'
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = text[start_idx : end_idx + 1]
        else:
            # 3. Fallback: Assume the whole text might be JSON
            json_str = text

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON: {e}. Text: {text[:100]}...")
        # 4. Advanced: Try to repair common issue (trailing commas, etc.) - future work
        return None
