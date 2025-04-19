"""
Called inside the sandbox to run a SQL string against data.db
and emit result.json.
"""
import json, os, sqlite3, traceback
from pathlib import Path

def main():
    db_file   = Path("/workspace/session/data.db")
    sql_file  = Path(os.environ["USER_SQL"])
    out_file  = Path("/workspace/out/result.json")

    query = sql_file.read_text()

    con = sqlite3.connect(f"file:{db_file}?mode=ro", uri=True)
    con.set_progress_handler(lambda: 1/0, 100_000)
    err = ""
    try:
        cur  = con.cursor()
        cur.execute(query)
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    except Exception:
        rows = []
        err  = traceback.format_exc()
    finally:
        con.close()

    out_file.write_text(json.dumps(
        dict(stdout="", error=err, return_obj=rows, plots=[]),
        ensure_ascii=False))

if __name__ == "__main__":
    main()
