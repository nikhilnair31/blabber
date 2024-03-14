from dotenv import load_dotenv
import logging
import os
from groq import Groq
import keyboard

load_dotenv()

groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))
messages = [{"role": "system", "content": "You are a helpful AI assitant"}]
transcribed_text = ""

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
        if part is not None:  # Check if part is not None
            print(f"part: {part}")
            response += part
            print(part, end="")

    messages.append({"role": "assistant", "content": response})
    print(f"assistant: {response}")

if __name__ == "__main__":
    messages.append({"role": "user", "content": "will you work now?"})
    generate_ai_response()