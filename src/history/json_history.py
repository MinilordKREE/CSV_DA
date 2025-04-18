"""
JSONHistory:  persistent (question, code, result, explanation) store.
LogHelper:    central rotating logger for prompts & model outputs.
"""
import json
import logging
import logging.handlers  
from datetime import datetime, timezone   
from pathlib import Path
from typing import List, Dict

def _now_tag():
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

# ---------- Logging helper ----------
ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_LOG_DIR = ROOT_DIR / "log"
def make_logger(name: str = "cvs_da",
                log_dir: Path = DEFAULT_LOG_DIR,
                level: int = logging.INFO,
                name_suffix: str | None = None) -> logging.Logger:
    if name_suffix:
        name = f"{name}_{name_suffix}"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{name}.log"

    logger = logging.getLogger(name)
    if logger.handlers:          # already configured
        return logger

    logger.setLevel(level)
    fh = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=5_000_000, backupCount=5, encoding="utf-8"
    )
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.propagate = False
    return logger


logger = make_logger(level=logging.DEBUG)   # DEBUG captures .debug()


# ---------- JSON persistent history ----------
class JSONHistory:
    """
    Each row = {
        "question": str,
        "code": str,
        "stdout": str,
        "output": str,      # preview of output_data
        "explain": str
    }
    Stored as a list in src/history/chat_history/hist_<hash>.json
    """

    def __init__(self, file_path: Path):
        self.path = file_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._save([])

    # ---- internal I/O ----
    def _load(self) -> List[Dict]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(f"History file corrupted, resetting. {e}")
            self._save([])
            return []

    def _save(self, rows: List[Dict]):
        self.path.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # ---- public API ----
    @property
    def rows(self) -> List[Dict]:
        return self._load()

    def tail(self, n: int) -> List[Dict]:
        return self.rows[-n:]

    def append(self, row: Dict):
        data = self._load()
        data.append(row)
        self._save(data)
        logger.info(f"History appended (total {len(data)} rows).")

    def clear(self):
        self._save([])
        logger.info("History cleared.")

    # ---- convenience loggers for prompts / responses ----
    def log_prompt(self, prompt: str):
        logger.debug(f"\n---- PROMPT ---------------------------------\n{prompt}\n")

    def log_response(self, response: str):
        logger.debug(f"\n---- RESPONSE -------------------------------\n{response}\n")
