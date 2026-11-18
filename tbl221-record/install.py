#!/usr/bin/env python3
"""Install or uninstall tbl221-record as a systemd service."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

SOURCE_DIR = Path(__file__).resolve().parent
INSTALL_DIR = Path("/opt/tbl221-record")
CONFIG_PATH = Path("/etc/tbl221-record.toml")
SERVICE_PATH = Path("/etc/systemd/system/tbl221-record.service")
DATA_DIR = Path("/var/lib/tbl221-record")


def require_root() -> None:
    if os.geteuid() != 0:
        raise SystemExit("Bu işlem root yetkisi gerektirir (sudo kullanın).")


def systemctl(*arguments: str) -> None:
    subprocess.run(["systemctl", *arguments], check=True)


def install(start: bool) -> None:
    require_root()
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    for name in ("main.py", "config", "db", "model", "util"):
        source = SOURCE_DIR / name
        target = INSTALL_DIR / name
        if target.exists():
            shutil.rmtree(target) if target.is_dir() else target.unlink()
        shutil.copytree(source, target) if source.is_dir() else shutil.copy2(source, target)
    shutil.copy2(SOURCE_DIR.parent / "README.md", INSTALL_DIR / "README.md")
    if not CONFIG_PATH.exists():
        shutil.copy2(SOURCE_DIR / "config/default.toml", CONFIG_PATH)
    shutil.copy2(SOURCE_DIR / "tbl221-record.service", SERVICE_PATH)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    systemctl("daemon-reload")
    systemctl("enable", "tbl221-record.service")
    if start:
        systemctl("restart", "tbl221-record.service")
    print("tbl221-record kuruldu. Durum: systemctl status tbl221-record")


def uninstall() -> None:
    require_root()
    systemctl("disable", "--now", "tbl221-record.service")
    SERVICE_PATH.unlink(missing_ok=True)
    shutil.rmtree(INSTALL_DIR, ignore_errors=True)
    systemctl("daemon-reload")
    print("Program kaldırıldı; yapılandırma ve ölçüm verileri korundu.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "uninstall"), nargs="?", default="install")
    parser.add_argument("--no-start", action="store_true", help="Kurulumdan sonra servisi başlatma")
    args = parser.parse_args()
    if args.action == "install":
        install(not args.no_start)
    else:
        uninstall()
    return 0


if __name__ == "__main__":
    sys.exit(main())
