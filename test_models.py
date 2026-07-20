import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
response = requests.get(url)

try:
    data = response.json()
    print("Available Models supporting generateContent:")
    for model in data.get("models", []):
        if "generateContent" in model.get("supportedGenerationMethods", []):
            print(f"- {model['name'].split('/')[-1]}")
except Exception as e:
    print(f"Error fetching models: {response.text}")
