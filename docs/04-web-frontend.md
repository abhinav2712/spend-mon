# Phase 4 — `spendlite_web`: the React chat UI

**You are here:** Phase 4 of 5. The backend streams a typed event protocol you've already watched raw with curl. This phase turns that stream into UI, in four sub-phases with mini-gates — **A: streaming + tool chips → B: markdown + tables → C: session sidebar → D: charts**. Each sub-phase is demoable on its own; if you stall, you still have a working app at the last passed gate.

## What you'll learn

- Consuming an SSE stream in the browser with `fetch` + `ReadableStream` (and why `EventSource` couldn't do this job — it can't POST).
- **Reducing an event stream into UI state** — the same normalized events, now driving React instead of a terminal.
- Streaming-friendly markdown rendering, and charts driven deterministically by `tool_result` events.

## Setup

```bash
npm create vite@latest spendlite_web -- --template react-ts
npm i react-markdown remark-gfm recharts
# + Tailwind (follow current Vite guide)
```

- **TypeScript deliberately:** you'll mirror the backend's event protocol as a TS union type — typed events on both ends of the wire.
- `vite.config.ts`: proxy `/api` → `http://localhost:8000` (this is why the backend needs no CORS).

## The two core modules (build these before any components)

### `src/lib/events.ts` — the protocol, mirrored

```ts
// shape — one interface per backend event type, discriminated on `type`
type AgentEvent =
  | { type: "delta"; text: string }
  | { type: "tool_call"; name: string; call_id: string }
  | { type: "tool_result"; name: string; call_id: string; data: unknown }
  | { type: "guardrail_triggered"; message: string }
  | { type: "done"; session_id: string }
  | { type: "error"; message: string };
```

If the backend protocol changes, this file is the only place the frontend notices. That locality is the payoff of Phase 3's normalization.

### `src/lib/stream.ts` — the SSE reader

```ts
// shape
async function* streamChat(sessionId: string, message: string): AsyncGenerator<AgentEvent>
// fetch POST → res.body.getReader() → TextDecoder → accumulate a buffer →
// split on "\n\n" → for each complete frame, strip "data: " → JSON.parse → yield
```

The subtle part: a network chunk can end mid-frame. Keep the trailing partial in the buffer and only parse complete frames — this is the frontend twin of the delimited-events lesson from learnings.md.

## State model (decide before writing components)

```ts
// shape
type ToolActivity = { callId: string; name: string; data?: unknown; status: "running" | "done" };
type ChatMessage =
  | { role: "user"; content: string }
  | { role: "assistant"; content: string; tools: ToolActivity[]; streaming: boolean };
```

One reducer/handler consumes `AgentEvent`s: `delta` appends to the last assistant message; `tool_call` appends a running `ToolActivity`; `tool_result` completes it (matched by `call_id`) and attaches `data`; terminal events flip `streaming` off. Tool activities living **inside the message** (not in separate state) means chips and charts render in-place in the transcript, and history "just works."

## Sub-phases

### A — Streaming chat + tool chips

Components: `App` → `ChatWindow` → (`MessageList` → `MessageBubble` → `ToolChip`) + `Composer`.

- Send on submit → append user message + empty streaming assistant message → `for await` over `streamChat(...)` feeding the reducer.
- `ToolChip`: small pill per `ToolActivity` — spinner while `running` ("calling get_expenses…"), check when `done`. This is the web version of your `[tool]` lines — the demo beat that says *the model is calling remote tools right now*.
- `guardrail_triggered` renders as a distinct quiet style (not an error — the system working as designed).
- Auto-scroll to bottom on new content (a `ref` + `scrollIntoView` effect is enough).

**Mini-gate A:** deltas visibly stream; chips appear before answer text references their data; guardrail message styled distinctly; input disabled while `streaming`.

### B — Markdown + tables

- Assistant `content` renders through `react-markdown` + `remark-gfm` (GFM = tables).
- Nudge the agent: add one line to `instructions.txt` — "format lists of expenses as markdown tables." (Yes, the instructions file is now part of your UI stack. Sit with that for a second — it's the strangest true thing about agent products.)
- Style tables: right-align the ₹ column, subtle row borders, `overflow-x-auto` wrapper.

**Mini-gate B:** "Show my top 10 expenses for June 2026" renders as an actual table; ₹ amounts right-aligned; no raw `|---|` pipes visible.

### C — Session sidebar

Components: `Sidebar` (session list + "New chat") beside `ChatWindow`.

- On load: `GET /api/sessions` → list, newest first; auto-select most recent or create one.
- Select session → `GET /api/sessions/{id}/messages` → hydrate transcript (historical messages have `tools: []`, `streaming: false` — your state model already handles them).
- "New chat" → `POST /api/sessions` → select it. After a session's first message, refetch the list so its title appears.

**Mini-gate C:** the June/food conversation continues after a full page reload — this is `SQLiteSession` memory made visible, the web `--new` equivalent one click away.

### D — Charts (typed-SSE-event pattern, per decision #5)

- `ChartBlock` component: when a `ToolActivity` with `name === "get_category_summary"` completes, render a **horizontal bar chart** (Recharts) of `total_inr` by category, sorted descending, below the chips — categorical comparison, ₹-formatted axis/tooltips, one muted accent color. Validate `data` at runtime before rendering (`Array.isArray`, expected keys) — the wire is typed by convention, not enforcement.
- Optionally also chart `get_available_months` (counts by month) — same component pattern, ~20 minutes.
- **Ordering caveat:** the `tool_result` event usually arrives *before* the text that discusses it, so the chart naturally appears above the prose. That's good UX — leave it.

**Mini-gate D:** "Break down my June 2026 spending by category" → chart renders every time (deterministic — that was the whole argument for this wiring); numbers match the table/text; no chart appears for `get_expenses` calls.

> **Stretch (from decision #5):** afterwards, add an agent-driven `show_chart` tool + `chart` event type and feel the difference: the chart now appears at the model's discretion. Being able to articulate why production systems mostly pick the deterministic path is a senior-engineer talking point.

## Pitfalls

- **Don't start streams in `useEffect`.** Kick off `streamChat` from the submit handler. React StrictMode double-invokes effects in dev — an effect-started stream fires twice, and you'll chase a "double answer" ghost for an hour.
- **State updates during rapid deltas:** always use functional updates (`setMessages(prev => ...)`); stale-closure appends silently drop tokens.
- **Frame parsing:** if the UI shows nothing but curl works, log raw chunks first — it's almost always the partial-frame buffer, not React.
- **`react-markdown` re-renders per delta** — fine at this scale; resist optimizing until it's actually janky.
- **Keys:** index keys are fine for an append-only transcript; use `call_id` for tool activities.

## GATE — full browser UX

- [ ] All four mini-gates (A–D) pass in one continuous session
- [ ] Phase 2's seven terminal acceptance behaviors all reproduce in the browser
- [ ] Refresh mid-conversation → history intact, no duplicate messages
- [ ] Two rapid-fire questions don't interleave streams (input stays disabled while streaming)
- [ ] It looks like something you'd *choose* to demo — spacing, alignment, and the chart earn the phrase "good UI"
