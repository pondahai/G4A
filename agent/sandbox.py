import docker
import tempfile
import os
from pathlib import Path

class Sandbox:
    def __init__(self, image="python:3.10-slim"):
        self.image = image
        try:
            self.client = docker.from_env()
        except Exception as e:
            self.client = None
            print(f"Warning: Docker not available. Sandbox is disabled. Error: {e}")

    def execute_code(self, code: str, timeout: int = 10) -> dict:
        if not self.client:
            return {"success": False, "output": "Docker not available for sandbox execution."}

        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = Path(temp_dir) / "skill.py"
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)

            try:
                container = self.client.containers.run(
                    self.image,
                    command=f"python /sandbox/skill.py",
                    volumes={temp_dir: {'bind': '/sandbox', 'mode': 'ro'}},
                    working_dir="/sandbox",
                    mem_limit="128m",
                    cpu_period=100000,
                    cpu_quota=50000, # 50% CPU
                    network_disabled=True,
                    remove=True,
                    detach=False,
                    stdout=True,
                    stderr=True,
                    environment={"PYTHONUNBUFFERED": "1"}
                )
                output = container.decode('utf-8')
                return {"success": True, "output": output}
            except docker.errors.ContainerError as e:
                return {"success": False, "output": e.stderr.decode('utf-8') if e.stderr else str(e)}
            except Exception as e:
                return {"success": False, "output": str(e)}
