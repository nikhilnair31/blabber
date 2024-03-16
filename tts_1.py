from dotenv import load_dotenv
import shutil
import subprocess
from typing import Iterator
import requests
import json
import os

load_dotenv()
NEETS_API_KEY=os.environ.get("NEETS_API_KEY")

def play_stream(audio_stream: Iterator[bytes]) -> bytes:
    process = subprocess.Popen(
        ["mpv", "--no-cache", "--no-terminal", "--", "fd://0"],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    audio = b""

    for chunk in audio_stream:
        if chunk is not None:
            process.stdin.write(chunk)
            process.stdin.flush()
            audio += chunk

    if process.stdin:
        process.stdin.close()

    process.wait()

def say(text: str):
    response = requests.request(
        method="POST",
        url="https://api.neets.ai/v1/tts",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": NEETS_API_KEY
        },
        json={
            "text": text,
            "voice_id": "vits-eng-11",
            "params": {
                "model": "vits"
            }
        }
    )

    audio_stream = response.iter_content(chunk_size=None)
    play_stream(audio_stream)

say("orange potatoes eat ass?")