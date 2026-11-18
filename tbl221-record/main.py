#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import signal
import sys
import time
from pathlib import Path

# Allow direct execution from any working directory.
PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from config import Config
from db import Database
from model.perflog import PerfLog
from util.perfreader import collect, read_cpu_times

LOGGER = logging.getLogger("tbl221-record")
METRIC_LABELS = {
    "cpu_percent": "CPU kullanımı",
    "memory_percent": "Bellek kullanımı",
    "disk_percent": "Disk kullanımı",
    "load_1": "1 dakikalık sistem yükü",
}


def metric_values(reading: PerfLog) -> dict[str, float]:
    return {
        "cpu_percent": reading.cpu_percent,
        "memory_percent": reading.memory_percent,
        "disk_percent": reading.disk_percent,
        "load_1": reading.load_1,
    }


class AlertManager:
    def __init__(self, database: Database, thresholds: dict[str, float], cooldown: int):
        self.database = database
        self.thresholds = thresholds
        self.cooldown = cooldown
        self.last_alert: dict[str, int] = {}

    def evaluate(self, reading: PerfLog) -> list[str]:
        messages: list[str] = []
        for metric, value in metric_values(reading).items():
            threshold = self.thresholds.get(metric)
            if threshold is None or value < threshold:
                continue
            if reading.timestamp - self.last_alert.get(metric, 0) < self.cooldown:
                continue
            label = METRIC_LABELS.get(metric, metric)
            suffix = "%" if metric.endswith("percent") else ""
            message = f"{label} eşik üzerinde: {value:.1f}{suffix} >= {threshold:.1f}{suffix}"
            self.database.insert_alert(reading.timestamp, metric, value, threshold, message)
            self.last_alert[metric] = reading.timestamp
            LOGGER.warning(message)
            messages.append(message)
        return messages


class Recorder:
    def __init__(self, config: Config, once: bool = False):
        self.config = config
        self.once = once
        self.running = True
        self.database = Database(config.database_path)
        self.alerts = AlertManager(self.database, config.thresholds, config.alert_cooldown)

    def stop(self, signum: int, _frame: object) -> None:
        LOGGER.info("Durdurma sinyali alındı (%s)", signum)
        self.running = False

    def run(self) -> int:
        self.database.initialize()
        previous_cpu = read_cpu_times()
        if self.once:
            time.sleep(min(0.2, self.config.record_period))
        LOGGER.info(
            "Kaynak izleme başladı; aralık=%.1fs veritabanı=%s",
            self.config.record_period,
            self.config.database_path,
        )
        next_sample = time.monotonic()
        prune_counter = 0
        while self.running:
            if not self.once:
                delay = next_sample - time.monotonic()
                if delay > 0:
                    time.sleep(delay)
            try:
                reading, previous_cpu = collect(previous_cpu, self.config.disk_path)
                self.database.insert_reading(reading)
                self.alerts.evaluate(reading)
                LOGGER.info(
                    "CPU=%.1f%% RAM=%.1f%% disk=%.1f%% süreç=%d load=%.2f",
                    reading.cpu_percent,
                    reading.memory_percent,
                    reading.disk_percent,
                    reading.process_count,
                    reading.load_1,
                )
                prune_counter += 1
                if prune_counter >= 720:
                    self.database.prune(self.config.retention_days)
                    prune_counter = 0
            except (OSError, ValueError) as error:
                LOGGER.exception("Kaynak ölçümü başarısız: %s", error)
            if self.once:
                break
            next_sample = max(next_sample + self.config.record_period, time.monotonic())
        LOGGER.info("Kaynak izleme durdu")
        return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Linux sistem kaynaklarını ölç ve SQLite'a kaydet")
    parser.add_argument("--config", help="TOML yapılandırma dosyası")
    parser.add_argument("--database", help="Yapılandırmadaki veritabanı yolunu geçersiz kıl")
    parser.add_argument("--interval", type=float, help="Ölçüm aralığını saniye olarak geçersiz kıl")
    parser.add_argument("--once", action="store_true", help="Bir ölçüm alıp çık")
    parser.add_argument("--verbose", action="store_true", help="Ayrıntılı günlük çıktısı")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    config = Config.load(args.config)
    if args.database or args.interval:
        config = Config(
            record_period=max(0.1, args.interval if args.interval is not None else config.record_period),
            database_path=args.database or config.database_path,
            disk_path=config.disk_path,
            retention_days=config.retention_days,
            thresholds=config.thresholds,
            alert_cooldown=config.alert_cooldown,
        )
    recorder = Recorder(config, once=args.once)
    signal.signal(signal.SIGTERM, recorder.stop)
    signal.signal(signal.SIGINT, recorder.stop)
    return recorder.run()


if __name__ == "__main__":
    raise SystemExit(main())
