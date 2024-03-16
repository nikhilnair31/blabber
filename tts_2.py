import speech_recognition as sr
import pyttsx3
import threading
from time import sleep

# Initialize the Text-to-Speech engine
engine = pyttsx3.init()

# Function to speak a given text
def speak(text):
    engine.say(text)
    engine.runAndWait()

# Function to detect speech
def detect_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)  # Adjust for ambient noise
        print("Listening for speech...")
        audio = recognizer.listen(source)
    try:
        text = recognizer.recognize_google(audio)
        print("Detected speech:", text)
        return text
    except sr.UnknownValueError:
        print("Speech not detected")
        return None
    except sr.RequestError as e:
        print("Could not request results; {0}".format(e))
        return None

# Function to speak text with interruption detection
def speak_with_interrupt(text):
    # Create a thread for speech detection
    speech_thread = threading.Thread(target=detect_speech)
    speech_thread.start()

    # Speak the text
    sleep(3)
    speak(text)

    # Wait for speech detection thread to finish
    speech_thread.join()

# Test the function
text_to_speak = """
Hello, I am a text-to-speech engine.
Hello, I am a text-to-speech engine.
Hello, I am a text-to-speech engine.
Hello, I am a text-to-speech engine.
Hello, I am a text-to-speech engine.
Hello, I am a text-to-speech engine."""
detected_speech = speak_with_interrupt(text_to_speak)
if detected_speech:
    print("Detected speech during TTS:", detected_speech)
