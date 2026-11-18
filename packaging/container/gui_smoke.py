"""Start the dashboard briefly using Qt's offscreen platform plugin."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def load_graphui():
    source = Path(__file__).resolve().parents[2] / "tbl221-graphui/main.py"
    spec = importlib.util.spec_from_file_location("tbl221_graphui_main", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"GraphUI modülü yüklenemedi: {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit(f"Kullanım: {sys.argv[0]} DATABASE")
    graphui = load_graphui()
    app = graphui.QApplication([sys.argv[0]])
    window = graphui.Dashboard(sys.argv[1])
    window.show()
    graphui.QTimer.singleShot(250, app.quit)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
