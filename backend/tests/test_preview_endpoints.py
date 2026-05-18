"""Tests for preview REST + WebSocket endpoints."""

import pytest
from unittest.mock import patch, PropertyMock
from fastapi.testclient import TestClient

from app.main import app, docker_streaming
from app.services.session_service import _registry


@pytest.fixture(autouse=True)
def clear_registry():
    _registry.clear()
    yield
    _registry.clear()


def _create_session_with_files(client: TestClient) -> str:
    """Create a session and write test files to its directory."""
    resp = client.post("/sessions")
    sid = resp.json()["session_id"]

    from app.main import session_service
    session_dir = session_service.get_session_dir(sid)
    session_dir.mkdir(parents=True, exist_ok=True)

    (session_dir / "main.py").write_text('print("hello")\n')
    (session_dir / "agents.py").write_text('class MyAgent:\n    pass\n')
    (session_dir / "requirements.txt").write_text('crewai\n')

    return sid


# ── GET /sessions/{id}/files ─────────────────────────────────────────


class TestGetFiles:
    def test_returns_files(self):
        with TestClient(app) as client:
            sid = _create_session_with_files(client)
            resp = client.get(f"/sessions/{sid}/files")
            assert resp.status_code == 200
            data = resp.json()
            assert "files" in data
            assert "main.py" in data["files"]
            assert 'print("hello")' in data["files"]["main.py"]
            assert "agents.py" in data["files"]
            assert "requirements.txt" in data["files"]

    def test_404_unknown_session(self):
        with TestClient(app) as client:
            resp = client.get("/sessions/nonexistent/files")
            assert resp.status_code == 404

    def test_404_empty_session(self):
        with TestClient(app) as client:
            resp = client.post("/sessions")
            sid = resp.json()["session_id"]
            # Session exists but dir may be empty
            from app.main import session_service
            session_dir = session_service.get_session_dir(sid)
            # Remove all files from dir
            import shutil
            if session_dir.exists():
                shutil.rmtree(session_dir)
                session_dir.mkdir()
            resp = client.get(f"/sessions/{sid}/files")
            assert resp.status_code == 404


# ── POST /sessions/{id}/preview/run ──────────────────────────────────


class TestPreviewRun:
    def test_404_unknown_session(self):
        with TestClient(app) as client:
            resp = client.post("/sessions/nonexistent/preview/run")
            assert resp.status_code == 404

    def test_503_docker_unavailable(self):
        with TestClient(app) as client:
            sid = _create_session_with_files(client)
            with patch.object(type(docker_streaming), 'available', new_callable=PropertyMock, return_value=False):
                resp = client.post(f"/sessions/{sid}/preview/run")
                assert resp.status_code == 503
                assert "Docker" in resp.json()["detail"]

    def test_503_no_runner_image(self):
        with TestClient(app) as client:
            sid = _create_session_with_files(client)
            with patch.object(type(docker_streaming), 'available', new_callable=PropertyMock, return_value=True):
                with patch.object(docker_streaming, 'image_exists', return_value=False):
                    resp = client.post(f"/sessions/{sid}/preview/run")
                    assert resp.status_code == 503
                    assert "image" in resp.json()["detail"].lower()

    def test_409_already_running(self):
        with TestClient(app) as client:
            sid = _create_session_with_files(client)
            from app.main import session_service
            session_service.set_preview_running(sid, True)
            with patch.object(type(docker_streaming), 'available', new_callable=PropertyMock, return_value=True):
                with patch.object(docker_streaming, 'image_exists', return_value=True):
                    resp = client.post(f"/sessions/{sid}/preview/run")
                    assert resp.status_code == 409
            session_service.set_preview_running(sid, False)

    def test_404_no_python_entry_point(self):
        with TestClient(app) as client:
            resp = client.post("/sessions")
            sid = resp.json()["session_id"]
            from app.main import session_service
            session_dir = session_service.get_session_dir(sid)
            session_dir.mkdir(parents=True, exist_ok=True)
            (session_dir / "data.json").write_text('{}')

            with patch.object(type(docker_streaming), 'available', new_callable=PropertyMock, return_value=True):
                with patch.object(docker_streaming, 'image_exists', return_value=True):
                    resp = client.post(f"/sessions/{sid}/preview/run")
                    assert resp.status_code == 404
                    assert "entry point" in resp.json()["detail"].lower()


# ── WebSocket /ws/preview/{id} ───────────────────────────────────────


class TestPreviewWebSocket:
    def test_unknown_session_closes(self):
        with TestClient(app) as client:
            with pytest.raises(Exception):
                with client.websocket_connect("/ws/preview/bad-id") as ws:
                    ws.receive_json()

    def test_connect_and_request_no_queue(self):
        """Requesting stream without POST /preview/run returns error."""
        with TestClient(app) as client:
            sid = _create_session_with_files(client)
            with client.websocket_connect(f"/ws/preview/{sid}") as ws:
                ws.send_json({"type": "preview.request_stream"})
                data = ws.receive_json()
                assert data["type"] == "preview.run_error"
                assert "No active run" in data["payload"]["message"]


# ── Session service preview fields ───────────────────────────────────


class TestSessionPreviewFields:
    def test_preview_ws_set_clear(self):
        from app.main import session_service
        sid = session_service.create_session()
        session_service.set_preview_ws(sid, "mock_ws")
        assert _registry[sid]["preview_ws"] == "mock_ws"
        session_service.clear_preview_ws(sid)
        assert _registry[sid]["preview_ws"] is None

    def test_framework_set(self):
        from app.main import session_service
        sid = session_service.create_session()
        session_service.set_framework(sid, "langgraph")
        assert _registry[sid]["framework"] == "langgraph"

    def test_preview_running_flag(self):
        from app.main import session_service
        sid = session_service.create_session()
        assert session_service.is_preview_running(sid) is False
        session_service.set_preview_running(sid, True)
        assert session_service.is_preview_running(sid) is True
        session_service.set_preview_running(sid, False)
        assert session_service.is_preview_running(sid) is False

    def test_preview_running_nonexistent(self):
        from app.main import session_service
        assert session_service.is_preview_running("fake-id") is False
