from dotenv import load_dotenv
import requests
import os

load_dotenv()

VAPI_API_KEY = os.environ.get("VAPI_API_KEY")

url = "https://api.vapi.ai/assistant"

headers = {"Authorization": f"Bearer {VAPI_API_KEY}"}

response = requests.request("GET", url, headers=headers)

print(response.text)