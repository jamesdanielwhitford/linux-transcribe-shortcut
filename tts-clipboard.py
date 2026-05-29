#!/usr/bin/env python3
"""
Clipboard TTS tool for Linux.
Press Ctrl+Alt+V to read the current clipboard text aloud using Google Cloud TTS.
Audio is saved as an MP3 to ~/Music/TTS Recordings/ and opened with xdg-open.

Long texts are automatically split into chunks and stitched together with ffmpeg.

Requires:
  export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
  pip install pynput google-cloud-texttospeech
  sudo pacman -S ffmpeg xclip
"""

import os
import subprocess
import threading
import datetime
import tempfile
from pynput import keyboard
from google.cloud import texttospeech

LANGUAGE_CODE = "en-US"
VOICE_NAME = "en-US-Wavenet-F"
AUDIO_ENCODING = texttospeech.AudioEncoding.MP3
OUTPUT_DIR = os.path.expanduser("~/Music/TTS Recordings")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Google Cloud TTS hard limit is 5000 bytes per request; chunk conservatively at 4800.
CHUNK_SIZE = 4800

tts_lock = threading.Lock()
pressed_keys = set()


def notify(title, message):
    subprocess.run(["notify-send", title, message], check=False)


def get_clipboard():
    result = subprocess.run(
        ["xclip", "-selection", "clipboard", "-o"],
        capture_output=True,
    )
    return result.stdout.decode("utf-8", errors="replace").strip()


def split_text(text, chunk_size):
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    while text:
        if len(text) <= chunk_size:
            chunks.append(text)
            break

        segment = text[:chunk_size]
        split_at = max(
            segment.rfind(". "),
            segment.rfind("! "),
            segment.rfind("? "),
            segment.rfind(".\n"),
        )

        if split_at == -1:
            split_at = segment.rfind(" ")

        if split_at == -1:
            split_at = chunk_size - 1

        chunks.append(text[:split_at + 1].strip())
        text = text[split_at + 1:].strip()

    return chunks


def synthesize_chunk(client, text, voice, audio_config):
    synthesis_input = texttospeech.SynthesisInput(text=text)
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )
    return response.audio_content


def speak_clipboard():
    text = get_clipboard()
    if not text:
        notify("TTS Clipboard", "Clipboard is empty.")
        print("Clipboard is empty.")
        return

    preview = text[:60] + ("..." if len(text) > 60 else "")
    notify("TTS Clipboard", f"Speaking: {preview}")
    print(f"Speaking: {preview}")

    try:
        client = texttospeech.TextToSpeechClient()
        voice = texttospeech.VoiceSelectionParams(
            language_code=LANGUAGE_CODE,
            name=VOICE_NAME,
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=AUDIO_ENCODING,
        )

        chunks = split_text(text, CHUNK_SIZE)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_path = os.path.join(OUTPUT_DIR, f"tts_{timestamp}.mp3")

        if len(chunks) == 1:
            audio_content = synthesize_chunk(client, chunks[0], voice, audio_config)
            with open(output_path, "wb") as f:
                f.write(audio_content)
        else:
            print(f"Text is long, splitting into {len(chunks)} chunks...")
            notify("TTS Clipboard", f"Long text — processing {len(chunks)} chunks...")

            tmp_dir = tempfile.mkdtemp()
            chunk_files = []

            for i, chunk in enumerate(chunks):
                audio_content = synthesize_chunk(client, chunk, voice, audio_config)
                chunk_path = os.path.join(tmp_dir, f"chunk_{i:03d}.mp3")
                with open(chunk_path, "wb") as f:
                    f.write(audio_content)
                chunk_files.append(chunk_path)
                print(f"  Chunk {i + 1}/{len(chunks)} done")

            concat_list = os.path.join(tmp_dir, "concat.txt")
            with open(concat_list, "w") as f:
                for path in chunk_files:
                    f.write(f"file '{path}'\n")

            result = subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-f", "concat", "-safe", "0",
                    "-i", concat_list,
                    "-c:a", "libmp3lame", "-q:a", "2",
                    output_path,
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr[-500:] if result.stderr else "ffmpeg failed")

            for path in chunk_files:
                os.unlink(path)
            os.unlink(concat_list)
            os.rmdir(tmp_dir)

        print(f"Saved to {output_path}")
        subprocess.Popen(["xdg-open", output_path])
        notify("TTS Clipboard", f"Saved: tts_{timestamp}.mp3")

    except Exception as e:
        notify("TTS Clipboard", f"Error: {e}")
        print(f"Error: {e}")


def on_press(key):
    pressed_keys.add(key)
    ctrl = keyboard.Key.ctrl
    alt = keyboard.Key.alt
    try:
        v = keyboard.KeyCode.from_char('v')
    except Exception:
        return

    if ctrl in pressed_keys and alt in pressed_keys and v in pressed_keys:
        with tts_lock:
            threading.Thread(target=speak_clipboard, daemon=True).start()


def on_release(key):
    pressed_keys.discard(key)


print("TTS Clipboard running. Press Ctrl+Alt+V to speak clipboard text. Ctrl+C to quit.")

with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
