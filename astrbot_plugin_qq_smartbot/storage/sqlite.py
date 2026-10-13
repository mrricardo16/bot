"""Local-only idempotency and candidate event storage; no message text."""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path


class EventStore:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS processed_messages (
                    dedup_key TEXT PRIMARY KEY, created_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dedup_key TEXT NOT NULL UNIQUE,
                    group_id TEXT NOT NULL, sender_id TEXT NOT NULL,
                    rule_id TEXT NOT NULL, event_type TEXT NOT NULL,
                    game TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'candidate',
                    created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL
                );
            """)

    def _db(self):
        return sqlite3.connect(self.db_path, timeout=5)

    def purge_expired(self, *, processed_retention_days: int = 7) -> None:
        now = int(time.time())
        with self._db() as db:
            db.execute("DELETE FROM processed_messages WHERE created_at < ?", (now - processed_retention_days * 86400,))
            db.execute("DELETE FROM candidates WHERE expires_at < ? AND status = 'candidate'", (now,))

    def claim(self, key: str) -> bool:
        with self._db() as db:
            result = db.execute("INSERT OR IGNORE INTO processed_messages VALUES (?, ?)", (key, int(time.time())))
            return result.rowcount == 1

    def capture(self, *, key: str, group_id: str, sender_id: str,
                rule_id: str, event_type: str, game: str, ttl_hours: int) -> bool:
        now = int(time.time())
        with self._db() as db:
            result = db.execute("""INSERT OR IGNORE INTO candidates
                (dedup_key, group_id, sender_id, rule_id, event_type, game, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (key, group_id, sender_id, rule_id, event_type, game, now, now + ttl_hours * 3600))
            return result.rowcount == 1
