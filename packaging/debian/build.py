"""Build tbl221-record and tbl221-graphui Debian binary packages."""
from __future__ import annotations

import gzip
import io
import os
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSION = "1.0.0"
MAINTAINER = "Yiğit Cemal Öztürk <251307091@kocaeli.edu.tr>"
EPOCH = int(os.environ.get("SOURCE_DATE_EPOCH", "0"))


def add_bytes(archive: tarfile.TarFile, name: str, data: bytes, mode: int = 0o644) -> None:
    info = tarfile.TarInfo(name=name.lstrip("/"))
    info.size = len(data)
    info.mode = mode
    info.mtime = EPOCH
    info.uid = info.gid = 0
    info.uname = info.gname = "root"
    archive.addfile(info, io.BytesIO(data))


def add_directory(archive: tarfile.TarFile, name: str, mode: int = 0o755) -> None:
    info = tarfile.TarInfo(name=name.strip("/") + "/")
    info.type = tarfile.DIRTYPE
    info.mode = mode
    info.mtime = EPOCH
    info.uid = info.gid = 0
    info.uname = info.gname = "root"
    archive.addfile(info)


def add_source(archive: tarfile.TarFile, source: Path, destination: str, mode: int = 0o644) -> None:
    add_bytes(archive, destination, source.read_bytes(), mode)


def add_tree(archive: tarfile.TarFile, source: Path, destination: str) -> None:
    for path in sorted(source.rglob("*")):
        if "__pycache__" in path.parts or not path.is_file():
            continue
        add_source(archive, path, f"{destination}/{path.relative_to(source)}")


def compressed_tar(populate) -> bytes:
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.GNU_FORMAT) as archive:
        populate(archive)
    return gzip.compress(raw.getvalue(), compresslevel=9, mtime=EPOCH)


def ar_member(name: str, data: bytes) -> bytes:
    timestamp = str(EPOCH).encode()
    header = (
        name.encode().ljust(16)
        + timestamp.ljust(12)
        + b"0".ljust(6)
        + b"0".ljust(6)
        + b"100644".ljust(8)
        + str(len(data)).encode().ljust(10)
        + b"`\n"
    )
    return header + data + (b"\n" if len(data) % 2 else b"")


def write_deb(output: Path, control: bytes, data: bytes) -> None:
    output.write_bytes(
        b"!<arch>\n"
        + ar_member("debian-binary", b"2.0\n")
        + ar_member("control.tar.gz", control)
        + ar_member("data.tar.gz", data)
    )


def control_archive(metadata: str, conffiles: str = "", scripts: dict[str, str] | None = None) -> bytes:
    def populate(archive: tarfile.TarFile) -> None:
        add_bytes(archive, "control", metadata.encode())
        if conffiles:
            add_bytes(archive, "conffiles", conffiles.encode())
        for name, content in (scripts or {}).items():
            add_bytes(archive, name, content.encode(), 0o755)

    return compressed_tar(populate)


def record_data() -> bytes:
    def populate(archive: tarfile.TarFile) -> None:
        add_directory(archive, "var/lib/tbl221-record")
        add_source(archive, ROOT / "tbl221-record/main.py", "usr/libexec/tbl221-record/main.py")
        for package in ("config", "db", "model", "util"):
            add_tree(archive, ROOT / f"tbl221-record/{package}", f"usr/libexec/tbl221-record/{package}")
        add_source(archive, ROOT / "packaging/bin/tbl221-record", "usr/bin/tbl221-record", 0o755)
        add_source(archive, ROOT / "packaging/systemd/tbl221-record.service", "usr/lib/systemd/system/tbl221-record.service")
        add_source(archive, ROOT / "tbl221-record/config/default.toml", "etc/tbl221-record.toml")
        add_bytes(archive, "usr/share/man/man8/tbl221-record.8.gz", gzip.compress((ROOT / "docs/tbl221-record.8").read_bytes(), mtime=EPOCH))
        add_source(archive, ROOT / "README.md", "usr/share/doc/tbl221-record/README.md")
        add_source(archive, ROOT / "LICENSE", "usr/share/doc/tbl221-record/LICENSE")

    return compressed_tar(populate)


def graphui_data() -> bytes:
    def populate(archive: tarfile.TarFile) -> None:
        add_source(archive, ROOT / "tbl221-graphui/main.py", "usr/libexec/tbl221-graphui/main.py")
        add_source(archive, ROOT / "packaging/bin/tbl221-graphui", "usr/bin/tbl221-graphui", 0o755)
        add_source(archive, ROOT / "packaging/applications/tbl221-graphui.desktop", "usr/share/applications/tbl221-graphui.desktop")
        add_bytes(archive, "usr/share/man/man8/tbl221-graphui.8.gz", gzip.compress((ROOT / "docs/tbl221-graphui.8").read_bytes(), mtime=EPOCH))
        add_source(archive, ROOT / "README.md", "usr/share/doc/tbl221-graphui/README.md")
        add_source(archive, ROOT / "LICENSE", "usr/share/doc/tbl221-graphui/LICENSE")

    return compressed_tar(populate)


def installed_size(data: bytes) -> int:
    with tarfile.open(fileobj=io.BytesIO(gzip.decompress(data)), mode="r:") as archive:
        return max(1, (sum(item.size for item in archive.getmembers()) + 1023) // 1024)


def main() -> int:
    output_dir = ROOT / "dist/deb"
    output_dir.mkdir(parents=True, exist_ok=True)

    record = record_data()
    graphui = graphui_data()
    lifecycle = {
        "postinst": "#!/bin/sh\nset -e\nif command -v systemctl >/dev/null 2>&1; then\n    systemctl daemon-reload || true\n    systemctl preset tbl221-record.service || true\nfi\n",
        "prerm": "#!/bin/sh\nset -e\nif [ \"$1\" = remove ] && command -v systemctl >/dev/null 2>&1; then\n    systemctl disable --now tbl221-record.service || true\nfi\n",
        "postrm": "#!/bin/sh\nset -e\nif command -v systemctl >/dev/null 2>&1; then\n    systemctl daemon-reload || true\nfi\n",
    }
    record_control = f"""Package: tbl221-record
Version: {VERSION}
Section: admin
Priority: optional
Architecture: all
Maintainer: {MAINTAINER}
Depends: python3 (>= 3.11)
Installed-Size: {installed_size(record)}
Description: Linux system resource recorder
 Periodically records CPU, memory, swap, disk, process and load metrics in
 SQLite and emits threshold alerts through a hardened systemd service.
"""
    graphui_control = f"""Package: tbl221-graphui
Version: {VERSION}
Section: utils
Priority: optional
Architecture: all
Maintainer: {MAINTAINER}
Depends: python3 (>= 3.11), python3-pyside6.qtcore (>= 6.8), python3-pyside6.qtgui (>= 6.8), python3-pyside6.qtwidgets (>= 6.8)
Recommends: tbl221-record (= {VERSION})
Installed-Size: {installed_size(graphui)}
Description: graphical dashboard for TBL221 resource measurements
 Displays live cards, history charts and alerts from the SQLite database
 maintained by tbl221-record, and exports selected measurements as CSV.
"""
    write_deb(
        output_dir / f"tbl221-record_{VERSION}_all.deb",
        control_archive(record_control, "/etc/tbl221-record.toml\n", lifecycle),
        record,
    )
    write_deb(
        output_dir / f"tbl221-graphui_{VERSION}_all.deb",
        control_archive(graphui_control),
        graphui,
    )
    print(f"Debian packages written to {output_dir.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
