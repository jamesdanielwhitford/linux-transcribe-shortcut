#!/bin/bash
# Called by GNOME custom shortcut (Ctrl+Alt+C). Toggles recording on/off.

LOCK_FILE="/tmp/voice-transcribe.pid"
LOG="$HOME/voice-transcribe.log"
MISTRAL_API_KEY="$(grep 'export MISTRAL_API_KEY' ~/.bashrc | cut -d= -f2)"
export MISTRAL_API_KEY

echo "[toggle $(date)] LOCK_FILE exists: $([ -f "$LOCK_FILE" ] && echo yes || echo no)" >> "$LOG"

if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE")
    echo "[toggle $(date)] stopping PID $PID" >> "$LOG"
    kill "$PID" 2>>"$LOG"
    rm -f "$LOCK_FILE"
else
    echo "[toggle $(date)] starting recording" >> "$LOG"
    python3 "$HOME/linux-transcribe-shortcut/voice-transcribe-once.py" >> "$LOG" 2>&1 &
    echo $! > "$LOCK_FILE"
    echo "[toggle $(date)] started PID $!" >> "$LOG"
fi
