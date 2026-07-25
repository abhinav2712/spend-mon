# Phase 2 — `spendlite_agent`: agent core + terminal chat

**You are here:** Phase 2 of 5. The MCP server passed the Inspector gate, so tools are proven. Now a model gets to use them. Everything built here — the agent factory, guardrail, instructions — is **reused unchanged by the web backend in Phase 3**; only the terminal loop is phase-specific.

## What you'll learn

- The Agents SDK anatomy: an `Agent` is configuration (instructions + model + tools); a `Runner` executes the loop of model → tool call → tool result → model until a final answer.
- Running **Gemini through OpenAI packages** — the OpenAI-compatible endpoint trick that makes the SDK provider-agnostic.
- The SDK's **typed stream events** — the real version of the hand-rolled delimited events from learnings.md §4.
- Local function tools vs remote MCP tools, side by side in one agent.
- Guardrails with structured output, and why the SDK running them **in parallel** with the main run is a latency win.
- `SQLiteSession` as conversational memory that survives restarts.

## Build steps

### 2.1 Model wiring (`model.py`)

Per PRD §6.1 — `AsyncOpenAI` client pointed at Gemini's OpenAI-compatible `base_url`, wrapped in `OpenAIChatCompletionsModel`, with `set_tracing_disabled(True)` (no OpenAI key → the SDK's tracing backend would error).

One shared `build_model()` used by **both** the main agent and the guardrail agent. Model name from `SPENDLITE_MODEL` env var, not hardcoded.

### 2.2 Agent factory (`core.py`) — the key structural decision

Do **not** define the agent inside `chat.py`. Put it in `core.py`:

```python
# shape
def build_mcp_server() -> MCPServerStreamableHttp:
    # MCPServerStreamableHttp(params={"url": os.environ["SPENDLITE_MCP_URL"]})

def build_agent(mcp_server) -> Agent:
    # Agent(name="SpendLiteAgent",
    #       instructions=<read instructions.txt>,
    #       model=build_model(),
    #       tools=[report_progress],
    #       mcp_servers=[mcp_server],
    #       input_guardrails=[expense_topic_guardrail])
```

In Phase 3, `spendlite_api` imports these two functions and the terminal loop is simply bypassed. If you skip this refactor now, you'll do it under pressure later.

`report_progress(message: str)` — a `@function_tool` that prints `[working] {message}` and returns a short ack. It exists to keep the **local tool vs remote MCP tool** distinction alive in one codebase: same agent, two tool sources, only one crosses a process boundary.

### 2.3 Instructions (`instructions.txt`)

Required content, per PRD §6.3 — write these as numbered rules:
1. Answer **only** from tool results; never estimate amounts or invent merchants.
2. For "latest" / "last month" / "recently": call `get_available_months` first and use real months from its reply.
3. Refuse write requests, forecasting, and investment advice; state briefly what *is* supported.
4. Always name the month(s) an answer covers; format amounts as ₹ with Indian digit grouping.
5. Call `report_progress` before looking anything up.
6. Never mention tools, MCP, schemas, or JSON to the user.

> **Why rule 2 matters most:** it's the difference between a grounded agent and a plausible-sounding liar. Your Phase 2 gate tests it directly.

### 2.4 Streaming chat loop (`chat.py`)

Structure: `async def main()` under `asyncio.run(main())` — no top-level await. Open the MCP server as an async context manager around the whole loop (connect once, not per turn). Per turn:

```python
# shape — the typed-event pattern from learnings.md §4, SDK edition
result = Runner.run_streamed(agent, user_input, session=session)
async for event in result.stream_events():
    # raw_response_event + ResponseTextDeltaEvent → print(delta, end="", flush=True)
    # run_item_stream_event + item.type == "tool_call_item" → print(f"\n[tool] {name}")
```

### 2.5 Session memory

`SQLiteSession(session_id="local_chat", db_path=SPENDLITE_SESSIONS_DB)` passed to every `run_streamed` call. Add a `--new` flag that generates a fresh session id (timestamp is fine). Behavior to hit: "how much on food in June?" → "and transport?" works without restating the month; restarting `chat.py` resumes context.

### 2.6 Input guardrail (`guardrail.py`)

```python
# shape
class TopicCheck(BaseModel):
    is_off_topic: bool
    reasoning: str
```

A small guardrail agent (same `build_model()`, `output_type=TopicCheck`, 2–3 line instructions: "classify whether this is about personal expenses/spending") wrapped with `@input_guardrail`, returning `GuardrailFunctionOutput(tripwire_triggered=check.is_off_topic, output_info=check)`. The chat loop catches `InputGuardrailTripwireTriggered` and prints a polite redirect.

> **Demo talking point:** unlike a sequential pre-check, the SDK runs the guardrail **in parallel** with the main run and cancels on tripwire — you pay ~zero added latency for on-topic messages.

## Pitfalls

- **Free-tier rate limits:** the guardrail means **~2 Gemini calls per turn** (plus extra turns of the agent loop for tool calls). Gemini Flash free tier is in the ~10-requests-per-minute class — rapid-fire testing will hit 429s. When you see one, wait a minute; don't "fix" working code.
- **`flush=True` on every delta print** — without it, output buffers and streaming looks broken even when it isn't.
- **Tool-call event names:** for MCP tools, the tool name lives on the tool-call item's `raw_item`. Print `event.item.raw_item.name` defensively (attribute may differ between local and MCP tools — inspect one event object with `print(type(...))` the first time rather than guessing).
- **Guardrail exceptions during streaming** surface while iterating `stream_events()` — put the `try/except InputGuardrailTripwireTriggered` around the async-for, not just around the `run_streamed` call.
- **Don't reconnect the MCP server every turn** — context-manage it once around the loop. Per-turn reconnects work but teach you the wrong shape for Phase 3.

## GATE — terminal acceptance (all seven, in one sitting)

- [ ] Answers stream token-by-token, with `[working]` (local tool) and `[tool]` (remote MCP) lines visible
- [ ] "How much did I spend on food in June 2026?" → matches the SQL number you wrote down in Phase 1's gate
- [ ] "What's my latest month?" → visibly calls `get_available_months`; never guesses
- [ ] Follow-up "and transport?" works via session memory
- [ ] Restart `chat.py` → context resumes; `--new` → clean slate
- [ ] "Should I invest in stocks?" → guardrail redirect, not an answer
- [ ] "Add ₹500 chai expense" → refused per instructions (and no write tool exists — defense in two layers)

When all seven pass, the agent is *done* — Phases 3–4 change how you talk to it, not what it is.
