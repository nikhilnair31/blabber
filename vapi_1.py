from dotenv import load_dotenv
from vapi_python import Vapi
import keyboard

load_dotenv()

VAPI_API_KEY = os.environ.get("VAPI_API_KEY")

assistant_id = '20b54c74-2fa3-4278-843b-6509194b1b46'
on_call = False

vapi = Vapi(api_key=VAPI_API_KEY)

def toggle_call():
    if not on_call:
        vapi.start(assistant_id=assistant_id)
        print("Call started.")
    else:
        vapi.stop()
        print("Call stopped.")

keyboard.add_hotkey('q', toggle_call)