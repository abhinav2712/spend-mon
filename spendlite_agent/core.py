"""Agent factory. Imported by chat.py now and by spendlite_api in Phase 3."""

import os
from pathlib import Path

from agents import Agent, function_tool

## MCPServerStreamableHttp is a specialized MCP server that supports streaming responses over HTTP.
from agents.mcp import MCPServerStreamableHttp

from spendlite_agent.guardrail import expense_topic_guardrail
from spendlite_agent.model import build_model

INSTRUCTIONS_PATH = Path(__file__).with_name("instructions.txt")


## function_tool decorator is used to mark this function as a tool that the agent
#  can call to report progress to the user.
@function_tool
def report_progress(message: str) -> str:
    """Tell the user in one short phrase what you are about to look up.
    Call this before every expense lookup so the user sees progress."""
    print(f"\n[working] {message}", flush=True)
    return "acknowledged"


def build_mcp_server() -> MCPServerStreamableHttp:
    return MCPServerStreamableHttp(
        name="spendlite",
        params={"url": os.getenv("SPENDLITE_MCP_URL", "http://localhost:8010/mcp")},
        cache_tools_list=True,
        use_structured_content=True,
        client_session_timeout_seconds=15,
    )


def build_agent(mcp_server: MCPServerStreamableHttp) -> Agent:
    return Agent(
        name="SpendLiteAgent",
        instructions=INSTRUCTIONS_PATH.read_text(encoding="utf-8"),
        model=build_model(),
        # report_progress is deliberately unwired: Gemini's OpenAI-compat layer merges
        # the arguments of two tool calls emitted in the same turn, producing unparseable
        # JSON. With one tool call per turn, 5/5 runs succeed instead of 3/4.
        tools=[],
        mcp_servers=[mcp_server],
        input_guardrails=[expense_topic_guardrail],
    )
