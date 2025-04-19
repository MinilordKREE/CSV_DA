"""
Light-weight fallback when Docker is unavailable.
!!!! Not a hard security boundary - use with trusted code only.
"""
from __future__ import annotations
import json, io, contextlib, traceback, tempfile, shutil, sys, os, signal, resource, subprocess, builtins
from pathlib import Path
from typing import Dict, Any

SAFE_BUILTINS = {
    "abs": abs, "min": min, "max": max, "sum": sum,
    "range": range, "len": len, "print": print,
    "int": int, "float": float, "str": str,
    "list": list, "dict": dict, "tuple": tuple, "set": set,
    "enumerate": enumerate, "zip": zip, "sorted": sorted, "reversed": reversed,
    "any": any, "all": all, "round": round,
    "__import__": __import__, 
}

def _set_limits(mem_bytes: int, cpu_seconds: int):
    def _inner():
        resource.setrlimit(resource.RLIMIT_AS,  (mem_bytes, mem_bytes))
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
        signal.signal(signal.SIGALRM, lambda *_: sys.exit(1))
        signal.alarm(cpu_seconds + 1)
    return _inner


def run_in_sandbox(code: str, csv_path: str,
                   mem_limit: str = "2g", timeout: int = 120) -> Dict[str, Any]:
    """Execute snippet in a temp dir using the host Python interpreter."""
    tmp = Path(tempfile.mkdtemp(prefix="csv_da_"))
    try:
        # prepare session files
        code_file = tmp / "snippet.py"; code_file.write_text(code)
        csv_copy  = tmp / "data.csv";   shutil.copy2(csv_path, csv_copy)
        out_dir   = tmp / "out";        out_dir.mkdir()

        # driver script (runs inside the same interpreter via -c)
        driver = f"""
import json, io, contextlib, traceback, os, builtins
from pathlib import Path
import pandas as pd

SAFE = {list(SAFE_BUILTINS.keys())}
g = {{'__builtins__': {{k: getattr(builtins, k) for k in SAFE}}}}
g['df'] = pd.read_csv(os.environ['CSV_PATH'])

code = Path(os.environ['USER_CODE']).read_text()
buf  = io.StringIO(); err = ''
try:
    with contextlib.redirect_stdout(buf):
        exec(code, g)
except Exception:
    err = traceback.format_exc()

plots = [str(p) for p in Path('.').glob('*.png')]
res   = dict(stdout=buf.getvalue(), error=err,
             return_obj=g.get('output_data'), plots=plots)
Path(os.environ['OUT_DIR']).write_text(json.dumps(res, ensure_ascii=False))
"""
        mem_bytes = int(float(mem_limit.rstrip("g")) * (1024**3))
        proc = subprocess.run(
            [sys.executable, "-c", driver],
            cwd=tmp,
            env={**os.environ,
                 "USER_CODE": str(code_file),
                 "CSV_PATH":  str(csv_copy),
                 "OUT_DIR":   str(out_dir/"result.json")},
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=timeout + 2,
            text=True,
            preexec_fn=_set_limits(mem_bytes, timeout),
        )

        result_path = out_dir / "result.json"
        if not result_path.exists():
            raise RuntimeError(
                f"Local runner failed (exit {proc.returncode}).\n"
                f"stdout:\n{proc.stdout}\n\nstderr:\n{proc.stderr}"
            )
        res = json.loads(result_path.read_text())
        res["container_logs"] = proc.stderr
        res["plots"] = [str(out_dir / Path(p).name) for p in res.get("plots", [])]
        return res
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def try_run(code: str, csv_path: str):
    try:
        r = run_in_sandbox(code, csv_path)
        return r["stdout"], r["return_obj"], r["plots"], r["error"]
    except Exception as exc:
        return "", None, [], str(exc)
