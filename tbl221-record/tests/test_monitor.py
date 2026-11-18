from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from db import Database
from main import AlertManager
from model.perflog import PerfLog
from util.perfreader import CpuTimes, cpu_percent, parse_cpu_times, parse_meminfo


def reading(timestamp: int = 100, cpu: float = 10.0) -> PerfLog:
    return PerfLog(
        timestamp=timestamp,
        cpu_percent=cpu,
        memory_used=50,
        memory_total=100,
        swap_used=0,
        swap_total=0,
        disk_used=25,
        disk_total=100,
        process_count=12,
        load_1=0.5,
        load_5=0.4,
        load_15=0.3,
    )


class PerfReaderTests(unittest.TestCase):
    def test_cpu_delta_percentage(self) -> None:
        self.assertEqual(parse_cpu_times("cpu  100 0 50 850 0 0 0 0"), CpuTimes(850, 1000))
        self.assertAlmostEqual(cpu_percent(CpuTimes(850, 1000), CpuTimes(900, 1100)), 50.0)

    def test_meminfo_is_converted_to_bytes(self) -> None:
        values = parse_meminfo("MemTotal: 1000 kB\nMemAvailable: 250 kB\n")
        self.assertEqual(values["MemTotal"], 1_024_000)
        self.assertEqual(values["MemAvailable"], 256_000)


class DatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.database = Database(str(Path(self.tempdir.name, "readings.db")))
        self.database.initialize()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_reading_round_trip(self) -> None:
        expected = reading()
        self.database.insert_reading(expected)
        actual = self.database.recent_readings(1)[0]
        self.assertEqual(dict(actual), {name: getattr(expected, name) for name in dict(actual)})

    def test_alert_threshold_and_cooldown(self) -> None:
        manager = AlertManager(self.database, {"cpu_percent": 80.0}, cooldown=60)
        self.assertEqual(len(manager.evaluate(reading(cpu=90))), 1)
        self.assertEqual(len(manager.evaluate(reading(timestamp=120, cpu=95))), 0)
        self.assertEqual(len(manager.evaluate(reading(timestamp=161, cpu=95))), 1)
        self.assertEqual(len(self.database.recent_alerts()), 2)


if __name__ == "__main__":
    unittest.main()
