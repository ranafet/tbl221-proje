#!/bin/sh
set -eu

DATABASE="${TMPDIR:-/tmp}/tbl221-container-smoke.db"
cleanup() {
    rm -f "$DATABASE" "$DATABASE-shm" "$DATABASE-wal"
}
trap cleanup EXIT HUP INT TERM
cleanup

printf '%s\n' '==> Compiling Python sources'
python3 -m compileall -q tbl221-record tbl221-graphui packaging/debian/build.py packaging/container/gui_smoke.py

printf '%s\n' '==> Running recorder unit tests'
python3 -m unittest discover -s tbl221-record/tests -v

printf '%s\n' '==> Recording a real system-resource sample'
python3 tbl221-record/main.py --once --database "$DATABASE" --interval 0.1
[ -s "$DATABASE" ]

printf '%s\n' '==> Starting the dashboard with the offscreen Qt backend'
python3 packaging/container/gui_smoke.py "$DATABASE"

printf '%s\n' '==> All container tests passed'
