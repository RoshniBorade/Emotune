import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("MUSIC_API_KEY")
API_URL = os.getenv("MUSIC_API_URL", "https://api.piapi.ai/api/v1/task")

print(f"API Key: {API_KEY[:20]}..." if API_KEY else "NO API KEY FOUND")
print(f"API URL: {API_URL}")

# Test payload
payload = {
    "model": "Qubico/ace-step",
    "task_type": "txt2audio",
    "input": {
        "style_prompt": "Bollywood",
        "lyrics": "Test lyrics",
        "duration": 60
    }
}

headers = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

print("\n--- Testing PiAPI ---")
print(f"Payload: {payload}")
print(f"Headers: {headers}")

try:
    response = requests.post(API_URL, json=payload, headers=headers, timeout=10)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.text}")
    
except Exception as e:
    print(f"\nError: {e}")
