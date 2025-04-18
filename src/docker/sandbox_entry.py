"""
Run LLM‑generated code in a throw‑away namespace.

Expected env vars:
- USER_CODE : path to a .py file containing the code to exec
- CSV_PATH  : path to CSV (mounted read‑only)
Outputs:
- /workspace/out/result.json  (containing 'stdout', 'error', 'return_obj', 'plots')
"""
import json, io, contextlib, importlib.util, traceback, os, sys, types, uuid, inspect
from pathlib import Path

SAFE_BUILTINS = {
    "range": range, "len": len, "sum": sum, "min": min, "max": max,
    "abs":  abs,  "print": print, "int": int, "float": float, "str": str, 
    "list": list, "dict": dict, "tuple": tuple, "set": set,
    "enumerate": enumerate, "zip": zip, "map": map, "filter": filter,
    "sorted": sorted, "reversed": reversed,
    "any": any, "all": all, "sum": sum, "round": round,
    "open": open, "os": os, "sys": sys, "uuid": uuid,
    "inspect": inspect, "types": types, "Path": Path,
    "importlib": importlib, "json": json, "contextlib": contextlib,
    "io": io, "traceback": traceback,
    "pd": None, 
    "plt": None, 
    "np": None, 
}

def run_user(code_text: str, local_ctx: dict):
    g = {"__builtins__": SAFE_BUILTINS, **local_ctx}
    out_buf = io.StringIO()
    err = ""
    try:
        with contextlib.redirect_stdout(out_buf):
            exec(code_text, g, {})
    except Exception:
        err = traceback.format_exc()
    return out_buf.getvalue(), err, g.get("output_data")

def main():
    code_path = Path(os.environ["USER_CODE"])
    csv_path  = Path(os.environ["CSV_PATH"])
    out_dir   = Path("/workspace/out")
    out_dir.mkdir(exist_ok=True)

    import pandas as pd
    df = pd.read_csv(csv_path)

    code_text = code_path.read_text()
    try:
        stdout, error, ret_obj = run_user(code_text, {"df": df})
    except Exception:
        stdout, ret_obj = "", None
        error = traceback.format_exc()
    finally:
        plot_files = [str(p) for p in Path(".").glob("*.png")]
        result = dict(stdout=stdout, error=error,
                      return_obj=ret_obj, plots=plot_files)
        (out_dir / "result.json").write_text(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
