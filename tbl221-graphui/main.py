#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

try:
    from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
    from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
    from PySide6.QtWidgets import (
        QApplication,
        QFileDialog,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QSpinBox,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )
except ImportError as error:
    raise SystemExit("PySide6 bulunamadı. Kurulum: pip install PySide6") from error

DEFAULT_DATABASE = "/var/lib/tbl221-record/tbl221-record.db"
READING_COLUMNS = (
    "timestamp, cpu_percent, memory_used, memory_total, swap_used, swap_total, "
    "disk_used, disk_total, process_count, load_1, load_5, load_15"
)


def percent(used: int, total: int) -> float:
    return used * 100 / total if total else 0.0


def format_bytes(value: int) -> str:
    amount = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if amount < 1024 or unit == "TiB":
            return f"{amount:.1f} {unit}"
        amount /= 1024
    return f"{amount:.1f} TiB"


class DataStore:
    def __init__(self, path: str):
        self.path = path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(f"file:{Path(self.path).resolve()}?mode=ro", uri=True, timeout=2)
        connection.row_factory = sqlite3.Row
        return connection

    def readings(self, limit: int) -> list[sqlite3.Row]:
        if not Path(self.path).is_file():
            return []
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    f"SELECT {READING_COLUMNS} FROM readings ORDER BY timestamp DESC LIMIT ?", (limit,)
                ).fetchall()
            return list(reversed(rows))
        except sqlite3.Error:
            return []

    def alerts(self, limit: int = 20) -> list[sqlite3.Row]:
        if not Path(self.path).is_file():
            return []
        try:
            with self._connect() as connection:
                return connection.execute(
                    "SELECT timestamp, metric, value, threshold, message FROM alerts "
                    "ORDER BY timestamp DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        except sqlite3.Error:
            return []


class MetricCard(QFrame):
    def __init__(self, title: str, warning: float | None = None):
        super().__init__()
        self.warning = warning
        self.setObjectName("metricCard")
        layout = QVBoxLayout(self)
        self.title = QLabel(title)
        self.title.setObjectName("metricTitle")
        self.value = QLabel("—")
        self.value.setObjectName("metricValue")
        self.detail = QLabel("Veri bekleniyor")
        self.detail.setObjectName("metricDetail")
        layout.addWidget(self.title)
        layout.addWidget(self.value)
        layout.addWidget(self.detail)

    def update_value(self, value: float, display: str, detail: str) -> None:
        self.value.setText(display)
        self.detail.setText(detail)
        color = "#ef4444" if self.warning is not None and value >= self.warning else "#22c55e"
        self.value.setStyleSheet(f"color: {color};")


class LineChart(QWidget):
    def __init__(self, title: str, color: str, maximum: float | None = 100.0):
        super().__init__()
        self.title = title
        self.color = QColor(color)
        self.maximum = maximum
        self.values: list[float] = []
        self.labels: list[int] = []
        self.setMinimumHeight(190)

    def set_data(self, labels: list[int], values: list[float]) -> None:
        self.labels = labels
        self.values = values
        self.update()

    def paintEvent(self, _event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#171b24"))
        painter.setPen(QColor("#e5e7eb"))
        painter.setFont(QFont("Sans", 10, QFont.Weight.Bold))
        painter.drawText(12, 22, self.title)
        plot = QRectF(45, 35, max(1, self.width() - 60), max(1, self.height() - 65))
        painter.setFont(QFont("Sans", 8))
        painter.setPen(QPen(QColor("#374151"), 1))
        max_value = self.maximum or max(self.values or [1]) * 1.1
        max_value = max(max_value, 1)
        for index in range(5):
            y = plot.top() + plot.height() * index / 4
            painter.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
            painter.setPen(QColor("#9ca3af"))
            painter.drawText(2, int(y + 3), f"{max_value * (4 - index) / 4:.0f}")
            painter.setPen(QColor("#374151"))
        if not self.values:
            painter.setPen(QColor("#9ca3af"))
            painter.drawText(plot, Qt.AlignmentFlag.AlignCenter, "Henüz ölçüm yok")
            return
        path = QPainterPath()
        count = len(self.values)
        for index, value in enumerate(self.values):
            x = plot.left() if count == 1 else plot.left() + plot.width() * index / (count - 1)
            y = plot.bottom() - plot.height() * min(max(value, 0), max_value) / max_value
            path.moveTo(x, y) if index == 0 else path.lineTo(x, y)
        painter.setPen(QPen(self.color, 2.5))
        painter.drawPath(path)
        if self.labels:
            painter.setPen(QColor("#9ca3af"))
            start = datetime.fromtimestamp(self.labels[0]).strftime("%H:%M:%S")
            end = datetime.fromtimestamp(self.labels[-1]).strftime("%H:%M:%S")
            painter.drawText(int(plot.left()), self.height() - 8, start)
            painter.drawText(int(plot.right() - 50), self.height() - 8, end)


class Dashboard(QMainWindow):
    def __init__(self, database_path: str):
        super().__init__()
        self.store = DataStore(database_path)
        self.database_path = database_path
        self.last_rows: list[sqlite3.Row] = []
        self.setWindowTitle("TBL221 Sistem Kaynakları İzleme")
        self.resize(1120, 800)
        self._build_ui()
        self._apply_style()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(5000)
        self.refresh()

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        header = QHBoxLayout()
        title = QLabel("Linux Sistem Kaynakları")
        title.setObjectName("pageTitle")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(QLabel("Gösterilecek ölçüm:"))
        self.limit = QSpinBox()
        self.limit.setRange(10, 1000)
        self.limit.setValue(120)
        self.limit.valueChanged.connect(self.refresh)
        header.addWidget(self.limit)
        refresh_button = QPushButton("Yenile")
        refresh_button.clicked.connect(self.refresh)
        header.addWidget(refresh_button)
        export_button = QPushButton("CSV Dışa Aktar")
        export_button.clicked.connect(self.export_csv)
        header.addWidget(export_button)
        layout.addLayout(header)

        self.status = QLabel(self.database_path)
        self.status.setObjectName("status")
        layout.addWidget(self.status)

        cards = QGridLayout()
        self.cpu = MetricCard("CPU", 85)
        self.memory = MetricCard("Bellek", 85)
        self.disk = MetricCard("Disk /", 90)
        self.processes = MetricCard("Süreçler")
        for index, card in enumerate((self.cpu, self.memory, self.disk, self.processes)):
            cards.addWidget(card, 0, index)
        layout.addLayout(cards)

        charts = QGridLayout()
        self.cpu_chart = LineChart("CPU kullanımı (%)", "#38bdf8")
        self.memory_chart = LineChart("Bellek kullanımı (%)", "#a78bfa")
        self.disk_chart = LineChart("Disk kullanımı (%)", "#f59e0b")
        self.load_chart = LineChart("1 dakikalık sistem yükü", "#34d399", maximum=None)
        charts.addWidget(self.cpu_chart, 0, 0)
        charts.addWidget(self.memory_chart, 0, 1)
        charts.addWidget(self.disk_chart, 1, 0)
        charts.addWidget(self.load_chart, 1, 1)
        layout.addLayout(charts)

        alerts_title = QLabel("Son Uyarılar")
        alerts_title.setObjectName("sectionTitle")
        layout.addWidget(alerts_title)
        self.alert_table = QTableWidget(0, 4)
        self.alert_table.setHorizontalHeaderLabels(("Zaman", "Kaynak", "Değer / Eşik", "Açıklama"))
        self.alert_table.horizontalHeader().setStretchLastSection(True)
        self.alert_table.setMaximumHeight(180)
        self.alert_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.alert_table)

    def _apply_style(self) -> None:
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #0f1117; color: #e5e7eb; }
            #pageTitle { font-size: 24px; font-weight: 700; }
            #sectionTitle { font-size: 16px; font-weight: 700; margin-top: 8px; }
            #status, #metricDetail { color: #9ca3af; }
            #metricCard { background: #171b24; border: 1px solid #2b3240; border-radius: 8px; }
            #metricTitle { color: #9ca3af; font-size: 12px; }
            #metricValue { font-size: 25px; font-weight: 700; }
            QPushButton, QSpinBox { background: #252b38; border: 1px solid #3b4558; border-radius: 5px; padding: 6px; }
            QPushButton:hover { background: #30394a; }
            QTableWidget { background: #171b24; alternate-background-color: #1d2330; gridline-color: #303746; }
            QHeaderView::section { background: #252b38; padding: 5px; border: 0; }
        """)

    def refresh(self) -> None:
        rows = self.store.readings(self.limit.value())
        self.last_rows = rows
        if not rows:
            self.status.setText(f"Veri bekleniyor — {self.database_path}")
            self._update_alerts()
            return
        latest = rows[-1]
        age = max(0, int(datetime.now().timestamp()) - latest["timestamp"])
        self.status.setText(
            f"Son ölçüm: {datetime.fromtimestamp(latest['timestamp']):%Y-%m-%d %H:%M:%S} "
            f"({age} sn önce) — {self.database_path}"
        )
        memory_pct = percent(latest["memory_used"], latest["memory_total"])
        disk_pct = percent(latest["disk_used"], latest["disk_total"])
        self.cpu.update_value(latest["cpu_percent"], f"{latest['cpu_percent']:.1f}%", f"Load: {latest['load_1']:.2f}")
        self.memory.update_value(memory_pct, f"{memory_pct:.1f}%", f"{format_bytes(latest['memory_used'])} / {format_bytes(latest['memory_total'])}")
        self.disk.update_value(disk_pct, f"{disk_pct:.1f}%", f"{format_bytes(latest['disk_used'])} / {format_bytes(latest['disk_total'])}")
        self.processes.update_value(0, str(latest["process_count"]), "Çalışan süreç sayısı")
        labels = [row["timestamp"] for row in rows]
        self.cpu_chart.set_data(labels, [row["cpu_percent"] for row in rows])
        self.memory_chart.set_data(labels, [percent(row["memory_used"], row["memory_total"]) for row in rows])
        self.disk_chart.set_data(labels, [percent(row["disk_used"], row["disk_total"]) for row in rows])
        self.load_chart.set_data(labels, [row["load_1"] for row in rows])
        self._update_alerts()

    def _update_alerts(self) -> None:
        alerts = self.store.alerts()
        self.alert_table.setRowCount(len(alerts))
        for row_index, alert in enumerate(alerts):
            values = (
                datetime.fromtimestamp(alert["timestamp"]).strftime("%Y-%m-%d %H:%M:%S"),
                alert["metric"],
                f"{alert['value']:.1f} / {alert['threshold']:.1f}",
                alert["message"],
            )
            for column, value in enumerate(values):
                self.alert_table.setItem(row_index, column, QTableWidgetItem(value))
        self.alert_table.resizeColumnsToContents()

    def export_csv(self) -> None:
        if not self.last_rows:
            QMessageBox.information(self, "CSV", "Dışa aktarılacak ölçüm bulunmuyor.")
            return
        filename, _ = QFileDialog.getSaveFileName(self, "CSV Kaydet", "tbl221-readings.csv", "CSV (*.csv)")
        if not filename:
            return
        with open(filename, "w", newline="", encoding="utf-8") as output:
            writer = csv.writer(output)
            writer.writerow(self.last_rows[0].keys())
            writer.writerows(tuple(row) for row in self.last_rows)
        self.status.setText(f"{len(self.last_rows)} ölçüm {filename} dosyasına aktarıldı")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TBL221 sistem kaynakları grafik arayüzü")
    parser.add_argument(
        "--database",
        default=os.environ.get("TBL221_DATABASE", DEFAULT_DATABASE),
        help="Recorder SQLite veritabanı yolu",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    app = QApplication(sys.argv[:1])
    app.setApplicationName("TBL221 GraphUI")
    window = Dashboard(args.database)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
