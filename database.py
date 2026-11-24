import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "iftar_menu.db"

ALLOWED_CATEGORIES = (
    "Main Dish",
    "Soup",
    "Appetizer",
    "Side Dish",
    "Dessert",
    "Beverage",
)

SAMPLE_DISHES = [
    ("Lamb Kabsa", "Main Dish", 85.00, 6),
    ("Lentil Soup", "Soup", 18.50, 6),
    ("Cheese Sambosa", "Appetizer", 24.00, 6),
    ("Fattoush Salad", "Side Dish", 20.00, 4),
    ("Kunafa", "Dessert", 35.00, 6),
    ("Vimto & Laban", "Beverage", 22.00, 6),
]


class MenuDatabase:
    """Manages SQLite persistence for Iftar Menu Planner records."""

    def __init__(self, db_path=DB_PATH):
        self.db_path = str(db_path)

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self, seed_if_empty=True):
        """Creates the dishes table if missing and preserves existing records."""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS dishes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    cost REAL NOT NULL,
                    servings INTEGER NOT NULL
                )
                """
            )
            if seed_if_empty:
                cursor.execute("SELECT COUNT(*) AS count FROM dishes")
                row = cursor.fetchone()
                if row and row["count"] == 0:
                    cursor.executemany(
                        """
                        INSERT INTO dishes (name, category, cost, servings)
                        VALUES (?, ?, ?, ?)
                        """,
                        SAMPLE_DISHES,
                    )
            conn.commit()
        finally:
            conn.close()

    def get_dishes(self, category=None):
        """Returns a list of dish dictionaries, optionally filtered by category."""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            if category and category != "All":
                cursor.execute(
                    """
                    SELECT id, name, category, cost, servings
                    FROM dishes
                    WHERE category = ?
                    ORDER BY id ASC
                    """,
                    (category,),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, name, category, cost, servings
                    FROM dishes
                    ORDER BY id ASC
                    """
                )
            rows = cursor.fetchall()
            dishes = []
            for row in rows:
                dishes.append(
                    {
                        "id": row["id"],
                        "name": row["name"],
                        "category": row["category"],
                        "cost": round(float(row["cost"]), 2),
                        "servings": int(row["servings"]),
                    }
                )
            return dishes
        finally:
            conn.close()

    def add_dish(self, name, category, cost, servings):
        """Inserts a new dish record and returns the created dictionary."""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO dishes (name, category, cost, servings)
                VALUES (?, ?, ?, ?)
                """,
                (name, category, cost, servings),
            )
            conn.commit()
            new_id = cursor.lastrowid
            return {
                "id": new_id,
                "name": name,
                "category": category,
                "cost": round(float(cost), 2),
                "servings": int(servings),
            }
        finally:
            conn.close()

    def update_dish(self, dish_id, name, category, cost, servings):
        """Updates an existing dish by ID. Returns True if updated, False if ID not found."""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE dishes
                SET name = ?, category = ?, cost = ?, servings = ?
                WHERE id = ?
                """,
                (name, category, cost, servings, dish_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def delete_dish(self, dish_id):
        """Deletes a dish by ID. Returns True if deleted, False if ID not found."""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM dishes WHERE id = ?", (dish_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
