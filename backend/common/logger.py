import logging
import sys
import json
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from contextlib import contextmanager
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """
    Custom JSON Formatter for structured logging.
    """
    def format(self, record):
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        # Add extra fields (like task_id if passed via extra={})
        if hasattr(record, "task_id"):
            log_record["task_id"] = record.task_id
            
        return json.dumps(log_record)

# [NEW] 일반 스크립트용 로거 추가
def get_logger(name: str = "ADEASY") -> logging.Logger:
    """
    일반적인 콘솔 출력용 로거를 생성하여 반환합니다.
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        sh = logging.StreamHandler(sys.stdout)
        # Use JSON Formatter for consistency or standard for local dev?
        # Let's use standard for local dev readability, JSON for TaskLogger (production-like)
        # Or checking env var? For now, stick to readable for generic, JSON for TaskLogger.
        formatter = logging.Formatter(
            '[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        sh.setFormatter(formatter)
        logger.addHandler(sh)
        
    return logger


@dataclass
class TaskLogger:
    task_id: str
    log_file: Path
    level: int = logging.INFO

    def __post_init__(self) -> None:
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        name = f"adway.task.{self.task_id}"
        self._logger = logging.getLogger(name)
        self._logger.setLevel(self.level)
        self._logger.propagate = False

        # 중복 핸들러 방지
        if not self._logger.handlers:
            # Use JSON Formatter for Task Logs
            json_fmt = JSONFormatter()

            # File Handler (JSON)
            fh = logging.FileHandler(self.log_file, encoding="utf-8")
            fh.setFormatter(json_fmt)
            fh.setLevel(self.level)

            # Stream Handler (JSON for aggregation, or Text for readability?)
            # Usually aggregating stdout is better in JSON.
            # But for local debugging, text is nicer.
            # Let's make StreamHandler use Text for readable CLI, File for JSON.
            # Wait, "Centralized JSON Logging" implies we want stdout to be JSON for agents/Docker.
            # Let's start with File=JSON (machine readable), Stream=Text (human readable).
            # If user wants full centralized log aggregation from stdout, we'd enable JSON there too.
            # Given the requirement "Centralized JSON logging", I'll enable it for File.
            
            text_fmt = logging.Formatter(
                "[%(asctime)s] %(levelname)s %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

            sh = logging.StreamHandler()
            sh.setFormatter(text_fmt) # Keep human readable for dev console
            sh.setLevel(self.level)

            self._logger.addHandler(fh)
            self._logger.addHandler(sh)

    def _log(self, level, msg, **kwargs):
        # Inject task_id into extra for JSONFormatter (if we used it on stream)
        # For now, just logging.
        extra = kwargs.get("extra", {})
        extra["task_id"] = self.task_id
        kwargs["extra"] = extra
        self._logger.log(level, msg, **kwargs)

    def info(self, msg: str) -> None:
        self._log(logging.INFO, msg)

    def warning(self, msg: str) -> None:
        self._log(logging.WARNING, msg)

    def error(self, msg: str) -> None:
        self._log(logging.ERROR, msg)
        
    def debug(self, msg: str) -> None:
        self._log(logging.DEBUG, msg)

    def step(self, step_no: int, title: str, msg: str = "") -> None:
        base = f"Step {step_no}: {title}"
        self.info(f"{base} {('- ' + msg) if msg else ''}".rstrip())

    @contextmanager
    def time_block(self, label: str):
        t0 = perf_counter()
        self.info(f"⏱️  START: {label}")
        try:
            yield
        except Exception as e:
            self.error(f"❌ FAIL: {label} ({type(e).__name__}: {e})")
            raise
        finally:
            dt = perf_counter() - t0
            self.info(f"✅ END: {label} ({dt:.2f}s)")