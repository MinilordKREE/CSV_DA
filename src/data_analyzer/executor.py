from ..utils.sandbox_runner import run_in_sandbox

def try_run(code: str, csv_path: str):
    try:
        r = run_in_sandbox(code, csv_path)
        error = r["error"]
        stdout = r["stdout"]
        ret    = r["return_obj"]
        plots  = r["plots"]
        return (stdout, ret, plots, error)
    except Exception as e:
        return ("", None, [], str(e))
