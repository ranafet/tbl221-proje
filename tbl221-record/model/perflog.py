import datetime

class PerfLog:
    def __init__(self, timestamp: int | None, used_ram: int, free_ram: int, cpu_usage: float):
        self.used_ram = used_ram
        self.free_ram = free_ram
        self.cpu_usage = cpu_usage
        if timestamp is None:
            self.timestamp = datetime.now().timestamp()
        else:
            self.timestamp = timestamp

    def __repr__(self):
        return f"PerfLog(timestamp={self.timestamp}, used_ram={self.used_ram}, free_ram={self.free_ram}, cpu_usage={self.cpu_usage})"
