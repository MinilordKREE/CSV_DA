import json
import shutil
import tempfile
from pathlib import Path
import docker

client = docker.from_env()


def run_in_sandbox(
    code: str, 
    csv_path: str, 
    mem_limit: str = "2g", 
    timeout: int = 120
) -> dict:
    """
    Run the given code in a sandbox container and retrieve the result.
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix="csv_da_"))
    try:
        # Create temporary files and directories
        code_file = tmp_dir / "snippet.py"
        code_file.write_text(code)

        csv_copy = tmp_dir / "data.csv"
        shutil.copy2(csv_path, csv_copy)

        out_dir = tmp_dir / "out"
        out_dir.mkdir()

        # Container file paths
        SESSION_DIR = "/workspace/session"
        USER_CODE   = f"{SESSION_DIR}/snippet.py"
        CSV_IN_BOX  = f"{SESSION_DIR}/data.csv"
        RESULT_JSON = f"{SESSION_DIR}/out/result.json"

        # Start the container
        container = client.containers.run(
            image="csv_da_sandbox",
            user="sandbox",
            working_dir="/workspace",
            environment={
                "USER_CODE": USER_CODE,
                "CSV_PATH":  CSV_IN_BOX,
            },
            volumes={
                tmp_dir.as_posix():     {"bind": SESSION_DIR,   "mode": "rw"},
                out_dir.as_posix():     {"bind": "/workspace/out", "mode": "rw"},
            },
            network_mode="none",
            mem_limit=mem_limit,
            nano_cpus=1_000_000_000,
            detach=True,
            stdout=True,
            stderr=True,
            remove=False,
        )

        # Wait for container completion
        try:
            exit_res = container.wait(timeout=timeout)
        except Exception:
            container.kill()
            raise RuntimeError(f"Sandbox timed out after {timeout} seconds")

        logs = container.logs(stdout=True, stderr=True).decode(errors="ignore")

        # Check and return the result
        result_json_path = out_dir / "result.json"
        if not result_json_path.exists():
            raise RuntimeError(
                f"Sandbox exited with code {exit_res.get('StatusCode')} "
                f"but did not create result.json.\nLogs:\n{logs}"
            )

        result = json.loads(result_json_path.read_text())
        result["container_logs"] = logs
        result["plots"] = [
            str(out_dir / Path(p).name) for p in result.get("plots", [])
        ]
        return result

    finally:
        # Clean up
        try:
            container.remove(force=True)
        except Exception:
            pass
        shutil.rmtree(tmp_dir, ignore_errors=True)

def try_run(code: str, csv_path: str):
    """
    Execute code in the sandbox and return stdout, returned object, plots, and errors.
    """
    try:
        r = run_in_sandbox(code, csv_path)
        return r["stdout"], r["return_obj"], r["plots"], r["error"]
    except Exception as e:
        return "", None, [], str(e)