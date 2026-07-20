import os
import time
from dotenv import load_dotenv

load_dotenv()

# We will import the NEW officially supported sdk
try:
    from google import genai
except ImportError:
    genai = None

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")

def generate_hindi_lyrics(prompt: str, max_retries: int = 3) -> str:
    """
    Generates Hindi lyrics using the brand new officially supported google-genai package.
    Includes retry logic with exponential backoff and fallback models for temporary Gemini outages.
    
    Args:
        prompt: The user's input for lyrics generation
        max_retries: Maximum number of retry attempts per model (default: 3)
    
    Returns:
        Generated Hindi lyrics or an error message
    """
    if not api_key or api_key == "Paste_Your_Real_Gemini_Key_Here":
        return "ERROR: Gemini API Key is missing or invalid. Please check your .env file."
        
    if genai is None:
        return "ERROR: The google-genai package is not installed yet."

    system_prompt = (
        "You are an expert, highly creative music lyricist. "
        "Write a beautiful and rhythmic song based on the user's prompt. "
        "The lyrics MUST be written in the Hindi language (using Devanagari script). "
        "Structure the song clearly with '[Verse 1]', '[Chorus]', '[Verse 2]', '[Bridge]', and '[Outro]'. "
        "Make sure the lyrics flow well and convey the emotion requested in the prompt."
    )
    
    full_prompt = f"{system_prompt}\n\nUser Prompt: {prompt}"
    
    def is_temporary_error(message: str) -> bool:
        message = message or ""
        return (
            "503" in message or
            "UNAVAILABLE" in message or
            "high demand" in message.lower() or
            "temporarily" in message.lower() or
            "try again later" in message.lower()
        )

    fallback_models = [
        "gemini-2.5-flash",
        "gemini-2.1",
        "gemini-1.5-mini"
    ]

    for model_name in fallback_models:
        for attempt in range(max_retries):
            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=full_prompt
                )
                return response.text.strip()

            except Exception as e:
                error_str = str(e)
                if not is_temporary_error(error_str):
                    return f"ERROR generating lyrics via google-genai SDK: {error_str}"

                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"🔄 Temporary API issue with {model_name}. Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue

                print(f"⚠️ Model {model_name} unavailable after {max_retries} attempts: {error_str}")
                break

    return (
        "ERROR: Gemini is currently experiencing high demand and all fallback models are unavailable. "
        "Please try again in a few minutes, or refresh the page and generate again."
    )
