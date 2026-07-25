from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

import db
from schemas import MONTH_RE, CategorySummary, ExpenseRow, MonthInfo

mcp = FastMCP("spendlite")

Month = Annotated[
    str, Field(description="Month to report on, in YYYY-MM form, e.g. 2026-06")
]


def require_valid_month(month: str) -> str:
    if not MONTH_RE.match(month):
        raise ToolError(
            f"Invalid month {month!r}. Expected YYYY-MM with a month between 01 and 12, "
            f"for example 2026-06. Call get_available_months to see which months have data."
        )
    return month


def require_known_category(category: str) -> str:
    known = db.categories()
    if category not in known:
        raise ToolError(
            f"Unknown category {category!r}. Valid categories are: {', '.join(known)}."
        )
    return category


@mcp.tool
def get_available_months() -> list[MonthInfo]:
    """Return every month that has expense data, with the number of expenses in each.
    Call this first whenever the user says "latest", "last month", or "recently"."""
    return [MonthInfo(**dict(row)) for row in db.months()]


@mcp.tool
def list_categories() -> list[str]:
    """Return the spending categories that actually appear in the data.
    Call this to check a category name before filtering expenses by it."""
    return db.categories()


@mcp.tool
def get_expenses(
    month: Month,
    category: Annotated[
        str | None, Field(description="Optional category filter")
    ] = None,
    limit: Annotated[int, Field(description="Max rows to return", ge=1, le=100)] = 20,
) -> list[ExpenseRow]:
    """Return individual expense records for one month, newest first.
    Use this when the user asks about specific transactions or merchants."""
    require_valid_month(month)
    if category is not None:
        require_known_category(category)
    return [ExpenseRow(**dict(row)) for row in db.expenses(month, category, limit)]


@mcp.tool
def get_category_summary(month: Month) -> list[CategorySummary]:
    """Return total spending per category for one month, largest first.
    Use this for "how much did I spend on X" and for any monthly breakdown."""
    require_valid_month(month)
    return [CategorySummary(**dict(row)) for row in db.category_summary(month)]


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8010)
