# src/utils/guard.py
import ast, textwrap, re

_BANNED = {"pd.read_csv", "pd.DataFrame(", "DataFrame(", "read_csv("}

def looks_suspicious(code: str) -> bool:
    lowered = code.lower()
    return any(p.lower() in lowered for p in _BANNED)
