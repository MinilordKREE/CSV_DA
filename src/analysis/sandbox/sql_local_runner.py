"""
Execute a read-only SQL query against the per-session sqlite DB
"""
from __future__ import annotations
import sqlite3, json, traceback, tempfile, shutil
from pathlib import Path
from typing import Dict, Any

def _run_query(db_path: str, query: str, timeout_steps: int = 100_000):
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)

    # Abort long‑running queries
    con.set_progress_handler(lambda: 1/0, timeout_steps)
    try:
        cur = con.cursor()
        cur.execute(query)
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return "", rows, ""
    except Exception as e:
        return "", [], traceback.format_exc()
    finally:
        con.close()


def try_run_sql(sql: str, db_path: str):
    stdout, rows, err = _run_query(db_path, sql)
    return stdout, rows, [], err  # plots list left empty
