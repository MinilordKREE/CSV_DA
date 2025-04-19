"""
Public façade (`try_run`) that auto‑selects Docker or Local backend.
"""
from __future__ import annotations
import shutil, importlib.util, importlib
import sys

# --- Try Docker first --------------------------------------------------------
try:
    import docker                         # noqa: F401
    from . import docker_runner as _backend
    _backend.client.ping()                # type: ignore[attr-defined]
    _USING_DOCKER = True
except Exception:
    from . import local_runner as _backend
    _USING_DOCKER = False

# Banner (prints once per interpreter session)
print(
    "🐳  Using **Docker** sandbox (image csv_da_sandbox)."
    if _USING_DOCKER
    else "⚠️  Docker not available → using **LOCAL** sandbox (limited isolation)."
)

# -------- Re‑export the stable interface -------------------------------------
run_in_sandbox = _backend.run_in_sandbox          # type: ignore[attr-defined]
try_run        = _backend.try_run                 # type: ignore[attr-defined]

__all__ = ["run_in_sandbox", "try_run"]
