from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_DATABASE_PATH = "/var/lib/tbl221-record/tbl221-record.db"
DEFAULT_THRESHOLDS = {
    "cpu_percent": 85.0,
    "memory_percent": 85.0,
    "disk_percent": 90.0,
    "load_1": 8.0,
}


@dataclass(frozen=True, slots=True)
class Config:
    record_period: float = 5.0
    database_path: str = DEFAULT_DATABASE_PATH
    disk_path: str = "/"
    retention_days: int = 30
    thresholds: dict[str, float] = field(default_factory=lambda: DEFAULT_THRESHOLDS.copy())
    alert_cooldown: int = 300

    @classmethod
    def load(cls, path: str | None = None) -> "Config":
        requested = path or os.environ.get("TBL221_CONFIG", "/etc/tbl221-record.toml")
        config_path = Path(requested)
        data: dict[str, Any] = {}
        if config_path.is_file():
            with config_path.open("rb") as source:
                data = tomllib.load(source)
        thresholds = DEFAULT_THRESHOLDS | {
            key: float(value) for key, value in data.get("thresholds", {}).items()
        }
        alerts = data.get("alerts", {})
        return cls(
            record_period=max(0.1, float(data.get("record_period", 5))),
            database_path=str(data.get("database_path", DEFAULT_DATABASE_PATH)),
            disk_path=str(data.get("disk_path", "/")),
            retention_days=max(0, int(data.get("retention_days", 30))),
            thresholds=thresholds,
            alert_cooldown=max(0, int(alerts.get("cooldown_seconds", 300))),
        )
