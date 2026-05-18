import asyncio
import io
import json
import logging
import time
import zipfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from langgraph.types import Command
from pydantic import BaseModel

from app.config import settings
from app.models.messages import (
    ActivityMessage,
    BaseMessage,
    ChatMessage,
    CheckpointMessage,
    CompleteMessage,
    ErrorMessage,
    QuestionGroupMessage,
    StageUpdateMessage,
)
from app.models.preview import (
    PreviewRunCompleteMessage,
    PreviewRunErrorMessage,
    PreviewRunStartedMessage,
    PreviewTraceLineMessage,
)
from app.pipeline.graph import compiled_graph
from app.services.docker_streaming_service import DockerStreamingService
from app.services.streamlit_service import StreamlitService
from app.services.log_parser import parse_line, reset_parser_state
from app.services.session_service import SessionService

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
# Keep noisy libs at INFO
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.INFO)
logging.getLogger("chromadb").setLevel(logging.WARNING)
logging.getLogger("watchfiles").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

session_service = SessionService()
docker_streaming = DockerStreamingService()
streamlit_service = StreamlitService()

# In-memory pipeline run tracking (NFR16: no persistence)
_pipeline_runs: dict[str, asyncio.Task] = {}
_graph_locks: dict[str, asyncio.Lock] = {}
_preview_queues: dict[str, asyncio.Queue] = {}


def _get_graph_lock(session_id: str) -> asyncio.Lock:
    """Get or create an asyncio.Lock for a session's graph invocations."""
    if session_id not in _graph_locks:
        _graph_locks[session_id] = asyncio.Lock()
    return _graph_locks[session_id]


# ── Request/Response Models ──────────────────────────────────────────


class ApproveRequest(BaseModel):
    checkpoint: Literal["requirements", "spec"]
    approved: bool
    feedback: str | None = None


class ApproveResponse(BaseModel):
    status: Literal["resumed", "revision_requested"]


class AiAssistRequest(BaseModel):
    prompt: str
    questions: list[str]


