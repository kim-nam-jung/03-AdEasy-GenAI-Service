try:
    from app.core.config import Config, settings
except ImportError:
    import sys
    from pathlib import Path
    # Add backend root to sys.path
    root_dir = str(Path(__file__).resolve().parents[1])
    if root_dir not in sys.path:
        sys.path.append(root_dir)
    from app.core.config import Config, settings
