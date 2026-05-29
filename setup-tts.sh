#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_DIR="$HOME/.config/systemd/user"

echo "Linux TTS Clipboard Setup"
echo "========================="

# Check dependencies
for cmd in ffmpeg xclip notify-send python3; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "Error: '$cmd' is not installed."
        echo "Run: sudo pacman -S ffmpeg xclip libnotify"
        exit 1
    fi
done

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --user pynput google-cloud-texttospeech

# Get Google credentials path
echo ""
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    read -rp "Enter path to your Google service account JSON: " CREDS_PATH
    CREDS_PATH="${CREDS_PATH/#\~/$HOME}"
    if [ ! -f "$CREDS_PATH" ]; then
        echo "Error: File not found: $CREDS_PATH"
        exit 1
    fi
    echo "" >> "$HOME/.bashrc"
    echo "export GOOGLE_APPLICATION_CREDENTIALS=$CREDS_PATH" >> "$HOME/.bashrc"
    export GOOGLE_APPLICATION_CREDENTIALS="$CREDS_PATH"
    echo "Added GOOGLE_APPLICATION_CREDENTIALS to ~/.bashrc"
else
    CREDS_PATH="$GOOGLE_APPLICATION_CREDENTIALS"
    echo "GOOGLE_APPLICATION_CREDENTIALS already set: $CREDS_PATH"
fi

# Install systemd user service
mkdir -p "$SERVICE_DIR"
cp "$SCRIPT_DIR/tts-clipboard.service" "$SERVICE_DIR/"

# Inject credentials into service file
sed -i "s|^Environment=DISPLAY|Environment=GOOGLE_APPLICATION_CREDENTIALS=$CREDS_PATH\nEnvironment=DISPLAY|" "$SERVICE_DIR/tts-clipboard.service"

systemctl --user daemon-reload
systemctl --user enable --now tts-clipboard.service

echo ""
echo "Done! TTS Clipboard is running."
echo "  Shortcut: Ctrl+Alt+V to speak clipboard text"
echo "  Logs:     tail -f ~/tts-clipboard.log"
echo ""
echo "Test it by running directly:"
echo "  GOOGLE_APPLICATION_CREDENTIALS=$CREDS_PATH python3 $SCRIPT_DIR/tts-clipboard.py"
