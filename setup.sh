#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_DIR="$HOME/.config/systemd/user"

echo "Linux Voice Transcribe Setup"
echo "============================="

# Check dependencies
for cmd in sox xclip notify-send python3; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "Error: '$cmd' is not installed."
        echo "Run: sudo pacman -S sox xclip xdotool libnotify"
        exit 1
    fi
done

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --user pynput requests

# Check for MISTRAL_API_KEY
if [ -z "$MISTRAL_API_KEY" ]; then
    echo ""
    echo "MISTRAL_API_KEY is not set in your environment."
    read -rp "Enter your Mistral API key (or press Enter to skip): " API_KEY
    if [ -n "$API_KEY" ]; then
        echo "" >> "$HOME/.bashrc"
        echo "export MISTRAL_API_KEY=$API_KEY" >> "$HOME/.bashrc"
        export MISTRAL_API_KEY="$API_KEY"
        echo "Added MISTRAL_API_KEY to ~/.bashrc"
    else
        echo "Skipping — set MISTRAL_API_KEY in ~/.bashrc manually before starting the service."
    fi
else
    echo "MISTRAL_API_KEY already set."
fi

# Install systemd user services
mkdir -p "$SERVICE_DIR"
cp "$SCRIPT_DIR/voice-transcribe.service" "$SERVICE_DIR/"

# Inject MISTRAL_API_KEY into service file
sed -i "s|^Environment=DISPLAY|Environment=MISTRAL_API_KEY=$MISTRAL_API_KEY\nEnvironment=DISPLAY|" "$SERVICE_DIR/voice-transcribe.service"

systemctl --user daemon-reload
systemctl --user enable --now voice-transcribe.service

echo ""
echo "Done! Voice Transcribe is running."
echo "  Shortcut: Ctrl+Alt+C to toggle recording"
echo "  Logs:     tail -f ~/voice-transcribe.log"
echo ""
echo "IMPORTANT: You must grant microphone access."
echo "Test it first by running directly:"
echo "  python3 $SCRIPT_DIR/voice-transcribe.py"
