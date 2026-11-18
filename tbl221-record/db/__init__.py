from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from model.perflog import PerfLog

READING_COLUMNS = (
    "timestamp, cpu_percent, memory_used, memory_total, swap_used, swap_total, "
    "disk_used, disk_total, process_count, load_1, load_5, load_15"
)


class Database:
    def __init__(self, path: str):
        self.path = path

    def connect(self) -> sqlite3.Connection:
        parent = Path(self.path).expanduser().parent
        parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=5000")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS readings (
                    id INTEGER PRIMARY KEY,
                    timestamp INTEGER NOT NULL,
                    cpu_percent REAL NOT NULL,
                    memory_used INTEGER NOT NULL,
                    memory_total INTEGER NOT NULL,
                    swap_used INTEGER NOT NULL,
                    swap_total INTEGER NOT NULL,
                    disk_used INTEGER NOT NULL,
                    disk_total INTEGER NOT NULL,
                    process_count INTEGER NOT NULL,
                    load_1 REAL NOT NULL,
                    load_5 REAL NOT NULL,
                    load_15 REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS readings_timestamp_idx ON readings(timestamp);
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY,
                    timestamp INTEGER NOT NULL,
                    metric TEXT NOT NULL,
                    value REAL NOT NULL,
                    threshold REAL NOT NULL,
                    message TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS alerts_timestamp_idx ON alerts(timestamp);
                """
            )

    def insert_reading(self, reading: PerfLog) -> None:
        values = tuple(getattr(reading, name.strip()) for name in READING_COLUMNS.split(","))
        placeholders = ", ".join("?" for _ in values)
        with self.connect() as connection:
            connection.execute(
                f"INSERT INTO readings ({READING_COLUMNS}) VALUES ({placeholders})", values
            )

    def insert_alert(self, timestamp: int, metric: str, value: float, threshold: float, message: str) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO alerts (timestamp, metric, value, threshold, message) VALUES (?, ?, ?, ?, ?)",
                (timestamp, metric, value, threshold, message),
            )

    def recent_readings(self, limit: int = 120) -> list[sqlite3.Row]:
        with self.connect() as connection:
            rows = connection.execute(
                f"SELECT {READING_COLUMNS} FROM readings ORDER BY timestamp DESC LIMIT ?", (limit,)
            ).fetchall()
        return list(reversed(rows))

    def recent_alerts(self, limit: int = 50) -> list[sqlite3.Row]:
        with self.connect() as connection:
            return connection.execute(
                "SELECT timestamp, metric, value, threshold, message FROM alerts ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()

    def prune(self, retention_days: int) -> None:
        if retention_days <= 0:
            return
        cutoff = int(time.time()) - retention_days * 86400
        with self.connect() as connection:
            connection.execute("DELETE FROM readings WHERE timestamp < ?", (cutoff,))
            connection.execute("DELETE FROM alerts WHERE timestamp < ?", (cutoff,))


# Compatibility functions for the original module API.
_DEFAULT_PATH = "/var/lib/tbl221-record/tbl221-record.db"


def initialize_db(path: str = _DEFAULT_PATH) -> None:
    Database(path).initialize()


def insert_perfcount(perf_log: PerfLog, path: str = _DEFAULT_PATH) -> None:
    Database(path).insert_reading(perf_log)


def get_performance_readings(path: str = _DEFAULT_PATH) -> list[PerfLog]:
    return [PerfLog(**dict(row)) for row in Database(path).recent_readings(10000)]
