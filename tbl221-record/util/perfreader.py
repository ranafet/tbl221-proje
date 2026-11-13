import io
import datetime
from model.perflog import PerfLog

def read_current_cpu_usage() -> float:
    with open("/proc/stat", "r") as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("cpu "):
                fields = line.split()
                user = int(fields[1])
                nice = int(fields[2])
                system = int(fields[3])
                idle = int(fields[4])
                total = user + nice + system + idle
                return total
            else:
                raise ValueError("Unexpected line in /proc/stat: " + line)
        raise ValueError("No cpu line found in /proc/stat")
    raise RuntimeError("Unexpected error reading /proc/stat")

def read_current_mem_usage() -> int:
    with open("/proc/meminfo", "r") as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("MemTotal:"):
                fields = line.split()
                return int(fields[1])
        raise ValueError("No MemTotal line found in /proc/meminfo")

def read_current_swap_usage() -> int:
    with open("/proc/meminfo", "r") as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("SwapTotal:"):
                fields = line.split()
                return int(fields[1])
        raise ValueError("No SwapTotal line found in /proc/meminfo")

def read_current_total_mem_usage() -> int:
    mem_usage = read_current_mem_usage()
    swap_usage = read_current_swap_usage()
    return mem_usage + swap_usage

def read_maxmem() -> int:
    with open("/proc/meminfo", "r") as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("MemTotal:"):
                fields = line.split()
                return int(fields[1])
        raise ValueError("No MemTotal line found in /proc/meminfo")

def read_maxswap() -> int:
    with open("/proc/meminfo", "r") as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("SwapTotal:"):
                fields = line.split()
                return int(fields[1])
        raise ValueError("No SwapTotal line found in /proc/meminfo")
