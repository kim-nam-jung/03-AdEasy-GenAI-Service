import functools
import logging
from common.redis_manager import RedisManager

logger = logging.getLogger(__name__)

def use_supervisor_config(func):
    """
    Decorator that checks Redis for any configuration overrides set by the Supervisor (Reflection Tool)
    and injects them into the tool's kwargs.
    
    Target config keys: "task:{task_id}:config" (Hash)
    Strategy: 
      1. Fetch all overrides from Redis.
      2. Filter keys that match the tool's domain (e.g., "segmentation:*").
      3. Update kwargs with overridden values.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        task_id = kwargs.get("task_id")
        # Try to find task_id in args if not in kwargs (though tools usually use kwargs)
        if not task_id and len(args) > 0:
            # Assuming task_id is the first argument for all tools
            task_id = args[0]
            
        if task_id:
            try:
                redis_mgr = RedisManager.from_env()
                config_key = f"task:{task_id}:config"
                overrides = redis_mgr.client.hgetall(config_key)
                
                if overrides:
                    # heuristic to determine tool category from function name (e.g. segmentation_tool -> segmentation)
                    tool_name = func.__name__.replace("_tool", "") 
                    
                    category_overrides = {}
                    for key, value in overrides.items():
                        # key format: "category:param_name" (e.g. "segmentation:prompt_mode")
                        if ":" in key:
                            category, param = key.split(":", 1)
                            if category == tool_name:
                                category_overrides[param] = value

                    if category_overrides:
                        logger.info(f"[{tool_name}] Applying Supervisor Overrides: {category_overrides}")
                        
                        # Apply overrides to kwargs
                        for param, value in category_overrides.items():
                            # Type casting logic
                            # We try to infer type from default values in function signature, but that requires inspection
                            # For now, simplistic casting based on value format or existing kwarg type
                            
                            original_val = kwargs.get(param)
                            
                            if original_val is not None:
                                if isinstance(original_val, int):
                                    kwargs[param] = int(value)
                                elif isinstance(original_val, bool):
                                    kwargs[param] = str(value).lower() in ("true", "1", "yes")
                                else:
                                    kwargs[param] = value
                            else:
                                # New param, try to cast intelligent
                                if value.isdigit():
                                    kwargs[param] = int(value)
                                elif value.lower() in ("true", "false"):
                                    kwargs[param] = value.lower() == "true"
                                else:
                                    kwargs[param] = value
                                    
                            logger.info(f"  -> Override Applied: {param} = {kwargs[param]}")

            except Exception as e:
                logger.warning(f"Failed to apply supervisor config: {e}")
                
        return func(*args, **kwargs)
    return wrapper
