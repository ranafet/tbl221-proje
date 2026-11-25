#!/bin/sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
RUNTIME_DIR="$PROJECT_DIR/dist"

stop_process() {
    NAME=$1
    PID_FILE=$2

    if [ ! -f "$PID_FILE" ]; then
        printf '%s is not running (no PID file).\n' "$NAME"
        return
    fi

    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        printf '%s stopped (PID %s).\n' "$NAME" "$PID"
    else
        printf '%s was not running; removed stale PID file.\n' "$NAME"
    fi
    rm -f "$PID_FILE"
}

stop_process "Dashboard" "$RUNTIME_DIR/graphui.pid"
stop_process "Recorder" "$RUNTIME_DIR/recorder.pid"
