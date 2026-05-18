"""Docker execution service for running generated agents in sandboxed containers.

Uses the Docker SDK to:
  1. Write CodeBundle files to a temp directory
  2. Mount into frankenstein-runner container
  3. Run with timeout, capture stdout/stderr
  4. Return structured execution results
"""

import logging
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import docker
from docker.errors import ContainerError, DockerException, ImageNotFound

from app.config import settings
from app.models.code import CodeBundle

logger = logging.getLogger(__name__)

RUNNER_IMAGE = "frankenstein-runner"


@dataclass
class ExecutionResult:
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    error: str = ""


class DockerService:
    """Manages frankenstein-runner containers for generated agent execution."""

    def __init__(self, timeout: int | None = None):
        self._timeout = timeout or settings.docker_timeout
        self._client = None
        self._available = False
        self._connect()

    def _connect(self):
        try:
            self._client = docker.from_env()
            self._available = True
            logger.info("Docker client connected")
        except DockerException as e:
            self._available = False
            logger.warning("Docker not available: %s", e)

    @property
    def available(self) -> bool:
        if not self._available:
            self._connect()
        return self._available

    def run_code_bundle(
        self,
        code: CodeBundle,
        timeout: int | None = None,
        env: dict[str, str] | None = None,
        network_disabled: bool = True,
    ) -> ExecutionResult:
        """Write code files to temp dir, mount into container, run, capture output."""
        if not self._available:
            return ExecutionResult(
                exit_code=-1,
                error="Docker not available on this host",
            )

        timeout = timeout or self._timeout
        tmp_dir = None

        try:
            # Write code files to temp directory
            tmp_dir = Path(tempfile.mkdtemp(prefix="frankenstein_agent_"))
            for fname, content in code.files.items():
                fpath = tmp_dir / fname
                fpath.parent.mkdir(parents=True, exist_ok=True)
                fpath.write_text(content)

            # Write requirements.txt if not already in files
            if "requirements.txt" not in code.files and code.dependencies:
                (tmp_dir / "requirements.txt").write_text(
                    "\n".join(code.dependencies) + "\n"
                )

            return self._execute_container(tmp_dir, code.entry_point, timeout, env, network_disabled)

        except ImageNotFound:
            logger.error("Runner image '%s' not found — build it first", RUNNER_IMAGE)
            return ExecutionResult(
                exit_code=-1,
                error=f"Image '{RUNNER_IMAGE}' not found. Run: docker build -t {RUNNER_IMAGE} runner/",
            )
        except DockerException as e:
            logger.error("Docker execution failed: %s", e)
            return ExecutionResult(exit_code=-1, error=str(e))
        finally:
            if tmp_dir and tmp_dir.exists():
                shutil.rmtree(tmp_dir, ignore_errors=True)

    def _execute_container(
        self,
        agent_dir: Path,
        entry_point: str,
        timeout: int,
        env: dict[str, str] | None,
        network_disabled: bool = True,
    ) -> ExecutionResult:
        """Run a container with agent code mounted at /agent."""
        agent_dir = agent_dir.resolve()
        container = None
        try:
            # Install extra deps if requirements.txt exists in the agent
            req_file = agent_dir / "requirements.txt"
            cmd = f"pip install -q -r requirements.txt 2>/dev/null; python {entry_point}"
            if not req_file.exists():
                cmd = f"python {entry_point}"

            container = self._client.containers.run(
                image=RUNNER_IMAGE,
                command=["sh", "-c", cmd],
                volumes={str(agent_dir): {"bind": "/agent", "mode": "rw"}},
                working_dir="/agent",
                environment=env or {},
                detach=True,
                mem_limit="512m",
                network_disabled=network_disabled,
            )

            # Wait with timeout
            result = container.wait(timeout=timeout)
            exit_code = result.get("StatusCode", -1)

            stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
            stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")

            return ExecutionResult(
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
            )

        except Exception as e:
            error_str = str(e)
            timed_out = "timed out" in error_str.lower() or "read timeout" in error_str.lower()

            # Capture whatever logs we can
            stdout = ""
            stderr = ""
            if container:
                try:
                    stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
                    stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")
                except Exception:
                    pass

            if timed_out:
                logger.warning("Container timed out after %ds", timeout)
                return ExecutionResult(
                    exit_code=-1,
                    stdout=stdout,
                    stderr=stderr,
                    timed_out=True,
                    error=f"Execution timed out after {timeout}s",
                )

            logger.error("Container execution error: %s", e)
            return ExecutionResult(
                exit_code=-1,
                stdout=stdout,
                stderr=stderr,
                error=error_str,
            )
        finally:
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass

    def image_exists(self) -> bool:
        """Check if the frankenstein-runner image is built."""
        if not self._available:
            return False
        try:
            self._client.images.get(RUNNER_IMAGE)
            return True
        except ImageNotFound:
            return False
