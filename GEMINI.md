# Linux Voice Transcribe — Agent Context

Two global keyboard shortcuts for voice and text on Linux (GNOME/Wayland).

- **Ctrl+Alt+C** — record voice, transcribe via Mistral Voxtral, copy to clipboard
- **Ctrl+Alt+V** — read clipboard aloud via Google Cloud TTS, save MP3 to `~/Music/TTS Recordings/`

## How it works

### Voice transcribe (Ctrl+Alt+C)

This does NOT use a systemd service or pynput. On Wayland, pynput cannot capture global hotkeys from background processes. Instead:

1. A GNOME custom keybinding calls `voice-transcribe-toggle.sh` on each keypress
2. The toggle script checks for `/tmp/voice-transcribe.pid`:
   - If absent: starts `voice-transcribe-once.py` in the background, writes its PID
   - If present: sends SIGTERM to that PID, deletes the file
3. `voice-transcribe-once.py` records audio via `sox` until it receives SIGTERM, then POSTs the WAV to Mistral's transcription API and copies the result to clipboard via `xclip`

### TTS clipboard (Ctrl+Alt+V)

`tts-clipboard.py` reads from clipboard via `xclip`, sends text to Google Cloud TTS in chunks (max 4800 chars each), stitches chunks with `ffmpeg` if needed, saves an MP3 to `~/Music/TTS Recordings/`, and opens it with `xdg-open`.

## Key files

| File | Purpose |
|------|---------|
| `voice-transcribe-toggle.sh` | GNOME shortcut target; toggles recording via PID file |
| `voice-transcribe-once.py` | Records audio until SIGTERM, then transcribes |
| `tts-clipboard.py` | Reads clipboard aloud via Google Cloud TTS |
| `setup.sh` | Sets up voice transcribe (installs deps, registers GNOME shortcut) |
| `setup-tts.sh` | Sets up TTS clipboard |

## Environment variables

| Variable | Used by | Where set |
|----------|---------|-----------|
| `MISTRAL_API_KEY` | `voice-transcribe-once.py` | `~/.bashrc` |
| `GOOGLE_APPLICATION_CREDENTIALS` | `tts-clipboard.py` | `~/.bashrc` |

The toggle script reads `MISTRAL_API_KEY` from `~/.bashrc` at runtime using grep/cut, so it does not need to be exported into a service environment.

## System dependencies

```bash
# Arch/EndeavourOS
sudo pacman -S sox xclip libnotify ffmpeg
yay -S python-pynput
sudo pacman -S python-requests

# Ubuntu/Debian
sudo apt install sox xclip libnotify-bin ffmpeg
pip install pynput requests
```

## Diagnostics

```bash
# View logs
tail -f ~/voice-transcribe.log
tail -f ~/tts-clipboard.log

# Check GNOME keybindings are registered
gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings

# Kill stuck recording
pkill -f voice-transcribe-once.py && rm -f /tmp/voice-transcribe.pid

# Test Mistral API key
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $MISTRAL_API_KEY" \
  https://api.mistral.ai/v1/models
# Should return 200
```

## Re-registering GNOME keybindings

Run this if shortcuts stop working after a settings reset:

```bash
# Check what custom keybindings already exist first
gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings

# Register voice transcribe as custom1 (adjust index if needed)
BASE="org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom1/"
gsettings set $BASE name 'Voice Transcribe'
gsettings set $BASE binding '<Ctrl><Alt>c'
gsettings set $BASE command "$HOME/linux-transcribe-shortcut/voice-transcribe-toggle.sh"
```

## Common failure modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| Shortcut does nothing | GNOME keybinding lost | Re-register with gsettings (see above) |
| Stuck recording, second press does nothing | PID file stale after crash | `pkill -f voice-transcribe-once.py && rm -f /tmp/voice-transcribe.pid` |
| "No speech detected" | Wrong mic or too short | `arecord -l` to list devices; set default in Sound settings |
| 401 error | Bad/expired Mistral API key | Update `MISTRAL_API_KEY` in `~/.bashrc` |
| No notifications | `libnotify` missing | `sudo pacman -S libnotify` |
| Clipboard not updated | `xclip` missing | `sudo pacman -S xclip` |
