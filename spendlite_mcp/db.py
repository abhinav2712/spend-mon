"""SQLite access layer. Every query the MCP tools run lives here."""

import os
import sqlite3
from contextlib import closing

DB_PATH = os.getenv("SPENDLITE_DB_PATH", "./expenses.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row 
    return conn


def query(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    with closing(connect()) as conn:
        return conn.execute(sql, params).fetchall()


def months() -> list[sqlite3.Row]:
    return query(
        "SELECT substr(spent_on, 1, 7) AS month, COUNT(*) AS expense_count "
        "FROM expenses GROUP BY month ORDER BY month"
    )


def categories() -> list[str]:
    rows = query("SELECT DISTINCT category FROM expenses ORDER BY category")
    return [row["category"] for row in rows]


def expenses(month: str, category: str | None, limit: int) -> list[sqlite3.Row]:
    sql = (
        "SELECT id, spent_on, amount_inr, category, merchant "
        "FROM expenses WHERE substr(spent_on, 1, 7) = ?"
    )
    params: list = [month]
    if category:
        sql += " AND category = ?"
        params.append(category)
    sql += " ORDER BY spent_on DESC, id DESC LIMIT ?"
    params.append(limit)
    return query(sql, tuple(params))


def category_summary(month: str) -> list[sqlite3.Row]:
    return query(
        "SELECT category, ROUND(SUM(amount_inr), 2) AS total_inr, COUNT(*) AS count "
        "FROM expenses WHERE substr(spent_on, 1, 7) = ? "
        "GROUP BY category ORDER BY total_inr DESC",
        (month,),
    )
