from ..utils import sandbox

def try_run(code: str, df):
    """Return (output, error_msg). df is injected in sandbox."""
    ctx = {"df": df}
    return sandbox.run(code, ctx)
