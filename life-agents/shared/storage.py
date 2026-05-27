"""SQLite-based persistent storage for life-agents."""
import sqlite3
import json
from datetime import datetime
from typing import Any, Optional
from shared.config import config


class Storage:
    """Simple key-value store backed by SQLite. Each 'category' is a table."""

    def __init__(self, db_name: str = "life_agents"):
        self.db_path = config.data_dir / f"{db_name}.db"
        self._tables: set[str] = set()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def ensure_table(self, category: str) -> None:
        if category in self._tables:
            return
        with self._connect() as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS [{category}] (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
        self._tables.add(category)

    def save(self, category: str, data: dict) -> int:
        """Save dict as JSON record, returns new id."""
        self.ensure_table(category)
        now = datetime.now().isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                f"INSERT INTO [{category}] (data, created_at, updated_at) VALUES (?, ?, ?)",
                (json.dumps(data, ensure_ascii=False), now, now)
            )
            return cur.lastrowid

    def load(self, category: str, id: int) -> Optional[dict]:
        """Load record by id, returns dict with 'id' field."""
        self.ensure_table(category)
        with self._connect() as conn:
            row = conn.execute(
                f"SELECT * FROM [{category}] WHERE id = ?", (id,)
            ).fetchone()
        if row is None:
            return None
        result = json.loads(row["data"])
        result["_id"] = row["id"]
        result["_created_at"] = row["created_at"]
        result["_updated_at"] = row["updated_at"]
        return result

    def list_all(self, category: str) -> list[dict]:
        """Return all records sorted by created_at descending."""
        self.ensure_table(category)
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM [{category}] ORDER BY created_at DESC"
            ).fetchall()
        results = []
        for row in rows:
            item = json.loads(row["data"])
            item["_id"] = row["id"]
            item["_created_at"] = row["created_at"]
            item["_updated_at"] = row["updated_at"]
            results.append(item)
        return results

    def update(self, category: str, id: int, data: dict) -> bool:
        """Update record by id. Returns True if found and updated."""
        self.ensure_table(category)
        now = datetime.now().isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                f"UPDATE [{category}] SET data = ?, updated_at = ? WHERE id = ?",
                (json.dumps(data, ensure_ascii=False), now, id)
            )
        return cur.rowcount > 0

    def delete(self, category: str, id: int) -> bool:
        """Delete record by id. Returns True if found."""
        self.ensure_table(category)
        with self._connect() as conn:
            cur = conn.execute(f"DELETE FROM [{category}] WHERE id = ?", (id,))
        return cur.rowcount > 0

    def count(self, category: str) -> int:
        """Return total record count for category."""
        self.ensure_table(category)
        with self._connect() as conn:
            row = conn.execute(f"SELECT COUNT(*) as n FROM [{category}]").fetchone()
        return row["n"]

    def search(self, category: str, field: str, value: str) -> list[dict]:
        """Search records where JSON field contains value (case-insensitive)."""
        all_records = self.list_all(category)
        value_lower = value.lower()
        results = []
        for item in all_records:
            field_val = str(item.get(field, "")).lower()
            if value_lower in field_val:
                results.append(item)
        return results

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a user setting by key."""
        results = self.search("user_settings", "key", key)
        for r in results:
            if r.get("key") == key:
                return r.get("value", default)
        return default

    def set_setting(self, key: str, value: Any) -> None:
        """Set a user setting by key (upsert)."""
        results = self.search("user_settings", "key", key)
        for r in results:
            if r.get("key") == key:
                self.update("user_settings", r["_id"], {"key": key, "value": value})
                return
        self.save("user_settings", {"key": key, "value": value})
