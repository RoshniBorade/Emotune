import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# Music API Key from PiAPI (Workspace -> API Keys)
API_KEY = os.getenv("MUSIC_API_KEY")
API_URL = os.getenv("MUSIC_API_URL", "https://api.piapi.ai/api/v1/task") 

def generate_music_task(prompt: str, tags: str) -> dict:
    """
    Step 1: Submit the generation task to PiAPI using the Qubico/ace-step model.
    """
    if not API_KEY or API_KEY == "Paste_Your_Secret_PiAPI_Key_Here" or API_KEY.startswith("http"):
        return {"status": "error", "message": "Missing or invalid MUSIC_API_KEY in .env. Please just put the secret key string."}

    # Payload matching the PiAPI Ace Step documentation
    payload = {
        "model": "Qubico/ace-step",
        "task_type": "txt2audio",
        "input": {
            "style_prompt": tags, # User selected styles
            "lyrics": prompt,     # Generated Hindi lyrics
            "duration": 60        # Generating ~1 minute
        }
    }
    
    headers = {
        "x-api-key": API_KEY, # PiAPI uses x-api-key header
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=30)
        
        # Try to parse JSON response regardless of status code
        try:
            data = response.json()
        except:
            data = {"error": response.text}
        
        # Check for HTTP errors
        if response.status_code >= 400:
            error_msg = data.get("message") or data.get("error") or f"HTTP {response.status_code}: {response.text}"
            return {"status": "error", "message": f"API Error: {error_msg}"}
        
        # PiAPI returns "code": 200 and data contains task_id
        if data.get("code") == 200 and data.get("data"):
            task_id = data["data"]["task_id"]
            return {"status": "success", "task_id": task_id}
        else:
             return {"status": "error", "message": data.get("message", "Unknown error submitting task")}
             
    except requests.exceptions.Timeout:
        return {"status": "error", "message": "Request timeout: The API took too long to respond. Please try again."}
    except requests.exceptions.ConnectionError:
        return {"status": "error", "message": "Connection error: Unable to reach the music API. Please check your internet connection."}
    except Exception as e:
        return {"status": "error", "message": f"Unexpected error: {str(e)}"}

def poll_music_task(task_id: str, timeout: int = 300) -> dict:
    """
    Step 2: Poll for the task status until complete or timeout.
    """
    headers = {"x-api-key": API_KEY}
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            # Polling endpoint for PiAPI is typically GET /api/v1/task/{task_id}
            response = requests.get(f"{API_URL}/{task_id}", headers=headers, timeout=30)
            
            # Try to parse JSON response
            try:
                data = response.json()
            except:
                data = {"error": response.text}
            
            # Check for HTTP errors
            if response.status_code >= 400:
                error_msg = data.get("message") or data.get("error") or f"HTTP {response.status_code}"
                return {"status": "error", "message": f"Polling failed: {error_msg}"}
            
            if data.get("code") == 200:
                task_status = data["data"]["status"]
                
                if task_status == "completed":
                    # For PiAPI Ace-step, the output audio URL is usually in data.output.audio_url
                    output_data = data["data"].get("output", {})
                    audio_url = output_data.get("audio_url")
                    
                    if audio_url:
                        return {"status": "success", "audio_url": audio_url}
                    else:
                        return {"status": "error", "message": "Task completed but no audio URL found."}
                    
                elif task_status == "failed":
                     error_detail = data["data"].get("error", "Unknown error")
                     return {"status": "error", "message": f"Task failed: {error_detail}"}
            
            # If "pending" or "processing", wait and try again
            time.sleep(5)
            
        except requests.exceptions.Timeout:
            return {"status": "error", "message": "Polling timeout: The API took too long to respond."}
        except requests.exceptions.ConnectionError:
            return {"status": "error", "message": "Connection error during polling. Please try again."}
        except Exception as e:
            return {"status": "error", "message": f"Polling error: {str(e)}"}
            
    return {"status": "error", "message": "Polling timed out after 5 minutes. Your task may still be processing."}
