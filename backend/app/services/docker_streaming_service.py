"""Streaming Docker execution service for live agent preview.

Runs generated agent code in a Docker container and streams stdout/stderr
line-by-line to an asyncio.Queue for real-time WebSocket delivery.
"""

import asyncio
import logging
import shutil
import tempfile
import time
from pathlib import Path

import docker
from docker.errors import DockerException, ImageNotFound

from app.config import settings

logger = logging.getLogger(__name__)

RUNNER_IMAGE = "frankenstein-runner"


class DockerStreamingService:
    """Streams container output line-by-line via asyncio.Queue."""

    def __init__(self, timeout: int | None = None):
        self._timeout = timeout or (settings.docker_timeout * 2)
        self._client = None
        self._available = False
        self._connect()

    def _connect(self):
        try:
            self._client = docker.from_env()
            self._available = True
        except DockerException as e:
            self._available = False
            logger.warning("Docker not available: %s", e)

    @property
    def available(self) -> bool:
        if not self._available:
            self._connect()
        return self._available

    def image_exists(self) -> bool:
        if not self._available:
            return False
        try:
            self._client.images.get(RUNNER_IMAGE)
            return True
        except ImageNotFound:
            return False

    async def run_streaming(
        self,
        session_dir: Path,
        entry_point: str,
        env: dict[str, str] | None = None,
        queue: asyncio.Queue | None = None,
        timeout: int | None = None,
    ) -> dict:
        """Run agent code in Docker, streaming lines to queue.

        Returns dict with exit_code, duration_ms, output (final combined output).
        Sends None sentinel to queue when done.
        """
        if not self._available:
            if queue:
                await queue.put(None)
            return {"exit_code": -1, "duration_ms": 0, "output": "", "error": "Docker not available"}

        timeout = timeout or self._timeout
        container_env = {"PYTHONUNBUFFERED": "1", **(env or {})}

        # Check for requirements.txt
        req_file = session_dir / "requirements.txt"
        cmd = f"pip install -q -r requirements.txt 2>/dev/null; python {entry_point}"
        if not req_file.exists():
            cmd = f"python {entry_point}"

        container = None
        start_time = time.monotonic()

        try:
            container = self._client.containers.run(
                image=RUNNER_IMAGE,
                command=["sh", "-c", cmd],
                volumes={str(session_dir): {"bind": "/agent", "mode": "rw"}},
                working_dir="/agent",
                environment=container_env,
                detach=True,
                mem_limit="512m",
                network_disabled=False,
            )

            container_id = container.id

            # Stream logs in a thread to avoid blocking event loop
            output_lines: list[str] = []

            def _stream_logs():
                try:
                    for chunk in container.logs(stream=True, follow=True, timestamps=False):
                        line = chunk.decode("utf-8", errors="replace")
                        output_lines.append(line)
                        if queue:
                            # Schedule put on the event loop
                            asyncio.run_coroutine_threadsafe(
                                queue.put(line), _loop
                            )
                except Exception as e:
                    logger.warning("Log streaming error: %s", e)

            _loop = asyncio.get_event_loop()

            # Run streaming in background thread with timeout
            stream_task = asyncio.get_event_loop().run_in_executor(None, _stream_logs)

            try:
                # Wait for container to finish with timeout
                result = await asyncio.wait_for(
                    asyncio.to_thread(container.wait, timeout=timeout),
                    timeout=timeout + 5,
                )
                exit_code = result.get("StatusCode", -1)
            except (asyncio.TimeoutError, Exception) as e:
                logger.warning("Container timeout or error: %s", e)
                exit_code = -1
                try:
                    container.stop(timeout=5)
                except Exception:
                    pass

            # Wait for stream thread to finish
            try:
                await asyncio.wait_for(stream_task, timeout=3)
            except (asyncio.TimeoutError, Exception):
                pass

            duration_ms = int((time.monotonic() - start_time) * 1000)
            combined_output = "".join(output_lines)

            return {
                "exit_code": exit_code,
                "duration_ms": duration_ms,
                "output": combined_output,
                "container_id": container_id,
            }

        except ImageNotFound:
            logger.error("Runner image '%s' not found", RUNNER_IMAGE)
            return {"exit_code": -1, "duration_ms": 0, "output": "", "error": f"Image '{RUNNER_IMAGE}' not found"}
        except DockerException as e:
            logger.error("Docker execution failed: %s", e)
            return {"exit_code": -1, "duration_ms": 0, "output": "", "error": str(e)}
        finally:
            if queue:
                await queue.put(None)  # Sentinel
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
