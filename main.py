from dotenv import load_dotenv
import shutil
import subprocess
from typing import Iterator
import requests
import logging
import os
from groq import Groq
from time import sleep
import keyboard
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions, Microphone

load_dotenv()

NEETS_API_KEY = os.environ.get("NEETS_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
messages = [{"role": "system", "content": "You are a helpful AI assitant"}]
ongoing_transcript = ""

deepgram = DeepgramClient()
groq = Groq(api_key=GROQ_API_KEY)

def stt():
    dg_connection = deepgram.listen.live.v("1")

    def on_message(self, result, **kwargs):
        global ongoing_transcript
        sentence = result.channel.alternatives[0].transcript
        if sentence.strip() == "":
            return
        if sentence.strip() != ongoing_transcript.strip():
            print(f"speaker:\n{sentence}")
            if result.is_final:
                ongoing_transcript += sentence + " "
                # ongoing_transcript = sentence
    def on_utterance_end(self, utterance_end, **kwargs):
        global ongoing_transcript
        print(f"\nUtterance ended.\n{utterance_end}\nTranscribed text:\n{ongoing_transcript}\n")
        messages.append({"role": "user", "content": ongoing_transcript})
        generate_ai_response()
        ongoing_transcript = ""
    def on_metadata(self, metadata, **kwargs):
        print(f"\n\n{metadata}\n\n")
    def on_speech_started(self, speech_started, **kwargs):
        print(f"\n\n{speech_started}\n\n")
    def on_error(self, error, **kwargs):
        print(f"\n\n{error}\n\n")
    def on_close(self, close, **kwargs):
        print(f"\n\n{close}\n\n")

    def toggle_transcription():
        nonlocal transcribing_on, microphone
        if transcribing_on:
            # Wait for the microphone to close
            microphone.finish()
            dg_connection.finish()
            transcribing_on = False
            print("Transcription stopped.")
        else:
            dg_connection.start(options)
            microphone.start()
            transcribing_on = True
            print("Transcription started.")

    dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
    dg_connection.on(LiveTranscriptionEvents.Metadata, on_metadata)
    dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)
    dg_connection.on(LiveTranscriptionEvents.Error, on_error)
    dg_connection.on(LiveTranscriptionEvents.Close, on_close)

    options = LiveOptions(
        model="nova-2",
        punctuate=True,
        filler_words=True,
        profanity_filter=False,
        language="en-US",
        encoding="linear16",
        channels=1,
        sample_rate=16000,
        interim_results=True,
        utterance_end_ms="1500",
        vad_events=True,
    )

    transcribing_on = False
    microphone = Microphone(dg_connection.send)

    keyboard.add_hotkey('q', toggle_transcription)

    while True:
        sleep(1)

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

def generate_ai_response():
    global messages
    chat_completion = groq.chat.completions.create(
        messages = messages,
        model="mixtral-8x7b-32768",
        temperature=0.9,
        max_tokens=2048,
        stream=True,

        # A stop sequence is a predefined or user-specified text string that
        # signals an AI to stop generating content, ensuring its responses
        # remain focused and concise. Examples include punctuation marks and
        # markers like "[end]".
        # stop=None
    )
    response = ""
    for chunk in chat_completion:
        part = chunk.choices[0].delta.content
        if part is not None:
            response += part

    messages.append({"role": "assistant", "content": response})
    print(f"assistant:\n{response}\n")

    say(response)

def main():
    try:
        stt()
    except Exception as e:
        print(f"Error:\n{e}")
        return

if __name__ == "__main__":
    main()