from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from contextlib import contextmanager

# [NEW] 일반 스크립트용 로거 추가 (test_step0_agentic.py 등에서 사용)
def get_logger(name: str = "ADEASY") -> logging.Logger:
    """
    일반적인 콘솔 출력용 로거를 생성하여 반환합니다.
    (Task ID 없이 일반 스크립트나 모듈에서 사용)
    """
    logger = logging.getLogger(name)
    
    # 중복 핸들러 방지
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        # 콘솔 핸들러 (표준 출력)
        sh = logging.StreamHandler(sys.stdout)
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

        # 중복 핸들러 방지 (Celery 재시작/재임포트 대비)
        if not self._logger.handlers:
            fmt = logging.Formatter(
                "[%(asctime)s] %(levelname)s %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

            fh = logging.FileHandler(self.log_file, encoding="utf-8")
            fh.setFormatter(fmt)
            fh.setLevel(self.level)

            sh = logging.StreamHandler()
            sh.setFormatter(fmt)
            sh.setLevel(self.level)

            self._logger.addHandler(fh)
            self._logger.addHandler(sh)

    def info(self, msg: str) -> None:
        self._logger.info(msg)

    def warning(self, msg: str) -> None:
        self._logger.warning(msg)

    def error(self, msg: str) -> None:
        self._logger.error(msg)
        
    def debug(self, msg: str) -> None:
        self._logger.debug(msg)

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