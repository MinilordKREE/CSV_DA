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

# Default directories and logging setup
ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_LOG_DIR = ROOT_DIR / "log"


def make_logger(
    name: str = "cvs_da",
    log_dir: Path = DEFAULT_LOG_DIR,
    level: int = logging.INFO,
    name_suffix: str | None = None
) -> logging.Logger:
    """
    Create a rotating file logger. Each logger has a unique name and
    logs to a file in the specified directory.
    """
    if name_suffix:
        name = f"{name}_{name_suffix}"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{name}.log"

    logger = logging.getLogger(name)
    if logger.handlers:
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


class JSONHistory:
    """
    Each row = {
        "question": str,
        "code": str,
        "stdout": str,
        "output": str,      # preview of the result of the code
        "explain": str
    }
    A persistent store for question, code, and response data.
    Data is stored as JSON, with each entry containing question, code,
    output preview, and explanation fields.
    """

    def __init__(self, file_path: Path):
        self.path = file_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._save([])

    def _load(self) -> List[Dict]:
        """
        Load all rows from the history file, resetting it if corrupted.
        """
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(f"History file corrupted, resetting. {e}")
            self._save([])
            return []

    def _save(self, rows: List[Dict]):
        """
        Save all rows back to the history file.
        """
        self.path.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    @property
    def rows(self) -> List[Dict]:
        return self._load()

    def tail(self, n: int) -> List[Dict]:
        """
        Retrieve the last 'n' rows of history.
        """
        return self.rows[-n:]

    def append(self, row: Dict):
        """
        Add a new row to the history file.
        """
        data = self._load()
        data.append(row)
        self._save(data)
        logger.info(f"History appended (total {len(data)} rows).")

    def clear(self):
        """
        Clear all entries from the history file.
        """
        self._save([])
        logger.info("History cleared.")


    def log_prompt(self, prompt: str):
        """
        Log the prompt text for debugging purposes.
        """
        logger.debug(f"\n---- PROMPT ---------------------------------\n{prompt}\n")

    def log_response(self, response: str):
        """
        Log the response text for debugging purposes.
        """
        logger.debug(f"\n---- RESPONSE -------------------------------\n{response}\n")
