#!/bin/sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
RUNTIME_DIR="$PROJECT_DIR/dist"
PID_FILE="$RUNTIME_DIR/recorder.pid"
DATABASE="$RUNTIME_DIR/tbl221-record.db"
LOG_FILE="$RUNTIME_DIR/recorder.log"
PROGRAM="$PROJECT_DIR/tbl221-record/main.py"

mkdir -p "$RUNTIME_DIR"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null && [ -r "/proc/$PID/cmdline" ] \
        && tr '\0' ' ' < "/proc/$PID/cmdline" | grep -Fq "$PROGRAM"; then
        printf 'Recorder is already running (PID %s).\n' "$PID"
        exit 0
    fi
    rm -f "$PID_FILE"
fi

nohup python3 "$PROGRAM" --database "$DATABASE" >>"$LOG_FILE" 2>&1 &
PID=$!
printf '%s\n' "$PID" > "$PID_FILE"
sleep 1

if kill -0 "$PID" 2>/dev/null; then
    printf 'Recorder started (PID %s).\nDatabase: %s\nLog: %s\n' "$PID" "$DATABASE" "$LOG_FILE"
else
    printf 'Recorder failed to start. See %s\n' "$LOG_FILE" >&2
    rm -f "$PID_FILE"
    exit 1
fi
