"""Gemini wired through OpenAI-compatible packages. One factory, shared by every agent."""

import os

from agents import OpenAIChatCompletionsModel, set_tracing_disabled
from openai import AsyncOpenAI

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

# The SDK ships traces to OpenAI's backend by default, and we have no OpenAI key.
set_tracing_disabled(True)


def build_model() -> OpenAIChatCompletionsModel:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set — check your .env file.")

    client = AsyncOpenAI(api_key=api_key, base_url=GEMINI_BASE_URL)
    return OpenAIChatCompletionsModel(
        model=os.getenv("SPENDLITE_MODEL", "gemini-2.5-flash"),
        openai_client=client,
    )
