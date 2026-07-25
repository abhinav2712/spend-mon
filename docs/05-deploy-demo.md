# Phase 5 — Deploy + demo: compose, EC2 stretch, and the 5-minute script

**You are here:** Phase 5 of 5. Everything works via `npm run dev` + two Python processes. This phase packages it so the demo is `docker compose up` → open a browser — and rehearses the story you'll tell over it.

## What you'll learn

- Multi-stage Docker builds (Node build stage feeding a Python runtime stage).
- Container networking: services addressing each other by name, and **which ports deserve to exist on the host at all**.
- Env-based config paying off: the same images run on a laptop or EC2 with only env values changing.

## Target topology

```text
docker compose
├── spendlite-mcp   (internal only — no host port needed once integrated)
│     └── expenses.db baked in at build (fine for a demo)
└── spendlite-api   (host port 8000)
      ├── runs FastAPI + agent (imports spendlite_agent)
      ├── serves spendlite_web/dist as static files
      └── talks to MCP at http://spendlite-mcp:8010/mcp/  ← service name, not localhost
```

> **The PRD's asymmetry, revisited:** the agent stayed on the host only because a terminal needs stdin. The web UI dissolved that reason — now the agent containerizes too. But keep MCP a **separate service**: the process boundary is the lesson, and compose's internal network demonstrates something better than port 8010 ever did — *the tool API doesn't need host exposure at all*. An MCP port you don't publish is an MCP port nobody can probe.

## Build steps

### 5.1 `spendlite_mcp/Dockerfile`

Per PRD §8.1, unchanged: `python:3.12-slim`, install requirements, copy code, `RUN python seed.py` (bake the DB — fine for a demo, and say so), `EXPOSE 8010`, run `server.py`.

### 5.2 `spendlite_api/Dockerfile` (multi-stage)

```dockerfile
# shape
# Stage 1 "web": node:22-slim → copy spendlite_web → npm ci && npm run build
# Stage 2:       python:3.12-slim → pip install api+agent requirements
#                → copy spendlite_api/ and spendlite_agent/
#                → COPY --from=web /app/spendlite_web/dist ./static
#                → uvicorn spendlite_api.main:app --host 0.0.0.0 --port 8000
```

- Build context must be the **repo root** (the image needs `spendlite_agent/` too) — set `build: {context: ., dockerfile: spendlite_api/Dockerfile}` in compose.
- In `main.py`, mount `StaticFiles(directory=..., html=True)` at `/` **after** the `/api` routes, only when the directory exists — dev mode (Vite proxy) stays unchanged.

### 5.3 `docker-compose.yml`

- `spendlite-mcp`: build + healthcheck per PRD §8.1. During development keep `ports: ["8010:8010"]` (Inspector needs it); comment it out for the pure demo topology and mention that in the demo.
- `spendlite-api`: `ports: ["8000:8000"]`, `env_file: .env`, `SPENDLITE_MCP_URL=http://spendlite-mcp:8010/mcp/`, `depends_on: {spendlite-mcp: {condition: service_healthy}}`.
- Session persistence across restarts: volume-mount a data dir for `sessions.db` (or accept fresh sessions per `up` — decide consciously, it's a demo beat either way).

### 5.4 EC2 stretch (optional, per decision #8)

Same as PRD §8.2, upgraded from "MCP only" to the whole stack: t3.micro Ubuntu, install docker + compose plugin, clone, add `.env` (never commit the key), `docker compose up -d`. Security group: **port 8000 only, only from your IP** — 8010 stays unpublished, so there's nothing else to protect. Open `http://<ec2-ip>:8000` from the laptop. Demo line: *"same images, one env file changed."* Tear it down after.

## Pitfalls

- `localhost` **inside a container is that container.** The #1 compose bug: API pointing at `localhost:8010` instead of `spendlite-mcp:8010`. If Phase 3 worked and compose doesn't, it's this.
- `.dockerignore` at repo root: `node_modules`, `dist`, `.env`, `*.db`, `.git` — or the API image build context uploads half a gigabyte and bakes your sessions in.
- **SPA fallback:** `StaticFiles(html=True)` serves `index.html` at `/` but 404s unknown paths; fine for this app (no client-side routes). If you add routes later, you need a catch-all.
- **Healthcheck honesty:** PRD's urllib check hits `/mcp/` — a redirect/405 still proves the server is up, which is all a demo healthcheck needs. Know that's what it proves.

## GATE — final acceptance (the demo *is* the test)

- [ ] From a clean checkout + `.env`: `docker compose up --build` → healthy → `http://localhost:8000` serves the full app

- [ ] Phase 4's browser gate passes against the containerized stack

- [ ] `docker compose exec` or logs show the API resolving MCP by service name

- [ ] Frontend was **not rebuilt or edited** between dev and compose — only env/config changed

- [ ] Demo script below rehearsed once, under 5 minutes, timer running

## The 5-minute demo script

1. **(30s)** `docker compose up` already running; show `docker compose ps` healthy. *"Three processes: data tools, agent+API, and a browser. Each boundary is a protocol I can show you raw."*
2. **(60s)** MCP Inspector (with 8010 temporarily published) → list tools → call `get_category_summary(month="2026-06")` → then `month="2026-13"` for the structured error. *"This process owns the data. No model involved yet. Bad input gets an error the model can self-correct from."*
3. **(30s)** `curl -N` one chat message → typed SSE frames scroll by. *"The agent's run normalized into a stable event protocol — deltas, tool calls, tool results. The frontend only knows these six event types. This is the Con-Mon run-stream idea at demo scale."*
4. **(90s)** Browser: ask "How much did I spend on food in June 2026?" → point at tool chips, streaming text, the ₹ total. Follow with "and transport?" → session memory. Refresh the page → history intact.
5. **(45s)** "Break down June by category" → chart renders. *"Deterministic — driven by the tool result event, not model whim."* Then "Should I invest in stocks?" → guardrail redirect, and note it ran in parallel with the main call.
6. **(30s)** Close: *"Milestone 0 and 1 of Spend-Mon, merged. Next: Postgres, auth, and multi-user sessions — and I'd like to pick up a small Con-Mon task when there's one going."*