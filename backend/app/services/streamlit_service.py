"""Streamlit container service — runs generated app.py in Docker with Streamlit."""

import logging
import socket
import time

import docker
from docker.errors import DockerException, ImageNotFound

from app.config import settings

logger = logging.getLogger(__name__)

RUNNER_IMAGE = "frankenstein-runner"


class StreamlitService:
    """Manages Streamlit containers for live app preview."""

    PORT_RANGE = (8501, 8600)

    def __init__(self):
        self._containers: dict[str, dict] = {}  # session_id -> {container, port, started_at}
        self._used_ports: set[int] = set()
        self._client = None
        self._available = False
        self._connect()

    def _connect(self):
        try:
            self._client = docker.from_env()
            self._available = True
        except DockerException as e:
            self._available = False
            logger.warning("Docker not available for Streamlit: %s", e)

    @property
    def available(self) -> bool:
        if not self._available:
            self._connect()
        return self._available

    def _allocate_port(self) -> int:
        for port in range(self.PORT_RANGE[0], self.PORT_RANGE[1]):
            if port in self._used_ports:
                continue
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(("", port))
                    self._used_ports.add(port)
                    return port
                except OSError:
                    continue
        raise RuntimeError("No available ports in range %s-%s" % self.PORT_RANGE)

    def start(self, session_id: str, session_dir, env: dict[str, str] | None = None) -> dict:
        """Start a Streamlit container for a session. Returns {url, port, container_id}."""
        if not self._available:
            raise RuntimeError("Docker not available")

        # Stop existing container for this session
        if session_id in self._containers:
            self.stop(session_id)

        port = self._allocate_port()
        container_env = {
            "PYTHONUNBUFFERED": "1",
            "OPENAI_API_KEY": settings.openrouter_api_key,
            "OPENROUTER_API_KEY": settings.openrouter_api_key,
            "OPENAI_BASE_URL": "https://openrouter.ai/api/v1",
            "OPENAI_MODEL_NAME": settings.tester_test_model,
            **(env or {}),
        }

        cmd = (
            "pip install -q -r requirements.txt 2>/dev/null; "
            "streamlit run app.py "
            "--server.port=8501 "
            "--server.headless=true "
            "--server.address=0.0.0.0 "
            "--server.enableCORS=false "
            "--server.enableXsrfProtection=false"
        )

        container = self._client.containers.run(
            image=RUNNER_IMAGE,
            command=["sh", "-c", cmd],
            volumes={str(session_dir): {"bind": "/agent", "mode": "ro"}},
            working_dir="/agent",
            environment=container_env,
            detach=True,
            mem_limit="512m",
            ports={"8501/tcp": port},
            network_disabled=False,
        )

        self._containers[session_id] = {
            "container": container,
            "port": port,
            "started_at": time.time(),
        }

        url = f"http://localhost:{port}"
        logger.info("[%s] Streamlit started on port %d (container %s)", session_id, port, container.short_id)
        return {"url": url, "port": port, "container_id": container.id}

    def stop(self, session_id: str) -> None:
        """Stop and remove a session's Streamlit container."""
        info = self._containers.pop(session_id, None)
        if not info:
            return
        self._used_ports.discard(info["port"])
        try:
            info["container"].stop(timeout=5)
            info["container"].remove(force=True)
        except Exception as e:
            logger.warning("[%s] Streamlit container cleanup error: %s", session_id, e)

    def is_running(self, session_id: str) -> bool:
        info = self._containers.get(session_id)
        if not info:
            return False
        try:
            info["container"].reload()
            return info["container"].status == "running"
        except Exception:
            self._containers.pop(session_id, None)
            self._used_ports.discard(info["port"])
            return False

    def get_url(self, session_id: str) -> str | None:
        info = self._containers.get(session_id)
        if info:
            return f"http://localhost:{info['port']}"
        return None

    def cleanup_expired(self, max_age: int = 1800) -> None:
        """Stop containers older than max_age seconds."""
        now = time.time()
        expired = [
            sid for sid, info in self._containers.items()
            if now - info["started_at"] > max_age
        ]
        for sid in expired:
            logger.info("[%s] Cleaning up expired Streamlit container", sid)
            self.stop(sid)
