#!/bin/bash
# Picks up DISPLAY and XAUTHORITY from the running graphical session at launch time,
# so the service works after reboots even if the Xauthority filename changes.

export DISPLAY=:0
export XAUTHORITY=$(ls /run/user/1000/.mutter-Xwaylandauth.* 2>/dev/null | head -1)
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus

exec /usr/bin/python3 "$HOME/linux-transcribe-shortcut/voice-transcribe.py"
