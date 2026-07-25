"""Input guardrail: keep the conversation on the user's own spending."""

from functools import lru_cache

from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    Runner,
    input_guardrail,
)
from pydantic import BaseModel

from spendlite_agent.model import build_model

GUARDRAIL_INSTRUCTIONS = (
    "Decide whether the user's message belongs in a conversation about their own recorded "
    "expenses. You see only the current message, not the conversation it came from.\n"
    "On topic: amounts, categories, merchants, months, totals, budgets — and short follow-up "
    "fragments such as 'and transport?', 'what about May?', or 'top three' that only make "
    "sense as continuations of an expense question.\n"
    "Off topic: investment or financial advice, politics, news, general knowledge, and other "
    "unrelated subjects.\n"
    "If a message is ambiguous or very short, treat it as on topic."
)


## TopicCheck is the output type for the guardrail agent.
# It contains a boolean indicating whether the input is off-topic, and a reasoning string explaining the decision.
class TopicCheck(BaseModel):
    is_off_topic: bool
    reasoning: str

## lru_cache is used here to avoid rebuilding the agent on every call, which would be inefficient.
@lru_cache(maxsize=1)
def build_guardrail_agent() -> Agent:
    return Agent(
        name="TopicGuard",
        instructions=GUARDRAIL_INSTRUCTIONS,
        model=build_model(),
        output_type=TopicCheck,
    )

## input_guardrail decorator is used to mark this function as a guardrail that checks user input for
#  relevance to the user's own spending.
@input_guardrail
async def expense_topic_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    user_input,
) -> GuardrailFunctionOutput:
    result = await Runner.run(build_guardrail_agent(), user_input, context=ctx.context)
    check = result.final_output_as(TopicCheck)
    return GuardrailFunctionOutput(
        output_info=check, tripwire_triggered=check.is_off_topic
    )
