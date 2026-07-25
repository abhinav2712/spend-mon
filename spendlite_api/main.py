"""FastAPI app: one MCP connection, one agent, and a normalized SSE event stream."""

import json
from contextlib import AsyncExitStack, asynccontextmanager

from agents import InputGuardrailTripwireTriggered, Runner
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from openai.types.responses import ResponseTextDeltaEvent
from pydantic import BaseModel
from pathlib import Path
from fastapi.staticfiles import StaticFiles


from spendlite_agent.core import build_agent, build_mcp_server
from spendlite_api.events import (
    Delta,
    Done,
    Error,
    GuardrailTriggered,
    ToolCall,
    ToolResult,
    sse,
)
from spendlite_api.sessions import (
    get_history,
    list_sessions,
    new_session_id,
    open_session,
)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
REDIRECT = (
    "I can only help with your recorded expenses. Try asking about spending "
    "in a particular month, category, or merchant."
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    async with AsyncExitStack() as stack:
        ## build_mcp_server() inside the FastAPI lifespan context ensures that the MCP server 
        # connection is established when the app starts and properly closed when the app shuts down.
        mcp_server = await stack.enter_async_context(build_mcp_server())
        app.state.agent = build_agent(mcp_server)
        yield


app = FastAPI(title="SpendLite API", lifespan=lifespan)


class MessageIn(BaseModel):
    message: str


def parse_tool_output(output):
    """MCP tools return JSON text wrapped in {"result": ...}; local tools return plain strings."""
    if not isinstance(output, str):
        return output
    try:
        parsed = json.loads(output)
    except ValueError:
        return output
    if isinstance(parsed, dict) and list(parsed.keys()) == ["result"]:
        return parsed["result"]
    return parsed


async def event_stream(agent, session, session_id: str, message: str):
    tool_names: dict[str, str] = {}
    try:
        result = Runner.run_streamed(agent, message, session=session)
        async for event in result.stream_events():
            if event.type == "raw_response_event":
                if isinstance(event.data, ResponseTextDeltaEvent) and event.data.delta:
                    yield sse(Delta(text=event.data.delta))

            elif event.type == "run_item_stream_event":
                item = event.item

                if item.type == "tool_call_item":
                    raw = item.raw_item
                    call_id = getattr(raw, "call_id", "") or ""
                    name = getattr(raw, "name", "tool")
                    tool_names[call_id] = name
                    yield sse(ToolCall(name=name, call_id=call_id))

                elif item.type == "tool_call_output_item":
                    raw = item.raw_item if isinstance(item.raw_item, dict) else {}
                    call_id = raw.get("call_id", "")
                    yield sse(
                        ToolResult(
                            name=tool_names.get(call_id, "tool"),
                            call_id=call_id,
                            data=parse_tool_output(raw.get("output")),
                        )
                    )

        yield sse(Done(session_id=session_id))

    except InputGuardrailTripwireTriggered:
        await session.pop_item()  # otherwise it poisons every later turn
        yield sse(GuardrailTriggered(message=REDIRECT))

    except Exception as exc:
        yield sse(Error(message=str(exc) or exc.__class__.__name__))


@app.post("/api/sessions")
async def create_session() -> dict:
    return {"id": new_session_id()}


@app.get("/api/sessions")
async def get_sessions() -> list[dict]:
    return list_sessions()


@app.get("/api/sessions/{session_id}/messages")
async def session_history(session_id: str) -> list[dict]:
    return await get_history(session_id)


@app.post("/api/sessions/{session_id}/messages")
async def send_message(session_id: str, body: MessageIn) -> StreamingResponse:
    return StreamingResponse(
        event_stream(
            app.state.agent, open_session(session_id), session_id, body.message
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

# Mount LAST so every /api route is matched first. Present only in the container
# image, where the build copies the compiled SPA here; in dev, Vite serves it.
if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="web")
