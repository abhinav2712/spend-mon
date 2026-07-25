"""Generate ( mock testing) expenses.db with ~190 rows of plausible spending, March–June 2026."""

import calendar
import os
import random
import sqlite3

DB_PATH = os.getenv("SPENDLITE_DB_PATH", "./expenses.db")

random.seed(
    27
)  # reproducible: re-seeding gives the same numbers to cross-check against

SCHEMA = """
DROP TABLE IF EXISTS expenses;
CREATE TABLE expenses (
    id         INTEGER PRIMARY KEY,
    spent_on   TEXT NOT NULL,
    amount_inr REAL NOT NULL CHECK (amount_inr > 0),
    category   TEXT NOT NULL,
    merchant   TEXT NOT NULL
);
CREATE INDEX idx_expenses_spent_on ON expenses (spent_on);
"""

MONTHS = [(2026, 3), (2026, 4), (2026, 5), (2026, 6)]

# category -> (merchants, min amount, max amount, rows per month)
PROFILE = {
    "food": (
        ["Swiggy", "Zomato", "Blue Tokai", "Third Wave Coffee", "Rameshwaram Cafe"],
        120,
        850,
        (20, 28),
    ),
    "transport": (["Uber", "Ola", "Rapido", "Indian Oil"], 60, 700, (8, 12)),
    "shopping": (["Amazon", "DMart", "Myntra", "IKEA"], 400, 6000, (4, 7)),
    "health": (["Apollo Pharmacy", "PharmEasy", "Cult.fit"], 200, 2500, (1, 3)),
}

SUBSCRIPTIONS = [
    ("Netflix", 649.0),
    ("Spotify", 119.0),
    ("Amazon Prime", 179.0),
    ("iCloud+", 75.0),
]


def generate_rows() -> list[tuple]:
    rows = []
    for year, month in MONTHS:
        last_day = calendar.monthrange(year, month)[1]

        def day(lo: int = 1, hi: int = last_day) -> str:
            return f"{year:04d}-{month:02d}-{random.randint(lo, hi):02d}"

        # Rent: one large payment early in the month.
        rows.append(
            (day(1, 5), round(random.uniform(28000, 32000), 2), "rent", "NoBroker Pay")
        )

        # Subscriptions: same merchants at the same prices every month.
        for merchant, amount in SUBSCRIPTIONS:
            rows.append((day(1, 12), amount, "subscriptions", merchant))

        # Everything else: many smaller, randomized rows.
        for category, (merchants, low, high, count_range) in PROFILE.items():
            for _ in range(random.randint(*count_range)):
                rows.append(
                    (
                        day(),
                        round(random.uniform(low, high), 2),
                        category,
                        random.choice(merchants),
                    )
                )

    return rows


def main() -> None:
    rows = generate_rows()

    conn = sqlite3.connect(DB_PATH)
    with conn:
        conn.executescript(SCHEMA)
        conn.executemany(
            "INSERT INTO expenses (spent_on, amount_inr, category, merchant) VALUES (?, ?, ?, ?)",
            rows,
        )
        summary = conn.execute(
            "SELECT substr(spent_on, 1, 7) AS month, COUNT(*), ROUND(SUM(amount_inr)) "
            "FROM expenses GROUP BY 1 ORDER BY 1"
        ).fetchall()
    conn.close()

    print(f"Seeded {len(rows)} rows into {DB_PATH}")
    for month, count, total in summary:
        print(f"  {month}: {count:3d} rows, {total:,.0f} INR")


if __name__ == "__main__":
    main()
