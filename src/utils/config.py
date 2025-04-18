import os
from pathlib import Path

# -------- runtime flags --------
MODEL_BACKEND = os.getenv("CSV_DA_MODEL", "openai")
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_HF_MODEL     = "Qwen/Qwen1.5-7B-Chat"
MAX_LLM_TOKENS       = 2048
TEMPERATURE          = 0

# -------- paths --------
ROOT   = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"

# -------- secrets / keys --------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
HF_ACCESS_TOKEN = os.getenv("HF_ACCESS_TOKEN", "")
