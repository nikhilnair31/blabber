from dotenv import load_dotenv
import logging
import os
from groq import Groq
from time import sleep
import keyboard
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions, Microphone

load_dotenv()

deepgram = DeepgramClient()
groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))
messages = [{"role": "system", "content": "You are a helpful AI assitant"}]
transcribed_text = ""

def main():
    try:
        dg_connection = deepgram.listen.live.v("1")

        def on_message(self, result, **kwargs):
            global transcribed_text
            sentence = result.channel.alternatives[0].transcript
            if sentence.strip() == "":
                return
            if sentence.strip() != transcribed_text.strip():
                print(f"speaker: {sentence}")
                # transcribed_text += sentence + " "
                transcribed_text = sentence
                messages.append({"role": "user", "content": transcribed_text})

        def on_utterance_end(self, utterance_end, **kwargs):
            global transcribed_text
            print(f"\nUtterance ended. Transcribed text:\n{transcribed_text}\n")
            transcribed_text = ""

        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)

        options = LiveOptions(
            model="nova-2",
            punctuate=True,
            language="en-US",
            encoding="linear16",
            channels=1,
            sample_rate=16000,
            interim_results=True,
            utterance_end_ms="2000",
            vad_events=True,
        )

        transcribing_on = False
        microphone = Microphone(dg_connection.send)

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

        # Start or stop transcription on pressing 'Q' key
        keyboard.add_hotkey('q', toggle_transcription)

        # Infinite loop to keep the program running
        while True:
            sleep(1)

    except Exception as e:
        print(f"Could not open socket: {e}")
        return

if __name__ == "__main__":
    main()