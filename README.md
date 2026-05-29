# Linux Voice Transcribe

Two global keyboard shortcuts for voice and text on Linux (GNOME/Wayland).

- **Ctrl+Alt+C** — record your voice, transcribe it, copy to clipboard (speech to text)
- **Ctrl+Alt+V** — read your clipboard text aloud and save as MP3 (text to speech)

---

## Requirements

- Linux with GNOME desktop (Wayland or X11)
- Python 3
- A [Mistral API key](https://console.mistral.ai/) (for voice transcription)
- A [Google Cloud service account](https://console.cloud.google.com/) with Text-to-Speech API enabled (for TTS)

### System packages

```bash
sudo pacman -S sox xclip libnotify ffmpeg        # Arch/EndeavourOS/Manjaro
sudo apt install sox xclip libnotify-bin ffmpeg  # Ubuntu/Debian
```

### Python packages

```bash
yay -S python-pynput          # Arch AUR
sudo pacman -S python-requests # Arch official

# Or on Ubuntu/Debian:
pip install pynput requests
```

---

## Tool 1: Voice Transcribe (Ctrl+Alt+C)

Records your microphone and transcribes speech to text using Mistral's Voxtral model. The result is copied to your clipboard.

### Setup

1. Add your Mistral API key to `~/.bashrc`:

```bash
echo 'export MISTRAL_API_KEY=your_key_here' >> ~/.bashrc
source ~/.bashrc
```

2. Register the GNOME keyboard shortcut:

```bash
# Add custom1 to the keybindings list (adjust if you already have custom shortcuts)
gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings \
  "['/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/', '/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom1/']"

BASE="org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom1/"
gsettings set $BASE name 'Voice Transcribe'
gsettings set $BASE binding '<Ctrl><Alt>c'
gsettings set $BASE command "$HOME/linux-transcribe-shortcut/voice-transcribe-toggle.sh"
```

3. Make scripts executable:

```bash
chmod +x ~/linux-transcribe-shortcut/voice-transcribe-toggle.sh
chmod +x ~/linux-transcribe-shortcut/voice-transcribe-once.py
```

### Testing

Press **Ctrl+Alt+C** — you should see a "Recording..." notification. Say something, then press **Ctrl+Alt+C** again. You should see "Transcribing..." then "Copied: [your words]". Paste anywhere to verify.

### How it works

- GNOME calls `voice-transcribe-toggle.sh` on each keypress
- The toggle script uses a PID file (`/tmp/voice-transcribe.pid`) to track state
- On first press: starts `voice-transcribe-once.py` in the background, saves PID
- On second press: sends SIGTERM to the recording process
- The Python script records via `sox`, sends audio to Mistral's `/v1/audio/transcriptions`, copies result to clipboard via `xclip`

---

## Tool 2: TTS Clipboard (Ctrl+Alt+V)

Reads clipboard text aloud using Google Cloud TTS (WaveNet). Audio is saved as an MP3 to `~/Music/TTS Recordings/` and opened with your default media player.

### Google Cloud setup

1. Go to [console.cloud.google.com](https://console.cloud.google.com) and create a project
2. Enable the **Text-to-Speech API**
3. Go to **IAM & Admin > Service Accounts**, create a service account, assign **Basic > Editor** role
4. Under the service account **Keys** tab, create a JSON key and download it
5. Move it somewhere safe:

```bash
mkdir -p ~/.config/gcloud
mv ~/Downloads/your-key-file.json ~/.config/gcloud/tts-service-account.json
```

6. Add to `~/.bashrc`:

```bash
echo 'export GOOGLE_APPLICATION_CREDENTIALS=~/.config/gcloud/tts-service-account.json' >> ~/.bashrc
source ~/.bashrc
```

### Setup

```bash
chmod +x ~/linux-transcribe-shortcut/setup-tts.sh
./setup-tts.sh
```

---

## Managing shortcuts

View logs:

```bash
tail -f ~/voice-transcribe.log
tail -f ~/tts-clipboard.log
```

If a recording gets stuck:

```bash
pkill -f voice-transcribe-once.py && rm -f /tmp/voice-transcribe.pid
```

View or edit shortcuts in **Settings > Keyboard > Custom Shortcuts**.

---

## Troubleshooting

**Shortcut does nothing** — GNOME keybinding may not be registered. Re-run the gsettings commands from Setup step 2.

**"No speech detected"** — Recording was too short or the wrong mic is selected. Check: `arecord -l` to list devices; set default in **Settings > Sound > Input**.

**401 error from Mistral** — API key is wrong or expired. Update `MISTRAL_API_KEY` in `~/.bashrc`.

**No notifications** — `libnotify` not installed, or no notification daemon running. On GNOME this works out of the box.

**xclip error** — Install xclip: `sudo pacman -S xclip` (Arch) or `sudo apt install xclip` (Ubuntu).

**Wayland note** — This tool is designed for Wayland and uses GNOME keybindings instead of pynput for that reason. It does not require XWayland.
