from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from model.perflog import PerfLog


@dataclass(frozen=True, slots=True)
class CpuTimes:
    idle: int
    total: int


def parse_cpu_times(line: str) -> CpuTimes:
    fields = line.split()
    if not fields or fields[0] != "cpu" or len(fields) < 5:
        raise ValueError("invalid aggregate CPU line")
    values = [int(value) for value in fields[1:]]
    idle = values[3] + (values[4] if len(values) > 4 else 0)
    return CpuTimes(idle=idle, total=sum(values))


def read_cpu_times(proc_root: str | Path = "/proc") -> CpuTimes:
    with Path(proc_root, "stat").open(encoding="utf-8") as source:
        line = source.readline()
    return parse_cpu_times(line)


def cpu_percent(previous: CpuTimes, current: CpuTimes) -> float:
    total_delta = current.total - previous.total
    idle_delta = current.idle - previous.idle
    if total_delta <= 0:
        return 0.0
    return max(0.0, min(100.0, (total_delta - idle_delta) * 100.0 / total_delta))


def parse_meminfo(text: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for line in text.splitlines():
        key, separator, value = line.partition(":")
        if not separator:
            continue
        parts = value.split()
        if not parts:
            continue
        multiplier = 1024 if len(parts) > 1 and parts[1].lower() == "kb" else 1
        result[key] = int(parts[0]) * multiplier
    return result


def read_memory(proc_root: str | Path = "/proc") -> Mapping[str, int]:
    text = Path(proc_root, "meminfo").read_text(encoding="utf-8")
    values = parse_meminfo(text)
    total = values.get("MemTotal", 0)
    available = values.get("MemAvailable", values.get("MemFree", 0))
    swap_total = values.get("SwapTotal", 0)
    swap_free = values.get("SwapFree", 0)
    return {
        "memory_total": total,
        "memory_used": max(0, total - available),
        "swap_total": swap_total,
        "swap_used": max(0, swap_total - swap_free),
    }


def count_processes(proc_root: str | Path = "/proc") -> int:
    return sum(entry.name.isdigit() and entry.is_dir() for entry in Path(proc_root).iterdir())


def collect(previous_cpu: CpuTimes, disk_path: str = "/", proc_root: str | Path = "/proc") -> tuple[PerfLog, CpuTimes]:
    current_cpu = read_cpu_times(proc_root)
    memory = read_memory(proc_root)
    disk = shutil.disk_usage(disk_path)
    try:
        load_1, load_5, load_15 = os.getloadavg()
    except OSError:
        load_1 = load_5 = load_15 = 0.0

    reading = PerfLog.now(
        cpu_percent=cpu_percent(previous_cpu, current_cpu),
        memory_used=memory["memory_used"],
        memory_total=memory["memory_total"],
        swap_used=memory["swap_used"],
        swap_total=memory["swap_total"],
        disk_used=disk.used,
        disk_total=disk.total,
        process_count=count_processes(proc_root),
        load_1=load_1,
        load_5=load_5,
        load_15=load_15,
    )
    return reading, current_cpu


# Backward-compatible helpers retained for simple interactive use.
def read_current_cpu_usage() -> float:
    first = read_cpu_times()
    second = read_cpu_times()
    return cpu_percent(first, second)


def read_current_mem_usage() -> int:
    return int(read_memory()["memory_used"])


def read_current_swap_usage() -> int:
    return int(read_memory()["swap_used"])


def read_current_total_mem_usage() -> int:
    memory = read_memory()
    return int(memory["memory_used"] + memory["swap_used"])


def read_maxmem() -> int:
    return int(read_memory()["memory_total"])


def read_maxswap() -> int:
    return int(read_memory()["swap_total"])
