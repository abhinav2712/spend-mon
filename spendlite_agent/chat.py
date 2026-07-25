"""Terminal chat loop — the Phase 2 gate. Proves the agent works before any web layer exists."""

## TODO: Understand this code

import argparse
import asyncio
import os
from datetime import datetime

from agents import InputGuardrailTripwireTriggered, Runner, SQLiteSession
from dotenv import load_dotenv
from openai.types.responses import ResponseTextDeltaEvent

from spendlite_agent.core import build_agent, build_mcp_server

REDIRECT = (
    "I can only help with your recorded expenses. Try asking about spending "
    "in a particular month, category, or merchant."
)

## run_turn is the main loop for a single turn of the chat. It takes the agent, session, and user input,
#  runs the agent, and prints the output to the terminal. It also handles guardrail tripwires and tool calls,
#  printing appropriate messages to the terminal.
async def run_turn(agent, session, user_input: str) -> None:
    result = Runner.run_streamed(agent, user_input, session=session)
    try:
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(
                event.data, ResponseTextDeltaEvent
            ):
                print(event.data.delta, end="", flush=True)
            elif (
                event.type == "run_item_stream_event"
                and event.item.type == "tool_call_item"
            ):
                print(f"\n[tool] {event.item.raw_item.name}", flush=True)
        print()
    except InputGuardrailTripwireTriggered:
        print(REDIRECT)


async def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("--new", action="store_true", help="start a fresh session")
    args = parser.parse_args()

    session_id = f"chat-{datetime.now():%Y%m%d-%H%M%S}" if args.new else "local_chat"
    session = SQLiteSession(
        session_id, os.getenv("SPENDLITE_SESSIONS_DB", "./sessions.db")
    )

    async with build_mcp_server() as mcp_server:
        agent = build_agent(mcp_server)
        print(f"SpendLite ready — session {session_id}. Ctrl-C to quit.\n")

        while True:
            try:
                user_input = input("you > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nbye")
                return
            if not user_input:
                continue
            print("bot > ", end="", flush=True)
            await run_turn(agent, session, user_input)


asyncio.run(main())
