"""The SSE event protocol — the contract between this API and every client."""

from typing import Any, Literal

from pydantic import BaseModel


class Delta(BaseModel):
    type: Literal["delta"] = "delta"
    text: str


class ToolCall(BaseModel):
    type: Literal["tool_call"] = "tool_call"
    name: str
    call_id: str


class ToolResult(BaseModel):
    type: Literal["tool_result"] = "tool_result"
    name: str
    call_id: str
    data: Any


class GuardrailTriggered(BaseModel):
    type: Literal["guardrail_triggered"] = "guardrail_triggered"
    message: str


class Done(BaseModel):
    type: Literal["done"] = "done"
    session_id: str


class Error(BaseModel):
    type: Literal["error"] = "error"
    message: str


AgentEvent = Delta | ToolCall | ToolResult | GuardrailTriggered | Done | Error


def sse(event: AgentEvent) -> str:
    """Frame one event for the wire. The blank line terminates the frame."""
    return f"data: {event.model_dump_json()}\n\n"
