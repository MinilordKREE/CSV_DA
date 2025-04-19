"""
auto-selects Docker or Local backend.
"""
from __future__ import annotations
import shutil, importlib.util, importlib
import sys, os 

# Check if user wants to force local execution
# Check if Docker is available 
if os.getenv("CSV_DA_FORCE_LOCAL"): 
    from . import local_runner as _backend
    _USING_DOCKER = False
else:
    try:
        import docker                 
        from . import docker_runner as _backend
        _backend.client.ping()           
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


run_in_sandbox = _backend.run_in_sandbox         
try_run        = _backend.try_run                

__all__ = ["run_in_sandbox", "try_run"]
