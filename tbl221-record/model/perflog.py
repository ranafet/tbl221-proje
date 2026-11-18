from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PerfLog:
    """A single system resource measurement.

    Memory and disk values are stored in bytes; percentages are in the 0-100
    range. Timestamps are Unix seconds in UTC.
    """

    timestamp: int
    cpu_percent: float
    memory_used: int
    memory_total: int
    swap_used: int
    swap_total: int
    disk_used: int
    disk_total: int
    process_count: int
    load_1: float
    load_5: float
    load_15: float

    @classmethod
    def now(
        cls,
        *,
        cpu_percent: float,
        memory_used: int,
        memory_total: int,
        swap_used: int,
        swap_total: int,
        disk_used: int,
        disk_total: int,
        process_count: int,
        load_1: float,
        load_5: float,
        load_15: float,
    ) -> PerfLog:
        return cls(
            timestamp=int(time.time()),
            cpu_percent=cpu_percent,
            memory_used=memory_used,
            memory_total=memory_total,
            swap_used=swap_used,
            swap_total=swap_total,
            disk_used=disk_used,
            disk_total=disk_total,
            process_count=process_count,
            load_1=load_1,
            load_5=load_5,
            load_15=load_15,
        )

    @property
    def memory_percent(self) -> float:
        return self.memory_used * 100 / self.memory_total if self.memory_total else 0.0

    @property
    def swap_percent(self) -> float:
        return self.swap_used * 100 / self.swap_total if self.swap_total else 0.0

    @property
    def disk_percent(self) -> float:
        return self.disk_used * 100 / self.disk_total if self.disk_total else 0.0
