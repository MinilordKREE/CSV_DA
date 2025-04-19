"""
Host helper mirroring docker_runner.py but for SQL strings.
"""
import json, shutil, tempfile
from pathlib import Path
import docker, uuid

client = docker.from_env()
EXPORT_PLOTS_DIR = Path("exports/plots")   # unlikely for SQL mode but kept

def run_in_sandbox(sql: str, db_path: str,
                   mem_limit="512m", timeout=60) -> dict:
    tmp = Path(tempfile.mkdtemp(prefix="csv_da_sql_"))
    try:
        sql_file = tmp / "query.sql"; sql_file.write_text(sql)
        db_copy  = tmp / "data.db";   shutil.copy2(db_path, db_copy)
        out_dir  = tmp / "out"
        out_dir.mkdir()
        # Make the directory writeable by the unprivileged `sandbox`
        out_dir.chmod(0o777)

        SESSION = "/workspace/session"
        container = client.containers.run(
            image="csv_da_sandbox",
            user="sandbox",
            working_dir="/workspace",
            entrypoint=["python", "sql_driver.py"],
            environment={
                "USER_SQL": f"{SESSION}/query.sql",
            },
            volumes={
                tmp.as_posix(): {"bind": SESSION, "mode": "rw"},
                out_dir.as_posix(): {"bind": "/workspace/out", "mode": "rw"},
            },
            network_mode="none",
            mem_limit=mem_limit,
            detach=True,
            stdout=True, stderr=True, remove=False,
        )
        exit_res = container.wait(timeout=timeout)
        logs = container.logs(stdout=True, stderr=True).decode()

        result_path = out_dir / "result.json"
        if not result_path.exists():        # robustness / better diagnostics
            raise RuntimeError(
                "Sandbox exited without creating result.json.\n"
                f"Container logs:\n{logs}"
            )
        result = json.loads(result_path.read_text())
        result["container_logs"] = logs
        return result
    finally:
        try: container.remove(force=True)  # type: ignore
        except Exception: pass
        shutil.rmtree(tmp, ignore_errors=True)

def try_run_sql(sql: str, db_path: str):
    r = run_in_sandbox(sql, db_path)
    return r["stdout"], r["return_obj"], [], r["error"]
