from dotenv import load_dotenv
import shutil
from datetime import datetime
import subprocess
from typing import Iterator
import multiprocessing
import threading
import requests
import logging
import asyncio
import os
import traceback
from groq import Groq
from time import sleep
import keyboard
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions, Microphone

load_dotenv()

NEETS_API_KEY = os.environ.get("NEETS_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

messages = [
    {
        "role": "system", 
        "content": """
            You are a helpful AI assitant.
        """.strip()
    }
]
ongoing_transcript = ""

deepgram = DeepgramClient()
groq = Groq(api_key=GROQ_API_KEY)

audio_process = None

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
    def on_utterance_end(self, utterance_end, **kwargs):
        global ongoing_transcript

        print(f"\nUtterance ended. Transcribed text:\n{ongoing_transcript}\n")
        messages.append({"role": "user", "content": ongoing_transcript})
        llm_response()
        ongoing_transcript = ""
    def on_metadata(self, metadata, **kwargs):
        print(f"\n\n{metadata}\n\n")
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
        sleep(0.1)

def interrupt_and_play_stream(audio_stream: Iterator[bytes]):
    global audio_process
    
    print(f"audio_process is not None: {audio_process is not None}")
    if audio_process is not None:
        audio_process.kill()
        audio_process.wait()
        print(f"Process killed!")

    audio_process = subprocess.Popen(
        ["mpv", "--no-cache", "--no-terminal", "--", "fd://0"],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"new audio_process is not None: {audio_process is not None}")

    for chunk in audio_stream:
        if chunk is not None:
            audio_process.stdin.write(chunk)
            audio_process.stdin.flush()

    if audio_process.stdin:
        audio_process.stdin.close()
    audio_process.wait()
    audio_process = None
    print(f"final audio_process is not None: {audio_process is not None}")
def play_stream_async(audio_stream: Iterator[bytes]):
    threading.Thread(target=interrupt_and_play_stream, args=(audio_stream,)).start()
def tts(text: str):
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
    play_stream_async(audio_stream)

def llm_response():
    global messages

    start_time = datetime.now()

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

    # Calculate and print the LLM response time
    llm_response_time_seconds = (datetime.now() - start_time).total_seconds()
    print(f"LLM Response Time: {llm_response_time_seconds}s\n")

    tts_process = multiprocessing.Process(target=tts, args=(response, ))
    tts_process.start()

def main():
    try:
        stt()
    except Exception as e:
        print(f"Error:\n{e}")
        traceback.print_exc()
        return

if __name__ == "__main__":
    main()