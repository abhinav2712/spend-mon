"""Pydantic models: the contract the MCP tools advertise to any client."""

## Self Note: They validate your data and they become the JSON 
# Schema that FastMCP publishes to clients. Every description= 
# you write ends up in the tool schema an LLM reads (agent side)

import re

from pydantic import BaseModel, Field

MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class MonthInfo(BaseModel):
    month: str = Field(description="Calendar month in YYYY-MM form, e.g. 2026-06")
    expense_count: int = Field(
        description="Number of expense rows recorded in that month"
    )


class ExpenseRow(BaseModel):
    id: int
    spent_on: str = Field(description="ISO date the money was spent, YYYY-MM-DD")
    amount_inr: float = Field(description="Amount in Indian rupees")
    category: str
    merchant: str


class CategorySummary(BaseModel):
    category: str
    total_inr: float = Field(
        description="Sum of all spending in this category for the month"
    )
    count: int = Field(description="Number of expenses making up the total")
