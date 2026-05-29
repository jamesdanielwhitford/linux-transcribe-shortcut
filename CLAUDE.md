# Linux Voice Transcribe

Two global keyboard shortcuts for voice and text on Linux (GNOME/Wayland).

- **Ctrl+Alt+C** — record voice, transcribe via Mistral Voxtral, copy to clipboard
- **Ctrl+Alt+V** — read clipboard aloud via Google Cloud TTS, save MP3 to `~/Music/TTS Recordings/`

## Key files

- `voice-transcribe-toggle.sh` — called by GNOME shortcut, manages PID file to toggle recording
- `voice-transcribe-once.py` — records until killed (SIGTERM), then transcribes and copies to clipboard
- `tts-clipboard.py` — reads clipboard via Google Cloud TTS, saves MP3, opens with xdg-open
- `voice-transcribe.service` / `tts-clipboard.service` — systemd service templates (not used for voice transcribe on Wayland; kept for reference)
- `setup.sh` / `setup-tts.sh` — setup scripts

## Architecture note (important)

**Voice transcribe does NOT use a systemd service.** pynput global hotkeys don't work from background services on Wayland. Instead, a GNOME custom keybinding calls `voice-transcribe-toggle.sh` directly. The toggle script uses `/tmp/voice-transcribe.pid` to track whether recording is active.

TTS (`tts-clipboard.py`) also uses a GNOME keybinding (Ctrl+Alt+V) via the same pattern.

## GNOME keybinding registration

These are registered as `custom1` and `custom2` in gsettings:

```bash
gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings
```

To re-register voice transcribe if lost:

```bash
BASE="org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom1/"
gsettings set $BASE name 'Voice Transcribe'
gsettings set $BASE binding '<Ctrl><Alt>c'
gsettings set $BASE command "$HOME/linux-transcribe-shortcut/voice-transcribe-toggle.sh"
```

## Environment variables

- `MISTRAL_API_KEY` — set in `~/.bashrc`, read at runtime by `voice-transcribe-toggle.sh`
- `GOOGLE_APPLICATION_CREDENTIALS` — set in `~/.bashrc`, read by `tts-clipboard.py`

## Logs

```bash
tail -f ~/voice-transcribe.log
tail -f ~/tts-clipboard.log
```

## Common failure modes

**Shortcut does nothing** — GNOME keybinding lost (e.g. after settings reset). Re-register with gsettings commands above.

**Stuck in recording state** — PID file left over from a crash:
```bash
pkill -f voice-transcribe-once.py && rm -f /tmp/voice-transcribe.pid
```

**"No speech detected"** — Recording too short, or wrong mic. Check: `arecord -l`

**401 from Mistral** — API key wrong or expired. Update `MISTRAL_API_KEY` in `~/.bashrc`.

**No notifications** — `libnotify` not installed: `sudo pacman -S libnotify`

**xclip error** — `sudo pacman -S xclip`

**sox not found** — `sudo pacman -S sox`

## System dependencies (Arch/EndeavourOS)

```bash
sudo pacman -S sox xclip libnotify ffmpeg
yay -S python-pynput
sudo pacman -S python-requests
```
