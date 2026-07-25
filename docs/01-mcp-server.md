# Phase 1 — `spendlite_mcp`: the FastMCP server

**You are here:** Phase 1 of 5. Nothing exists yet. By the end of this phase a separate process owns your expense data and exposes it as typed tools over HTTP — and you'll have proven it works *without any LLM involved*.

## What you'll learn

- What MCP actually is: a protocol that lets tools live in a **different process** than the model, connected only by a URL. This is the core boundary idea of Con-Mon at the smallest scale.
- FastMCP's tool registration model, and why a tool's **docstring is a prompt**, not documentation.
- Pydantic validation as the line between "structured error the model can self-correct from" and "traceback that poisons the conversation."
- MCP Inspector as your LLM-free test harness.

## Build steps

### 1.1 Scaffold + seed (`seed.py`, `db.py`)

Create `spendlite_mcp/` with `requirements.txt` (`fastmcp`, `pydantic`).

`seed.py` spec:
- Creates `expenses.db` at `SPENDLITE_DB_PATH` (default `./expenses.db`) with the PRD §5.1 schema — keep the `CHECK (amount_inr > 0)` constraint.
- Inserts ~200 randomized rows across **March–June 2026**. Weight the randomness so data looks human: rent is 1 large payment/month, food is many small rows, subscriptions are the same few merchants at the same few prices.
- Categories: `food, transport, rent, shopping, subscriptions, health`. Merchants: pick 3–5 plausible ones per category (Swiggy, Uber, Amazon, DMart, Netflix, …).
- Ends by printing per-month row counts so seeding is verifiable at a glance.
- Must be **idempotent**: running it twice recreates the table rather than doubling rows (`DROP TABLE IF EXISTS` is fine here).

`db.py` spec:
- One function returning a `sqlite3` connection with `row_factory = sqlite3.Row` (dict-like rows → clean Pydantic construction).
- Query helpers used by the tools. **Parameterized queries only** — even in a toy, string-formatted SQL is a habit you don't want typed into muscle memory.

> **Why SQLite, why this schema:** the SQL is deliberately portable — when full Spend-Mon moves to Postgres, these queries move unchanged.

### 1.2 Schemas (`schemas.py`)

Pydantic models — these define both what the DB helpers return and what the MCP tool schemas advertise to any client:

```python
# shape, not full code
class MonthInfo(BaseModel):       # {month: "2026-06", expense_count: 57}
class ExpenseRow(BaseModel):      # id, spent_on, amount_inr, category, merchant
class CategorySummary(BaseModel): # {category, total_inr, count}
```

Month validation (used by `get_expenses` and `get_category_summary`):
- Must match `^\d{4}-(0[1-9]|1[0-2])$` **and** parse as a real month.
- Implement once — a validator or a small `validate_month(month: str)` helper the tools call.

### 1.3 Tools (`server.py`)

```python
# shape
from fastmcp import FastMCP
mcp = FastMCP("spendlite")

@mcp.tool
def get_available_months() -> list[MonthInfo]:
    """Return every month that has expense data, with row counts.
    Call this first to resolve 'latest' or 'last month'."""
    ...

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8010)
```

All four tools, per PRD §5.2:

| Tool | Inputs | Returns |
|------|--------|---------|
| `get_available_months` | — | `[{month, expense_count}]` |
| `list_categories` | — | `[category, ...]` derived from data (not hardcoded) |
| `get_expenses` | `month` (req), `category` (opt), `limit` (opt, default 20, max 100) | expense rows, newest first |
| `get_category_summary` | `month` (req) | `[{category, total_inr, count}]` |

Error behavior — this is the part that matters:
- Bad `month` → raise `ToolError` (from `fastmcp`) with a message stating the expected format and an example. FastMCP converts it into a structured tool error the client sees; a raw exception would be masked into a useless generic error.
- Unknown `category` → `ToolError` whose message **lists the valid categories**. That list is the model's self-correction path — it turns a dead end into a retry.

Docstring rules (every tool): one sentence on what it does, one on when to use it. You are writing the text the LLM reads when deciding which tool to call.

### 1.4 Run it

```bash
cd spend-mon && python spendlite_mcp/seed.py && python spendlite_mcp/server.py
```

Endpoint: `http://localhost:8010/mcp/`.

## Pitfalls

- **`0.0.0.0` vs `localhost`:** bind to `0.0.0.0` now — inside Docker later, `localhost` binding makes the port unreachable from outside the container. Same code both places is the goal.
- **Trailing slash (verified on FastMCP 3.4.4):** the canonical endpoint is `/mcp` — **no** trailing slash. `/mcp/` answers with a `307` redirect to `/mcp`. Well-behaved MCP clients follow it, but POST-with-body redirects are exactly the kind of thing an HTTP stack mishandles, so use the bare `/mcp` everywhere, env vars included. (FastMCP 2.x used `/mcp/`; the PRD predates the 3.x change.)
- **`run()` defaults will surprise you:** `host` defaults to `127.0.0.1` and `port` to `8000`. Pass both explicitly — `127.0.0.1` breaks Docker, and `8000` collides with the Phase 3 FastAPI server.
- **DB path is CWD-relative:** `./expenses.db` resolves against wherever you launched Python. Run from repo root consistently, or you'll seed one file and serve another — a classic "my data is empty" hour-waster.
- **`list_categories` from data, not a constant:** derive with `SELECT DISTINCT`. When you later add a category to the seed, the tool stays truthful automatically.

## GATE — MCP Inspector (do not write any agent code until every box ticks)

```bash
npx @modelcontextprotocol/inspector
# Transport: Streamable HTTP → URL: http://localhost:8010/mcp/
```

- [ ] Inspector connects and lists **all four tools** with correct input schemas
- [ ] `get_category_summary(month="2026-06")` returns real data
- [ ] `get_category_summary(month="2026-13")` returns the validation error message — **not** a crash or generic "internal error"
- [ ] `get_expenses(month="2026-06", category="nonsense")` returns an error that lists the valid categories
- [ ] `get_expenses` respects `limit` and caps at 100
- [ ] Cross-check one number: `sqlite3 expenses.db "SELECT SUM(amount_inr) FROM expenses WHERE category='food' AND spent_on LIKE '2026-06%'"` matches the tool's answer — write this number down; it's your ground truth for Phase 2's gate

This gate separates "my tools are broken" from "my agent is broken" **forever after**. It is never cut.
