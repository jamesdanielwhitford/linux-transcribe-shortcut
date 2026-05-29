# Linux Voice Transcribe

A Linux background tool that records voice on a global hotkey and transcribes it to clipboard using Mistral's Voxtral model. Also includes a TTS clipboard reader.

## Shortcuts

- **Ctrl+Alt+C** — toggle recording on/off (speech to text, copies to clipboard)
- **Ctrl+Alt+V** — read clipboard aloud using Google Cloud TTS

## Key files

- `voice-transcribe.py` — main transcription script, reads `MISTRAL_API_KEY` from environment
- `tts-clipboard.py` — TTS script, reads `GOOGLE_APPLICATION_CREDENTIALS` from environment
- `voice-transcribe.service` — systemd user service template for transcription
- `tts-clipboard.service` — systemd user service template for TTS
- `setup.sh` — one-command setup for voice transcription
- `setup-tts.sh` — one-command setup for TTS clipboard

## Model

- Model: `voxtral-mini-latest`
- Endpoint: `https://api.mistral.ai/v1/audio/transcriptions`

## System dependencies (Arch/EndeavourOS)

```bash
sudo pacman -S sox xclip xdotool libnotify ffmpeg
pip install --user pynput requests google-cloud-texttospeech
```

## Setup

```bash
chmod +x setup.sh setup-tts.sh
./setup.sh       # voice transcription
./setup-tts.sh   # TTS clipboard (optional)
```

## Managing services

```bash
# Status
systemctl --user status voice-transcribe
systemctl --user status tts-clipboard

# Stop
systemctl --user stop voice-transcribe
systemctl --user stop tts-clipboard

# Start
systemctl --user start voice-transcribe
systemctl --user start tts-clipboard

# Restart after config changes
systemctl --user restart voice-transcribe

# View logs
tail -f ~/voice-transcribe.log
tail -f ~/tts-clipboard.log

# Disable autostart
systemctl --user disable voice-transcribe
systemctl --user disable tts-clipboard
```

## Common problems

**No notifications showing** — `libnotify` must be installed (`sudo pacman -S libnotify`) and a notification daemon must be running (GNOME has one built in).

**"sox not found"** in the log — `sox` not installed. Run `sudo pacman -S sox`.

**Clipboard not working** — `xclip` not installed. Run `sudo pacman -S xclip`. On Wayland you may need `wl-clipboard` instead and replace `xclip` calls with `wl-copy`/`wl-paste`.

**Shortcut works in terminal but not in background** — The service may not have the right `DISPLAY` or `DBUS_SESSION_BUS_ADDRESS`. Check the service file has correct values and restart: `systemctl --user restart voice-transcribe`.

**Service fails to start** — Check logs: `journalctl --user -u voice-transcribe -n 50`. Most common cause is `MISTRAL_API_KEY` not set in the service environment.

**Wayland note** — `pynput` global hotkeys require `XWayland` on Wayland sessions. If shortcuts don't work, ensure `xorg-xwayland` is installed and the session is running in XWayland compatibility mode.

**No speech detected** — Recording may be too short, or wrong microphone selected. Check: `arecord -l` to list devices; set default in system sound settings.

## Environment variables

Both scripts read from environment. The setup scripts inject these into the systemd service files:

- `MISTRAL_API_KEY` — required for voice-transcribe.py
- `GOOGLE_APPLICATION_CREDENTIALS` — required for tts-clipboard.py
- `DISPLAY` — required for pynput to capture global keys (usually `:0`)
- `DBUS_SESSION_BUS_ADDRESS` — required for notify-send to work from services
