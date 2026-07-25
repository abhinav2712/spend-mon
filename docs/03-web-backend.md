# Phase 3 — `spendlite_api`: FastAPI + the normalized SSE event protocol

**You are here:** Phase 3 of 5. The agent works in a terminal. This phase gives it an HTTP face: a FastAPI app that runs the *same* agent (imported from `spendlite_agent.core`) and streams **normalized, typed events** to any client over SSE. This event protocol is the centerpiece — it's the Con-Mon run-stream pattern, and it's what makes Phase 4's charts deterministic.

## What you'll learn

- The SSE wire format, by writing it yourself (`data: {...}\n\n`) instead of using a library.
- **Event normalization:** translating the Agents SDK's internal stream events into a small, stable, client-facing protocol. Clients depend on *your* protocol, never on the SDK's shapes — so SDK upgrades can't break your frontend.
- FastAPI `lifespan` for managing long-lived resources (the MCP connection) across requests.
- Session management as an API concern: list/create/resume conversations.

## The event protocol (`events.py`) — design this first

Every SSE frame is `data: <json>\n\n`. Define these as Pydantic models; they are your API contract:

| type | payload | emitted when |
|------|---------|--------------|
| `delta` | `{text}` | each token of assistant text |
| `tool_call` | `{name, call_id}` | agent invokes any tool (local or MCP) |
| `tool_result` | `{name, call_id, data}` | a tool returns — `data` is the parsed result; **this is what drives charts** |
| `guardrail_triggered` | `{message}` | input guardrail tripwire |
| `done` | `{session_id}` | run completed normally |
| `error` | `{message}` | anything failed mid-run |

Rules:
- Every event has a `type` field; clients switch on it and **ignore unknown types** (forward compatibility — you'll add types later, e.g. a `chart` event for the agent-driven stretch).
- A stream always terminates with exactly one of `done`, `guardrail_triggered`, or `error`. The frontend's "is it still thinking?" state hangs on this invariant.

## Endpoints

| Method + path | Body → Response | Notes |
|---------------|-----------------|-------|
| `POST /api/sessions` | `{}` → `{id, title, created_at}` | creates a session id; title starts null |
| `GET /api/sessions` | → `[{id, title, created_at, updated_at}]` | newest first, for the sidebar |
| `GET /api/sessions/{id}/messages` | → `[{role, content}]` | history for resume (see 3.4) |
| `POST /api/sessions/{id}/messages` | `{message}` → **`text/event-stream`** | the main event: runs the agent, streams events |

> **Why POST for the stream:** the browser's `EventSource` API only does GET, which would force the message into a query string. Modern chat apps POST and read the response body as a stream via `fetch` — Phase 4 does exactly that. You're hand-parsing SSE frames on both ends, which is the point: after this you *know* the format.

## Build steps

### 3.1 App skeleton + lifespan (`main.py`)

- FastAPI app; on startup (lifespan), connect the MCP server once via `spendlite_agent.core.build_mcp_server()` (an `AsyncExitStack` entered in lifespan is the clean shape) and build the agent once. Store both on `app.state`.
- The agent object is stateless between runs — per-conversation state lives entirely in the `SQLiteSession` — so one shared agent instance is safe across requests. Say this out loud in the demo; it's a real architecture point.
- Run with `uvicorn spendlite_api.main:app --port 8000` from repo root.

### 3.2 The stream translator — the heart of this phase

An async generator: takes (agent, message, session), yields protocol events as SSE-framed strings; wrap it in `StreamingResponse(gen, media_type="text/event-stream")`.

Mapping (SDK event → your protocol):

| SDK stream event | → protocol event |
|---|---|
| `raw_response_event` with `ResponseTextDeltaEvent` | `delta` |
| `run_item_stream_event`, `item.type == "tool_call_item"` | `tool_call` — also record `call_id → name` in a local dict |
| `run_item_stream_event`, `item.type == "tool_call_output_item"` | `tool_result` — look the name up from that dict |
| `InputGuardrailTripwireTriggered` raised | `guardrail_triggered`, then end stream |
| any other exception | `error` (message only, never a traceback), then end stream |
| normal completion | `done` |

Two real problems you'll solve here (both are features, not bugs, of doing this by hand):
1. **Pairing outputs to names:** tool *output* items carry a `call_id` but not a friendly name — hence the `call_id → name` dict built from the call items. Con-Mon's stream normalizer does the same dance.
2. **Tool output parsing:** MCP tool outputs arrive as text (JSON in a string). `json.loads` with a fallback to raw-string passthrough — the frontend chart code wants structured `data`, not a string.

### 3.3 Session store (`sessions.py`)

`SQLiteSession` stores message history but doesn't know "which sessions exist" as a user-facing concept. Keep a small metadata table (same SQLite techniques as Phase 1): `sessions(id TEXT PK, title TEXT, created_at, updated_at)`.

- `POST /api/sessions` inserts a row with a generated id (uuid4).
- On the first user message of a session, set `title` = first ~40 chars of the message.
- The stream endpoint constructs `SQLiteSession(session_id=id, db_path=SPENDLITE_SESSIONS_DB)` per request — cheap, correct, no caching needed.

### 3.4 History endpoint

`session.get_items()` returns model-input items (user messages, assistant messages, tool call/output records). Map to display shape: keep `user` and `assistant` text messages, drop tool plumbing (stretch: reconstruct tool chips from call items later). Return `[{role, content}]`.

### 3.5 CORS / dev wiring

In Phase 4, Vite's dev server proxies `/api` → `localhost:8000`, so **no CORS config is needed**. Skip `CORSMiddleware` entirely unless you choose not to use the proxy — fewer moving parts, and the prod topology (FastAPI serves the built frontend, same origin) needs none either.

## Pitfalls

- **Frame format is exactly `data: <json>\n\n`** — the blank line terminates the frame. Miss it and the client buffers forever, which looks identical to "backend is hanging."
- **Yield, don't return, on errors:** an exception inside a `StreamingResponse` generator after headers are sent can't become a 500 — the client just sees a dead socket. Catch inside the generator and emit the `error` event.
- **Don't `await` the whole run then stream** — the temptation when debugging. If first tokens arrive only when the answer is complete, you've buffered somewhere; test with `curl -N` early and often.
- **One event per frame.** Resist batching; the protocol's value is that each frame is independently parseable.

## GATE — curl is your Inspector now

With the MCP container/process up and the API running:

- [ ] `curl -s -X POST localhost:8000/api/sessions` → returns `{id, ...}`
- [ ] `curl -N -X POST localhost:8000/api/sessions/<id>/messages -H 'content-type: application/json' -d '{"message":"How much did I spend on food in June 2026?"}'` streams frames **live** (deltas arrive progressively, not in one burst)
- [ ] The stream contains `tool_call` **and** `tool_result` events, and the `get_category_summary`/`get_expenses` `tool_result.data` is parsed JSON (an array), not a string
- [ ] Off-topic message → single `guardrail_triggered` event, stream ends cleanly
- [ ] Ask a follow-up ("and transport?") on the same session id → memory works over HTTP
- [ ] `GET /api/sessions` lists the session with a title; `GET .../messages` returns readable history
- [ ] Stream always ends in exactly one terminal event (`done` / `guardrail_triggered` / `error`)

Everything the frontend will ever see, you have now seen raw in a terminal. Phase 4 bugs are frontend bugs — by construction.
