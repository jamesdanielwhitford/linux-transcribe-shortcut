#!/usr/bin/env python3
"""
Called by voice-transcribe-toggle.sh. Records audio until killed, then transcribes
and copies result to clipboard.
"""

import os
import signal
import subprocess
import tempfile
import time
import requests

MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")
MODEL = "voxtral-mini-latest"
ENDPOINT = "https://api.mistral.ai/v1/audio/transcriptions"

if not MISTRAL_API_KEY:
    subprocess.run(["notify-send", "Voice Transcribe", "Error: MISTRAL_API_KEY not set"], check=False)
    raise SystemExit(1)


def notify(title, message):
    subprocess.run(["notify-send", title, message], check=False)


tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
audio_path = tmp.name
tmp.close()

notify("Voice Transcribe", "Recording... (press Ctrl+Alt+C to stop)")
print("Recording started")

sox_proc = subprocess.Popen(
    ["sox", "-d", "-r", "16000", "-c", "1", "-b", "16", audio_path],
    stderr=subprocess.DEVNULL,
)

stop_requested = False


def on_signal(signum, frame):
    global stop_requested
    stop_requested = True
    sox_proc.terminate()


signal.signal(signal.SIGTERM, on_signal)
signal.signal(signal.SIGINT, on_signal)

# Poll instead of blocking wait() so signals are delivered
while sox_proc.poll() is None:
    time.sleep(0.1)

if not stop_requested:
    # sox exited on its own (shouldn't happen) — just clean up
    try:
        os.unlink(audio_path)
    except Exception:
        pass
    raise SystemExit(0)

notify("Voice Transcribe", "Transcribing...")
print("Transcribing...")

max_retries = 4
try:
    response = None
    for attempt in range(max_retries):
        with open(audio_path, "rb") as f:
            response = requests.post(
                ENDPOINT,
                headers={"Authorization": f"Bearer {MISTRAL_API_KEY}"},
                files={"file": ("audio.wav", f, "audio/wav")},
                data={"model": MODEL},
                timeout=60,
            )
        if response.status_code not in (429, 503) or attempt == max_retries - 1:
            break
        wait = 2 ** attempt
        print(f"Retrying in {wait}s...")
        time.sleep(wait)
    response.raise_for_status()
    text = response.json().get("text", "").strip()
    if text:
        subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode(), check=True)
        notify("Voice Transcribe", f"Copied: {text[:60]}{'...' if len(text) > 60 else ''}")
        print(f"Copied: {text}")
    else:
        notify("Voice Transcribe", "No speech detected.")
        print("No speech detected.")
except Exception as e:
    notify("Voice Transcribe", f"Error: {e}")
    print(f"Error: {e}")
finally:
    try:
        os.unlink(audio_path)
    except Exception:
        pass