class AiAssistResponse(BaseModel):
    answers: list[str]


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.services.chroma_service import ChromaService

    base_dir = Path(settings.generated_agents_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    chroma = ChromaService(persist_dir=settings.chroma_persist_dir)
    tool_dir = Path(__file__).parent / "tool_library"
    count = chroma.seed_tools(tool_dir)
    logger.info("Seeded %d tools into Chroma.", count)
    app.state.chroma = chroma

    deleted = session_service.cleanup_old_sessions()
    logger.info("Startup complete. Cleaned %d old session(s).", deleted)
    yield


app = FastAPI(title="Frankenstein", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


def _is_qa_interrupt(value: dict) -> bool:
    """Return True if interrupt payload is Q&A questions (not a checkpoint)."""
    return isinstance(value, dict) and "categories" in value and "checkpoint_type" not in value


async def _send_interrupt(ws: WebSocket, interrupt_value: dict, session_id: str) -> None:
    """Route interrupt payload to correct message type: QuestionGroupMessage or CheckpointMessage."""
    if _is_qa_interrupt(interrupt_value):
        msg = QuestionGroupMessage(
            payload=interrupt_value,
            session_id=session_id,
        )
    else:
        msg = CheckpointMessage(
            payload=interrupt_value,
            session_id=session_id,
        )
    await send_message(ws, msg)


async def send_message(ws: WebSocket, msg: BaseMessage) -> None:
    try:
        await ws.send_json(msg.model_dump(mode="json"))
    except WebSocketDisconnect:
        raise
    except Exception as e:
        logger.error("Failed to send WS message: %s", e)
        raise


async def _send_activity(session_id: str, agent: str, text: str) -> None:
    """Send an inline activity message to the chat WebSocket."""
    session = session_service.get_session(session_id)
    chat_ws = session.get("chat_ws") if session else None
    if chat_ws:
        try:
            await send_message(chat_ws, ActivityMessage(
                payload={"agent": agent, "text": text},
                session_id=session_id,
            ))
        except Exception:
            pass


_NODE_ACTIVITIES: dict[str, list[tuple[str, str]]] = {
    "architect": [
        ("architect", "Querying past blueprints from memory..."),
        ("architect", "Decomposing requirements into agent tasks..."),
        ("architect", "Matching tools to task signatures..."),
        ("architect", "Designing agent roles and execution flow..."),
        ("architect", "Compiling full agent specification..."),
    ],
    "critic": [
        ("critic", "Checking for circular dependencies..."),
        ("critic", "Validating format compatibility across agents..."),
        ("critic", "Analyzing tool coverage and capability gaps..."),
        ("critic", "Running adversarial semantic review..."),
        ("critic", "Compiling critique report..."),
    ],
    "builder": [
        ("builder", "Querying past builds from memory..."),
        ("builder", "Planning project structure from spec..."),
        ("builder", "Generating agent code..."),
        ("builder", "Generating tool implementations..."),
        ("builder", "Writing orchestration & entry point..."),
        ("builder", "Running static validation checks..."),
    ],
    "builder_retry": [
        ("builder", "Analyzing test failures..."),
        ("builder", "Patching code from failure traces..."),
        ("builder", "Re-validating repaired files..."),
    ],
    "tester": [
        ("tester", "Generating test cases from spec..."),
        ("tester", "Running static analysis..."),
        ("tester", "Executing agent in Docker sandbox..."),
        ("tester", "Analyzing execution output..."),
    ],
    "learner": [
        ("learner", "Extracting build patterns..."),
        ("learner", "Storing outcome in vector memory..."),
    ],
}

_NODE_STAGE_DESC: dict[str, tuple[str, str]] = {
    "architect": ("architect", "Designing your agent architecture..."),
    "critic": ("critic", "Reviewing blueprint..."),
    "builder": ("builder", "Building your agents..."),
    "tester": ("tester", "Testing your agents..."),
    "learner": ("learner", "Storing patterns..."),
}


async def _run_post_approval(session_id: str, config: dict, graph_lock: asyncio.Lock) -> None:
    """Run builder→tester→learner in background after spec approval.

    Uses a queue bridge: sync graph.stream thread puts node events,
    async loop consumes them for real-time WS updates. Supports cycling
    (builder appearing multiple times in repair loops).
    """
    try:
        build_start = time.time()
        logger.info("[%s] POST-APPROVAL: starting builder→tester→learner pipeline", session_id)

        event_queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_event_loop()

        def _stream_graph():
            """Run graph.stream in a thread, putting node events onto queue."""
            try:
                logger.info("[%s] POST-APPROVAL: graph.stream starting in thread", session_id)
                for chunk in compiled_graph.stream(
                    Command(resume={"approved": True}),
                    config,
                    stream_mode="updates",
                ):
                    for node_name in chunk:
                        asyncio.run_coroutine_threadsafe(
                            event_queue.put(("node", node_name)), loop
                        )
                logger.info("[%s] POST-APPROVAL: graph.stream completed", session_id)
            finally:
                asyncio.run_coroutine_threadsafe(
                    event_queue.put(("done", None)), loop
                )

        logger.info("[%s] POST-APPROVAL: acquiring graph lock...", session_id)
        async with graph_lock:
            logger.info("[%s] POST-APPROVAL: graph lock acquired, starting stream", session_id)
            asyncio.get_event_loop().run_in_executor(None, _stream_graph)

            # Consume node events in real-time
            node_counts: dict[str, int] = {}
            prev_node: str | None = None

            while True:
                event_type, node_name = await event_queue.get()
                if event_type == "done":
                    break

                # Skip internal nodes
                if node_name not in _NODE_STAGE_DESC:
                    continue

                # Track how many times each node appears
                node_counts[node_name] = node_counts.get(node_name, 0) + 1
                count = node_counts[node_name]

                # Mark previous node done
                if prev_node and prev_node != node_name and prev_node in _NODE_STAGE_DESC:
                    session = session_service.get_session(session_id)
                    status_ws = session.get("status_ws") if session else None
                    if status_ws:
                        await send_message(status_ws, StageUpdateMessage(
                            payload={"stage": prev_node, "description": f"{prev_node.title()} complete", "status": "done"},
                            session_id=session_id,
                        ))

                # Send stage update (active)
                stage_id, stage_desc = _NODE_STAGE_DESC[node_name]
                session = session_service.get_session(session_id)
                status_ws = session.get("status_ws") if session else None
                if status_ws:
                    desc = stage_desc if count == 1 else f"Retrying {node_name}... (attempt {count})"
                    await send_message(status_ws, StageUpdateMessage(
                        payload={"stage": stage_id, "description": desc},
                        session_id=session_id,
                    ))

                # Pick activity key: use retry variant for builder on 2nd+ appearance
                if node_name == "builder" and count > 1:
                    activity_key = "builder_retry"
                else:
                    activity_key = node_name

                for agent, text in _NODE_ACTIVITIES.get(activity_key, []):
                    await _send_activity(session_id, agent, text)
                    await asyncio.sleep(0.05)

                prev_node = node_name

        build_time = round(time.time() - build_start, 1)
        logger.info("[%s] POST-APPROVAL: pipeline completed in %.1fs", session_id, build_time)

        # Final: mark all stages done + send completion
        session = session_service.get_session(session_id)
        status_ws = session.get("status_ws") if session else None

        if status_ws:
            for stage_id, desc in [
                ("builder", "Code generated"),
                ("tester", "Tests complete"),
                ("learner", "Patterns stored"),
            ]:
                await send_message(status_ws, StageUpdateMessage(
                    payload={"stage": stage_id, "description": desc, "status": "done"},
                    session_id=session_id,
                ))

            final_state = compiled_graph.get_state(config).values
            code_bundle = final_state.get("generated_code")
            test_results = final_state.get("test_results")
            spec = final_state.get("spec")
            framework = code_bundle.framework if code_bundle else "unknown"
            session_service.set_framework(session_id, framework)
            all_passed = test_results.all_passed if test_results else True
            summary = (
                f"Your {framework} agent pipeline is ready for download."
                if all_passed
                else f"Your {framework} agent pipeline is mostly ready — some tests had issues."
            )

            await send_message(status_ws, CompleteMessage(
                payload={
                    "session_id": session_id,
                    "framework": framework,
                    "download_url": f"/api/sessions/{session_id}/download",
                    "summary": summary,
                    "all_passed": all_passed,
                    "agents_count": len(spec.agents) if spec else 0,
                    "test_passed": test_results.passed if test_results else 0,
                    "test_total": test_results.total if test_results else 0,
                    "file_count": len(code_bundle.files) if code_bundle else 0,
                    "build_time_seconds": build_time,
                },
                session_id=session_id,
            ))

    except Exception as e:
        logger.error("[%s] POST-APPROVAL FAILED: %s", session_id, e, exc_info=True)
        session = session_service.get_session(session_id)
        chat_ws = session.get("chat_ws") if session else None
        if chat_ws:
            try:
                await send_message(chat_ws, ErrorMessage(
                    payload={
                        "stage": "builder",
                        "message": f"Build pipeline error: {e}",
                        "recoverable": False,
                    },
                    session_id=session_id,
                ))
            except Exception:
                pass


async def _run_req_approval(session_id: str, config: dict, graph_lock: asyncio.Lock) -> None:
    """Run architect→critic→spec_checkpoint in background after requirements approval.

    Uses queue-based streaming so architect↔critic cycling shows in real-time.
    """
    try:
        logger.info("[%s] REQ-APPROVAL: starting architect→critic pipeline", session_id)

        # Mark elicitor done
        session = session_service.get_session(session_id)
        status_ws = session.get("status_ws") if session else None
        if status_ws:
            try:
                await send_message(status_ws, StageUpdateMessage(
                    payload={"stage": "elicitor", "description": "Requirements gathered", "status": "done"},
                    session_id=session_id,
                ))
            except Exception:
                logger.warning("Failed to send elicitor done to %s", session_id)

        # Queue-based real-time streaming for architect→critic
        event_queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_event_loop()

        def _stream_req_approval():
            try:
                for chunk in compiled_graph.stream(
                    Command(resume={"approved": True}),
                    config,
                    stream_mode="updates",
                ):
                    for node_name in chunk:
                        asyncio.run_coroutine_threadsafe(
                            event_queue.put(("node", node_name)), loop
                        )
            finally:
                asyncio.run_coroutine_threadsafe(
                    event_queue.put(("done", None)), loop
                )

        async with graph_lock:
            loop.run_in_executor(None, _stream_req_approval)

            prev_node: str | None = None
            while True:
                event_type, node_name = await event_queue.get()
                if event_type == "done":
                    break

                if node_name not in _NODE_STAGE_DESC:
                    continue

                # Mark previous node done
                if prev_node and prev_node != node_name and prev_node in _NODE_STAGE_DESC:
                    session = session_service.get_session(session_id)
                    status_ws = session.get("status_ws") if session else None
                    if status_ws:
                        await send_message(status_ws, StageUpdateMessage(
                            payload={"stage": prev_node, "description": f"{prev_node.title()} complete", "status": "done"},
                            session_id=session_id,
                        ))

                # Activate current node
                stage_id, stage_desc = _NODE_STAGE_DESC[node_name]
                session = session_service.get_session(session_id)
                status_ws = session.get("status_ws") if session else None
                if status_ws:
                    await send_message(status_ws, StageUpdateMessage(
                        payload={"stage": stage_id, "description": stage_desc},
                        session_id=session_id,
                    ))

                for agent, text in _NODE_ACTIVITIES.get(node_name, []):
                    await _send_activity(session_id, agent, text)
                    await asyncio.sleep(0.05)

                prev_node = node_name

        # Mark last streamed node done
        if prev_node and prev_node in _NODE_STAGE_DESC:
            session = session_service.get_session(session_id)
            status_ws = session.get("status_ws") if session else None
            if status_ws:
                await send_message(status_ws, StageUpdateMessage(
                    payload={"stage": prev_node, "description": f"{prev_node.title()} complete", "status": "done"},
                    session_id=session_id,
                ))

        # Re-fetch fresh WS refs — originals may have disconnected/reconnected
        session = session_service.get_session(session_id)
        chat_ws = session.get("chat_ws") if session else None
        status_ws = session.get("status_ws") if session else None

        # Check if graph paused at next interrupt (spec checkpoint)
        state = compiled_graph.get_state(config)
        if state.next and state.tasks and hasattr(state.tasks[0], "interrupts") and state.tasks[0].interrupts:
            interrupt_value = state.tasks[0].interrupts[0].value
            logger.info("[%s] Forwarding post-approval interrupt to frontend", session_id)
            if chat_ws:
                await _send_interrupt(chat_ws, interrupt_value, session_id)

            # Send stage update for spec review
            if status_ws and isinstance(interrupt_value, dict) and interrupt_value.get("checkpoint_type") == "spec":
                await send_message(status_ws, StageUpdateMessage(
                    payload={
                        "stage": "spec_review",
                        "description": "Review your agent blueprint",
                        "is_checkpoint": True,
                    },
                    session_id=session_id,
                ))

    except Exception as e:
        logger.error("[%s] REQ-APPROVAL FAILED: %s", session_id, e, exc_info=True)
        session = session_service.get_session(session_id)
        chat_ws = session.get("chat_ws") if session else None
        if chat_ws:
            try:
                await send_message(chat_ws, ErrorMessage(
                    payload={
                        "stage": "architect",
                        "message": f"Design pipeline error: {e}",
                        "recoverable": False,
                    },
                    session_id=session_id,
                ))
            except Exception:
                pass


# ── REST Endpoints ───────────────────────────────────────────────────


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/sessions", status_code=201)
async def create_session():
    try:
        session_id = session_service.create_session()
        return {"session_id": session_id}
    except OSError as e:
        logger.error("Failed to create session directory: %s", e)
        return JSONResponse(
            content={"detail": "Failed to create session directory"},
            status_code=500,
        )


@app.post("/sessions/{session_id}/approve", response_model=ApproveResponse)
async def approve_checkpoint(session_id: str, body: ApproveRequest):
    """Resume pipeline after human checkpoint approval or send corrections."""
    logger.info("[%s] APPROVE: checkpoint=%s approved=%s feedback=%s",
                session_id, body.checkpoint, body.approved,
                body.feedback[:80] if body.feedback else None)
    if not session_service.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    thread_id = session_id
    config = {"configurable": {"thread_id": thread_id}}
    is_spec = body.checkpoint == "spec"

    # Idempotency: if graph already moved past checkpoint, return early
    graph_state = compiled_graph.get_state(config)
    if not graph_state.next:
        return ApproveResponse(status="resumed")

    graph_lock = _get_graph_lock(session_id)

    if body.approved:
        session = session_service.get_session(session_id)
        chat_ws = session.get("chat_ws") if session else None
        status_ws = session.get("status_ws") if session else None

        if is_spec:
            confirm_text = "Blueprint approved — building your agents..."
            stage_name = "spec_review"
            stage_desc = "Blueprint approved"
        else:
            confirm_text = "Requirements approved — designing your agent architecture..."
            stage_name = "requirements_review"
            stage_desc = "Requirements approved"

        if chat_ws:
            try:
                await send_message(chat_ws, ChatMessage(
                    payload={"text": confirm_text},
                    session_id=session_id,
                ))
            except Exception:
                logger.warning("Failed to send approval confirmation to %s", session_id)

        if status_ws:
            try:
                await send_message(status_ws, StageUpdateMessage(
                    payload={"stage": stage_name, "description": stage_desc, "status": "done"},
                    session_id=session_id,
                ))
            except Exception:
                logger.warning("Failed to send stage update to %s", session_id)

        if is_spec:
            # Run builder→tester→learner as background task so HTTP responds immediately
            asyncio.create_task(_run_post_approval(session_id, config, graph_lock))
        else:
            # Run architect→critic as background task so HTTP responds immediately
            # (this flow can take minutes with multiple revision cycles)
            asyncio.create_task(_run_req_approval(session_id, config, graph_lock))

        logger.info("[%s] %s approved — pipeline resumed", session_id, body.checkpoint)
        return ApproveResponse(status="resumed")

    else:
        if is_spec:
            # Spec feedback: resume with feedback for architect revision
            async with graph_lock:
                await asyncio.to_thread(
                    compiled_graph.invoke,
                    Command(resume={"approved": False, "feedback": body.feedback or ""}),
                    config,
                )
            logger.info("[%s] Spec feedback sent — architect revising", session_id)
        else:
            # Requirements corrections: resume with corrections for elicitor
            async with graph_lock:
                await asyncio.to_thread(
                    compiled_graph.invoke,
                    Command(resume={"approved": False, "corrections": body.feedback or ""}),
                    config,
                )
            logger.info("[%s] Requirements corrections sent — elicitor re-running", session_id)

        return ApproveResponse(status="revision_requested")


@app.get("/sessions/{session_id}/download")
async def download_agent(session_id: str):
    """Download the generated agent project as a zip file."""
    if not session_service.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    session_dir = session_service.get_session_dir(session_id)
    if not session_dir.exists() or not any(session_dir.iterdir()):
        raise HTTPException(status_code=404, detail="No generated files found")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(session_dir.rglob("*")):
            if file_path.is_file():
                arcname = file_path.relative_to(session_dir)
                zf.write(file_path, arcname)

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=agent_{session_id[:8]}.zip"},
    )


@app.post("/sessions/{session_id}/streamlit/start")
async def streamlit_start(session_id: str):
    """Start a Streamlit container for live app preview."""
    if not session_service.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    if not streamlit_service.available:
        raise HTTPException(status_code=503, detail="Docker not available")

    session_dir = session_service.get_session_dir(session_id)
    if not (session_dir / "app.py").exists():
        raise HTTPException(status_code=404, detail="No app.py found in generated files")

    if streamlit_service.is_running(session_id):
        raise HTTPException(status_code=409, detail="Streamlit already running")

    try:
        result = streamlit_service.start(session_id, session_dir)
        return result
    except Exception as e:
        logger.error("[%s] Streamlit start error: %s", session_id, e, exc_info=True)
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/sessions/{session_id}/streamlit/stop")
async def streamlit_stop(session_id: str):
    """Stop a session's Streamlit container."""
    if not streamlit_service.is_running(session_id):
        raise HTTPException(status_code=404, detail="No Streamlit container running")
    streamlit_service.stop(session_id)
    return {"status": "stopped"}


@app.get("/sessions/{session_id}/streamlit/status")
async def streamlit_status(session_id: str):
    """Check Streamlit container status."""
    running = streamlit_service.is_running(session_id)
    url = streamlit_service.get_url(session_id) if running else None
    return {"running": running, "url": url}


AI_ASSIST_SYSTEM = """\
You are a knowledgeable domain expert helping a user answer questions about building \
an AI agent pipeline. The user originally described their project as follows:

"{prompt}"

You are now answering specific clarifying questions on their behalf. Respond as if you \
are the domain expert who wrote the original prompt. Give specific, concrete answers \
with realistic values — not generic placeholders. Keep each answer to 2-4 sentences.

Respond ONLY with valid JSON:
{{
  "answers": ["<answer to question 1>", "<answer to question 2>", ...]
}}"""


@app.post("/sessions/{session_id}/ai-assist", response_model=AiAssistResponse)
async def ai_assist(session_id: str, body: AiAssistRequest):
    """Use AI to generate suggested answers for elicitor questions."""
    if not session_service.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    from app.services.llm_service import LLMService
    import json as _json

    llm = LLMService()
    system = AI_ASSIST_SYSTEM.format(prompt=body.prompt)
    questions_text = "\n".join(
        f"{i + 1}. {q}" for i, q in enumerate(body.questions)
    )
    user_msg = f"Answer these questions:\n\n{questions_text}"

    try:
        raw = await asyncio.to_thread(
            llm.call,
            "elicitor",
            system,
            user_msg,
            json_mode=True,
        )
        data = _json.loads(raw)
        answers = data.get("answers", [])
        # Pad or trim to match question count
        while len(answers) < len(body.questions):
            answers.append("")
        answers = answers[: len(body.questions)]
        return AiAssistResponse(answers=answers)
    except Exception as e:
        logger.error("[%s] AI assist error: %s", session_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI assist failed: {e}")


# ── Preview Endpoints ────────────────────────────────────────────────


@app.get("/sessions/{session_id}/files")
async def get_session_files(session_id: str):
    """Return all generated files for a session as {files: {name: content}}."""
    if not session_service.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    session_dir = session_service.get_session_dir(session_id)
    if not session_dir.exists() or not any(session_dir.iterdir()):
        raise HTTPException(status_code=404, detail="No generated files found")

    files: dict[str, str] = {}
    for file_path in sorted(session_dir.rglob("*")):
        if file_path.is_file():
            rel = str(file_path.relative_to(session_dir))
            try:
                files[rel] = file_path.read_text(errors="replace")
            except Exception:
                files[rel] = "# [binary or unreadable file]"

    return {"files": files}


@app.post("/sessions/{session_id}/preview/run", status_code=202)
async def start_preview_run(session_id: str):
    """Launch a streaming Docker execution for preview."""
    if not session_service.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    if not docker_streaming.available:
        raise HTTPException(status_code=503, detail="Docker not available")

    if not docker_streaming.image_exists():
        raise HTTPException(status_code=503, detail="Runner image not built")

    if session_service.is_preview_running(session_id):
        raise HTTPException(status_code=409, detail="Preview already running")

    session_dir = session_service.get_session_dir(session_id)
    if not session_dir.exists() or not any(session_dir.iterdir()):
        raise HTTPException(status_code=404, detail="No generated files found")

    # Determine entry point and framework
    entry_point = "main.py"
    framework = "crewai"
    session = session_service.get_session(session_id)
    if session and session.get("framework"):
        framework = session["framework"]

    # Check for entry point
    if not (session_dir / entry_point).exists():
        # Try to find any .py file
        py_files = list(session_dir.glob("*.py"))
        if py_files:
            entry_point = py_files[0].name
        else:
            raise HTTPException(status_code=404, detail="No Python entry point found")

    # Set up queue and launch
    queue: asyncio.Queue = asyncio.Queue()
    _preview_queues[session_id] = queue
    session_service.set_preview_running(session_id, True)

    env = {"CREWAI_TRACING_ENABLED": "false"}
    if settings.openrouter_api_key:
        env["OPENROUTER_API_KEY"] = settings.openrouter_api_key

    async def _run():
        try:
            result = await docker_streaming.run_streaming(
                session_dir=session_dir,
                entry_point=entry_point,
                env=env,
                queue=queue,
            )
            # Store result for WS to pick up
            await queue.put({"_result": result})
        except Exception as e:
            logger.error("[%s] Preview run error: %s", session_id, e, exc_info=True)
            await queue.put({"_error": str(e)})
        finally:
            session_service.set_preview_running(session_id, False)

    asyncio.create_task(_run())
    return {"status": "started"}


@app.websocket("/ws/preview/{session_id}")
async def ws_preview(websocket: WebSocket, session_id: str):
    """WebSocket for streaming preview execution output."""
    await websocket.accept()

    if not session_service.session_exists(session_id):
        await websocket.close(code=4004, reason="unknown session")
        return

    session_service.set_preview_ws(session_id, websocket)

    # Determine framework for log parsing
    session = session_service.get_session(session_id)
    framework = (session.get("framework") or "crewai") if session else "crewai"
    reset_parser_state()

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except (ValueError, TypeError):
                continue

            msg_type = data.get("type", "")

            if msg_type == "preview.request_stream":
                # Client ready to receive — read from queue
                queue = _preview_queues.get(session_id)
                if not queue:
                    await websocket.send_json(
                        PreviewRunErrorMessage(
                            payload={"message": "No active run. Click Run first."},
                            session_id=session_id,
                        ).model_dump(mode="json")
                    )
                    continue

                # Send run_started
                await websocket.send_json(
                    PreviewRunStartedMessage(
                        payload={"container_id": "pending"},
                        session_id=session_id,
                    ).model_dump(mode="json")
                )

                # Stream lines from queue
                while True:
                    item = await queue.get()

                    if item is None:
                        # Sentinel — wait for result dict
                        continue

                    if isinstance(item, dict):
                        if "_error" in item:
                            await websocket.send_json(
                                PreviewRunErrorMessage(
                                    payload={"message": item["_error"]},
                                    session_id=session_id,
                                ).model_dump(mode="json")
                            )
                            break
                        if "_result" in item:
                            result = item["_result"]
                            await websocket.send_json(
                                PreviewRunCompleteMessage(
                                    payload={
                                        "exit_code": result.get("exit_code", -1),
                                        "duration_ms": result.get("duration_ms", 0),
                                        "output": result.get("output", "")[:5000],
                                    },
                                    session_id=session_id,
                                ).model_dump(mode="json")
                            )
                            break
                        continue

                    # It's a log line string
                    event = parse_line(item, framework)
                    await websocket.send_json(
                        PreviewTraceLineMessage(
                            payload={"event": event.model_dump()},
                            session_id=session_id,
                        ).model_dump(mode="json")
                    )

                # Cleanup queue
                _preview_queues.pop(session_id, None)

    except WebSocketDisconnect:
        logger.info("Preview WS disconnected: %s", session_id)
    finally:
        session_service.clear_preview_ws(session_id)


# ── WebSocket Endpoints ─────────────────────────────────────────────


@app.websocket("/ws/chat/{session_id}")
async def ws_chat(websocket: WebSocket, session_id: str):
    await websocket.accept()
    logger.info("[%s] Chat WS CONNECTED (client=%s)", session_id, websocket.client)

    if not session_service.session_exists(session_id):
        logger.warning("[%s] Chat WS rejected — unknown session", session_id)
        await websocket.close(code=4004, reason="unknown session")
        return

    session_service.set_chat_ws(session_id, websocket)

    welcome = ChatMessage(
        payload={"text": "Frankenstein is ready. Describe the agent you want to build."},
        session_id=session_id,
    )
    await send_message(websocket, welcome)

    # Replay pending interrupt if graph is paused (handles page refresh / WS reconnect)
    if session_id in _pipeline_runs:
        try:
            config = {"configurable": {"thread_id": session_id}}
            state = compiled_graph.get_state(config)
            if state.next and state.tasks and hasattr(state.tasks[0], "interrupts") and state.tasks[0].interrupts:
                interrupt_value = state.tasks[0].interrupts[0].value
                logger.info("[%s] Replaying pending interrupt on WS reconnect", session_id)
                await _send_interrupt(websocket, interrupt_value, session_id)
        except Exception as e:
            logger.warning("[%s] Failed to replay interrupt: %s", session_id, e)

    async def run_pipeline(prompt: str) -> None:
        """Run pipeline in background, forwarding interrupts to frontend."""
        thread_id = session_id
        config = {"configurable": {"thread_id": thread_id}}
        initial_state = {"raw_prompt": prompt, "session_id": session_id}
        logger.info("[%s] PIPELINE START: prompt=%d chars", session_id, len(prompt))

        try:
            # Send stage update
            session = session_service.get_session(session_id)
            status_ws = session.get("status_ws") if session else None
            if status_ws:
                stage_msg = StageUpdateMessage(
                    payload={"stage": "elicitor", "description": "Understanding your needs"},
                    session_id=session_id,
                )
                await send_message(status_ws, stage_msg)

            # Run graph — blocks at interrupt() points
            graph_lock = _get_graph_lock(session_id)
            logger.info("[%s] PIPELINE: acquiring graph lock...", session_id)
            async with graph_lock:
                logger.info("[%s] PIPELINE: graph lock acquired, invoking graph (timeout=%ds)", session_id, settings.pipeline_timeout)
                result = await asyncio.wait_for(
                    asyncio.to_thread(compiled_graph.invoke, initial_state, config),
                    timeout=settings.pipeline_timeout,
                )
                logger.info("[%s] PIPELINE: graph.invoke returned", session_id)

            # Check for interrupt (graph paused at checkpoint)
            state = compiled_graph.get_state(config)
            while state.next:
                if state.tasks and hasattr(state.tasks[0], "interrupts") and state.tasks[0].interrupts:
                    interrupt_value = state.tasks[0].interrupts[0].value
                    await _send_interrupt(websocket, interrupt_value, session_id)

                    # Only send stage update for actual checkpoints, not Q&A
                    if not _is_qa_interrupt(interrupt_value):
                        cp_type = interrupt_value.get("checkpoint_type", "requirements") if isinstance(interrupt_value, dict) else "requirements"
                        stage_name = "spec_review" if cp_type == "spec" else "requirements_review"
                        stage_desc = "Review your agent blueprint" if cp_type == "spec" else "Reviewing requirements with you"

                        if status_ws:
                            stage_msg = StageUpdateMessage(
                                payload={
                                    "stage": stage_name,
                                    "description": stage_desc,
                                    "is_checkpoint": True,
                                },
                                session_id=session_id,
                            )
                            await send_message(status_ws, stage_msg)

                break

            logger.info("[%s] Pipeline initial run complete", session_id)

        except Exception as e:
            logger.error("[%s] Pipeline error: %s", session_id, e, exc_info=True)
            current_stage = session_service.get_session(session_id) or {}
            err = ErrorMessage(
                type="error.pipeline_failure",
                payload={
                    "stage": current_stage.get("stage", "unknown"),
                    "message": f"Pipeline error: {e}",
                    "recoverable": False,
                },
                session_id=session_id,
            )
            try:
                await send_message(websocket, err)
            except Exception:
                pass

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except (ValueError, TypeError):
                logger.warning("Invalid JSON from %s, ignoring", session_id)
                continue
            if not isinstance(data, dict) or "type" not in data:
                logger.warning("Malformed message from %s (missing type), ignoring", session_id)
                continue
            msg_type = data["type"]
            logger.info("Chat message from %s: %s", session_id, msg_type)

            if msg_type == "control.user_input":
                payload = data.get("payload", {})
                text = payload.get("text", "")
                if text and session_id not in _pipeline_runs:
                    # First prompt — start pipeline
                    task = asyncio.create_task(run_pipeline(text))
                    _pipeline_runs[session_id] = task
                    task.add_done_callback(lambda t: t.exception() if not t.cancelled() and t.exception() else None)
                elif text:
                    # Subsequent input (e.g., elicitor Q&A answers) — resume graph
                    logger.info("[%s] Resuming graph with user input (%d chars)", session_id, len(text))
                    thread_id = session_id
                    config = {"configurable": {"thread_id": thread_id}}
                    try:
                        graph_lock = _get_graph_lock(session_id)
                        logger.info("[%s] Acquiring graph lock...", session_id)
                        async with graph_lock:
                            logger.info("[%s] Graph lock acquired, invoking Command(resume=...)", session_id)
                            await asyncio.to_thread(
                                compiled_graph.invoke,
                                Command(resume=text),
                                config,
                            )
                        logger.info("[%s] Graph invoke returned, checking for next interrupt", session_id)
                        # Check if graph paused again (next Q&A round or checkpoint)
                        state = compiled_graph.get_state(config)
                        logger.info("[%s] Graph state.next=%s, has_tasks=%s", session_id, state.next, bool(state.tasks))
                        if state.next and state.tasks and hasattr(state.tasks[0], "interrupts") and state.tasks[0].interrupts:
                            interrupt_value = state.tasks[0].interrupts[0].value
                            is_qa = _is_qa_interrupt(interrupt_value)
                            logger.info("[%s] Sending interrupt (is_qa=%s)", session_id, is_qa)
                            await _send_interrupt(websocket, interrupt_value, session_id)
                        else:
                            logger.info("[%s] No pending interrupt after resume", session_id)
                    except Exception as e:
                        logger.error("[%s] Resume error: %s", session_id, e, exc_info=True)
                        try:
                            await send_message(websocket, ErrorMessage(
                                type="error.pipeline_failure",
                                payload={
                                    "stage": "elicitor",
                                    "message": f"Resume error: {e}",
                                    "recoverable": False,
                                },
                                session_id=session_id,
                            ))
                        except Exception:
                            pass
            else:
                logger.debug("Unhandled message type: %s", msg_type)

    except WebSocketDisconnect:
        logger.warning("[%s] Chat WS DISCONNECTED — pipeline task running=%s",
                       session_id, session_id in _pipeline_runs and not _pipeline_runs[session_id].done())
    finally:
        session_service.clear_chat_ws(session_id)
        # Clean up pipeline task and graph lock
        task = _pipeline_runs.pop(session_id, None)
        if task and not task.done():
            logger.warning("[%s] Cancelling running pipeline task due to WS disconnect", session_id)
            task.cancel()
        _graph_locks.pop(session_id, None)


@app.websocket("/ws/status/{session_id}")
async def ws_status(websocket: WebSocket, session_id: str):
    await websocket.accept()
    logger.info("[%s] Status WS CONNECTED (client=%s)", session_id, websocket.client)

    if not session_service.session_exists(session_id):
        logger.warning("[%s] Status WS rejected — unknown session", session_id)
        await websocket.close(code=4004, reason="unknown session")
        return

    session_service.set_status_ws(session_id, websocket)

    stage_msg = StageUpdateMessage(
        payload={"stage": "idle", "description": "Waiting for prompt"},
        session_id=session_id,
    )
    await send_message(websocket, stage_msg)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.warning("[%s] Status WS DISCONNECTED", session_id)
    finally:
        session_service.clear_status_ws(session_id)
