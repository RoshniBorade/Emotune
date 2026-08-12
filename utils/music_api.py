import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# ── Configuration (read once at import time) ───────────────────────────────────
API_KEY = os.getenv("MUSIC_API_KEY", "")
API_URL = os.getenv("MUSIC_API_URL", "https://api.piapi.ai/api/v1/task")


def generate_music_task(prompt: str, tags: str) -> dict:
    """
    Step 1: Submit a music generation task to PiAPI (Qubico/ace-step model).
    Returns {"status": "success", "task_id": str} or {"status": "error", "message": str}.
    """
    if not API_KEY or API_KEY == "Paste_Your_Secret_PiAPI_Key_Here" or API_KEY.startswith("http"):
        return {
            "status": "error",
            "message": "Missing or invalid MUSIC_API_KEY in .env. Please set the secret key string.",
        }

    payload = {
        "model": "Qubico/ace-step",
        "task_type": "txt2audio",
        "input": {
            "style_prompt": tags,   # user-selected styles
            "lyrics": prompt,        # generated Hindi lyrics
            "duration": 60,          # ~1 minute track
        },
    }
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=30)

        try:
            data = response.json()
        except Exception:
            data = {"error": response.text}

        if response.status_code >= 400:
            error_msg = data.get("message") or data.get("error") or f"HTTP {response.status_code}"
            if "credits" in str(error_msg).lower():
                return {
                    "status": "error",
                    "message": "PiAPI account has run out of credits. Please top up at piapi.ai.",
                }
            return {"status": "error", "message": f"API Error: {error_msg}"}

        if data.get("code") == 200 and data.get("data"):
            return {"status": "success", "task_id": data["data"]["task_id"]}

        return {"status": "error", "message": data.get("message", "Unknown error submitting task")}

    except requests.exceptions.Timeout:
        return {"status": "error", "message": "Request timed out. Please try again."}
    except requests.exceptions.ConnectionError:
        return {"status": "error", "message": "Connection error: unable to reach PiAPI. Check your internet."}
    except Exception as exc:
        return {"status": "error", "message": f"Unexpected error: {exc}"}


def poll_music_task(task_id: str, timeout: int = 300) -> dict:
    """
    Step 2: Poll PiAPI until the task completes or timeout expires.
    Returns {"status": "success", "audio_url": str} or {"status": "error", "message": str}.
    """
    headers = {"x-api-key": API_KEY}
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{API_URL}/{task_id}", headers=headers, timeout=30)

            try:
                data = response.json()
            except Exception:
                data = {"error": response.text}

            if response.status_code >= 400:
                error_msg = data.get("message") or data.get("error") or f"HTTP {response.status_code}"
                return {"status": "error", "message": f"Polling failed: {error_msg}"}

            if data.get("code") == 200:
                task_status = data["data"]["status"]

                if task_status == "completed":
                    audio_url = data["data"].get("output", {}).get("audio_url")
                    if audio_url:
                        return {"status": "success", "audio_url": audio_url}
                    return {"status": "error", "message": "Task completed but no audio URL found."}

                if task_status == "failed":
                    error_detail = data["data"].get("error", "Unknown error")
                    return {"status": "error", "message": f"Task failed: {error_detail}"}

            # "pending" or "processing" — wait and retry
            time.sleep(5)

        except requests.exceptions.Timeout:
            return {"status": "error", "message": "Polling timed out. Please try again."}
        except requests.exceptions.ConnectionError:
            return {"status": "error", "message": "Connection error during polling. Please try again."}
        except Exception as exc:
            return {"status": "error", "message": f"Polling error: {exc}"}

    return {"status": "error", "message": "Polling timed out after 5 minutes. Your task may still be processing."}

