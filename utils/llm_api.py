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

import json

ALLOWED_EMOTIONS = ["Happy", "Sad", "Romantic", "Angry", "Motivational", "Nostalgic", "Calm", "Excited"]

def safe_print(msg: str):
    """Safely print messages on Windows cp1252 consoles without UnicodeEncodeError."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'ignore').decode('ascii'))

def detect_emotion(prompt: str, max_retries: int = 2) -> dict:
    """
    Detects the primary emotion, intensity (0.0 - 1.0), and confidence score from a user story prompt.
    Returns a structured dictionary:
    {
        "primary_emotion": "Sad",
        "emotion_intensity": 0.85,
        "confidence": 0.90
    }
    """
    default_result = {
        "primary_emotion": "Romantic",
        "emotion_intensity": 0.75,
        "confidence": 0.80
    }

    if not prompt or not prompt.strip():
        return default_result

    if not api_key or api_key == "Paste_Your_Real_Gemini_Key_Here" or genai is None:
        return default_result

    detection_system_prompt = (
        "You are an expert sentiment and emotion analyzer for musical storytelling.\n"
        "Analyze the user's text input and extract:\n"
        "1. 'primary_emotion': Must be EXACTLY ONE of these categories: "
        f"{ALLOWED_EMOTIONS}.\n"
        "2. 'emotion_intensity': A float between 0.0 and 1.0 representing how strongly the emotion is expressed (e.g. 0.3 for mild, 0.9 for intense).\n"
        "3. 'confidence': A float between 0.0 and 1.0 representing your confidence in this classification.\n\n"
        "Respond ONLY with a valid JSON object matching this exact format:\n"
        '{"primary_emotion": "Sad", "emotion_intensity": 0.85, "confidence": 0.92}'
    )

    full_prompt = f"{detection_system_prompt}\n\nUser Input: {prompt}"

    fallback_models = [
        "gemini-2.5-flash",
        "gemini-flash-lite-latest",
        "gemini-flash-latest"
    ]

    for model_name in fallback_models:
        for attempt in range(max_retries):
            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=full_prompt
                )
                text_out = response.text.strip()
                # Clean code blocks if present
                if text_out.startswith("```json"):
                    text_out = text_out[7:]
                if text_out.startswith("```"):
                    text_out = text_out[3:]
                if text_out.endswith("```"):
                    text_out = text_out[:-3]
                text_out = text_out.strip()

                parsed = json.loads(text_out)
                emotion = parsed.get("primary_emotion", "").strip().capitalize()
                if emotion not in ALLOWED_EMOTIONS:
                    # Match case-insensitive
                    matched = next((e for e in ALLOWED_EMOTIONS if e.lower() == emotion.lower()), "Romantic")
                    emotion = matched
                
                intensity = float(parsed.get("emotion_intensity", 0.75))
                intensity = max(0.0, min(1.0, intensity))
                
                confidence = float(parsed.get("confidence", 0.85))
                confidence = max(0.0, min(1.0, confidence))

                return {
                    "primary_emotion": emotion,
                    "emotion_intensity": round(intensity, 2),
                    "confidence": round(confidence, 2)
                }
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                    safe_print(f"[WARN] Quota exceeded on {model_name}, switching to next fallback...")
                    break  # Immediately fall back to next model on quota exhaustion
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                break

    return default_result


def generate_hindi_lyrics(prompt: str, emotion_data: dict = None, max_retries: int = 3) -> str:
    """
    Generates Hindi lyrics using Gemini with optional emotion and intensity directives.
    
    Args:
        prompt: The user's story input
        emotion_data: Dictionary with primary_emotion, emotion_intensity, confidence
        max_retries: Maximum number of retry attempts (default: 3)
    
    Returns:
        Generated Hindi lyrics in Devanagari script or an error message
    """
    if not api_key or api_key == "Paste_Your_Real_Gemini_Key_Here":
        return "ERROR: Gemini API Key is missing or invalid. Please check your .env file."
        
    if genai is None:
        return "ERROR: The google-genai package is not installed yet."

    emotion_instruction = ""
    if emotion_data and isinstance(emotion_data, dict):
        p_emotion = emotion_data.get("primary_emotion", "Romantic")
        intensity = emotion_data.get("emotion_intensity", 0.75)
        pct = int(intensity * 100)
        emotion_instruction = (
            f"\nIMPORTANT EMOTION DIRECTIVE: The primary emotion of this song is '{p_emotion}' "
            f"with an emotion intensity level of {pct}%. Infuse the Hindi lyrics, poetic imagery, "
            f"and rhyming rhythm deeply with this exact emotion."
        )

    system_prompt = (
        "You are an expert, highly creative music lyricist. "
        "Write a beautiful and rhythmic song based on the user's prompt. "
        "The lyrics MUST be written in the Hindi language (using Devanagari script). "
        "Structure the song clearly with '[Verse 1]', '[Chorus]', '[Verse 2]', '[Bridge]', and '[Outro]'. "
        "Make sure the lyrics flow well and convey the emotion requested in the prompt."
        f"{emotion_instruction}"
    )
    
    full_prompt = f"{system_prompt}\n\nUser Prompt: {prompt}"
    
    def is_temporary_error(message: str) -> bool:
        message = message or ""
        return (
            "503" in message or
            "429" in message or
            "RESOURCE_EXHAUSTED" in message or
            "quota" in message.lower() or
            "rate" in message.lower() or
            "UNAVAILABLE" in message or
            "high demand" in message.lower() or
            "temporarily" in message.lower() or
            "try again later" in message.lower()
        )

    fallback_models = [
        "gemini-2.5-flash",
        "gemini-flash-lite-latest",
        "gemini-flash-latest"
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

                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                    safe_print(f"[WARN] Quota exceeded for {model_name}, switching to next fallback...")
                    break  # Immediately fall back to next model on quota exhaustion

                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    safe_print(f"[RETRY] Temporary API issue with {model_name}. Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue

                safe_print(f"[WARN] Model {model_name} unavailable after {max_retries} attempts.")
                break

    return (
        "ERROR: Gemini is currently experiencing high demand and all fallback models are unavailable. "
        "Please try again in a few minutes, or refresh the page and generate again."
    )


# ── AI Lyrics Refinement Operations ──────────────────────────────────────────

REFINEMENT_PROMPTS = {
    "improve": (
        "You are an expert Hindi song lyricist and poet.\n"
        "Refine and polish the following Hindi lyrics written in Devanagari script.\n"
        "GOAL: Enhance vocabulary, poetic expression, and natural rhythmic flow.\n"
        "RULES:\n"
        "1. Retain the exact same story, emotion, and core meaning.\n"
        "2. The lyrics MUST remain in Hindi (Devanagari script).\n"
        "3. Preserve the song structure tags like [Verse 1], [Chorus], [Bridge], [Outro].\n"
        "4. Do NOT rewrite into a totally new song; polish and improve the existing lines."
    ),
    "emotional": (
        "You are a master Hindi lyricist specializing in deep emotional songwriting.\n"
        "Refine the following Hindi lyrics written in Devanagari script to heighten their emotional depth, feeling, and heart-touching imagery.\n"
        "RULES:\n"
        "1. Enhance the emotional impact and sentiment of the existing lines.\n"
        "2. The lyrics MUST remain in Hindi (Devanagari script).\n"
        "3. Preserve song structure tags like [Verse 1], [Chorus], [Verse 2], [Bridge], [Outro].\n"
        "4. Keep the story and theme intact while making every line resonate with stronger feeling."
    ),
    "rhyme": (
        "You are a Hindi poet and songwriter focused on meter, rhyme scheme (tukaant/तुकांत), and cadence.\n"
        "Refine the following Hindi lyrics in Devanagari script to ensure strong, harmonious end-rhymes and balanced verse rhythm.\n"
        "RULES:\n"
        "1. Make the rhyming scheme consistent and melodious across stanzas.\n"
        "2. The lyrics MUST remain in Hindi (Devanagari script).\n"
        "3. Preserve the story, meaning, and song structure tags intact."
    ),
    "chorus": (
        "You are a hit Hindi music composer and lyricist.\n"
        "Focus specifically on rewriting and elevating the [Chorus] section of the following Hindi song to make it exceptionally catchy, memorable, and impactful.\n"
        "RULES:\n"
        "1. Rewrite ONLY the [Chorus] section with new, hooky Hindi lines in Devanagari script.\n"
        "2. Keep all other sections ([Verse 1], [Verse 2], [Bridge], [Outro]) unchanged unless minor adjustments are needed for context.\n"
        "3. Ensure the new Chorus blends seamlessly with the existing verses and theme."
    ),
    "add_verse": (
        "You are a creative Hindi lyricist.\n"
        "Expand the following Hindi song by adding ONE new verse (e.g., [Verse 3] or [Verse 2]) that naturally progresses the story and fits the tone of the song.\n"
        "RULES:\n"
        "1. Add a new relevant verse in Devanagari script matching the rhyming style and meter of the existing verses.\n"
        "2. Keep all existing verses, chorus, and bridge intact.\n"
        "3. Place the new verse logically before the bridge or final chorus."
    ),
    "shorten": (
        "You are an editor for Hindi music compositions.\n"
        "Condense and shorten the following Hindi song lyrics into a more compact, punchy version suitable for a shorter track.\n"
        "RULES:\n"
        "1. Trim unnecessary or repetitive lines while keeping the essential story, emotional core, and main chorus intact.\n"
        "2. Keep the script in Devanagari Hindi.\n"
        "3. Output a complete, concise song structure with [Verse 1], [Chorus], and optional [Outro]."
    )
}


def refine_hindi_lyrics(lyrics: str, action: str, max_retries: int = 3) -> str:
    """
    Refines existing Hindi lyrics based on the specified action using dedicated prompts.
    
    Args:
        lyrics: Current Hindi lyrics in Devanagari script
        action: Refinement action key ('improve', 'emotional', 'rhyme', 'chorus', 'add_verse', 'shorten')
        max_retries: Retry count for API calls (default: 3)
        
    Returns:
        Refined Hindi lyrics or an error message
    """
    if not lyrics or not lyrics.strip():
        return "ERROR: No lyrics provided to refine. Please generate lyrics first!"

    if not api_key or api_key == "Paste_Your_Real_Gemini_Key_Here":
        return "ERROR: Gemini API Key is missing or invalid. Please check your .env file."
        
    if genai is None:
        return "ERROR: The google-genai package is not installed yet."

    instruction = REFINEMENT_PROMPTS.get(action)
    if not instruction:
        return f"ERROR: Invalid refinement action '{action}'."

    full_prompt = f"{instruction}\n\nCURRENT HINDI LYRICS TO REFINE:\n{lyrics}"

    def is_temporary_error(message: str) -> bool:
        message = message or ""
        return (
            "503" in message or
            "429" in message or
            "RESOURCE_EXHAUSTED" in message or
            "quota" in message.lower() or
            "rate" in message.lower() or
            "UNAVAILABLE" in message or
            "high demand" in message.lower() or
            "temporarily" in message.lower() or
            "try again later" in message.lower()
        )

    fallback_models = [
        "gemini-2.5-flash",
        "gemini-flash-lite-latest",
        "gemini-flash-latest"
    ]

    for model_name in fallback_models:
        for attempt in range(max_retries):
            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=full_prompt
                )
                refined_text = response.text.strip()
                if refined_text:
                    return refined_text
                else:
                    return lyrics

            except Exception as e:
                error_str = str(e)
                if not is_temporary_error(error_str):
                    return f"ERROR refining lyrics via google-genai SDK: {error_str}"

                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                    safe_print(f"[WARN] Quota exceeded for {model_name}, switching to next fallback...")
                    break  # Immediately fall back to next model on quota exhaustion

                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    safe_print(f"[RETRY] Temporary API issue with {model_name}. Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue

                safe_print(f"[WARN] Model {model_name} unavailable after {max_retries} attempts.")
                break

    return (
        "ERROR: Gemini is currently experiencing high demand and all fallback models are unavailable. "
        "Please try again in a few moments."
    )


def recommend_music_parameters(emotion_data: dict, story_prompt: str, lyrics: str, max_retries: int = 2) -> dict:
    """
    Recommends music parameters based on emotion, story, and lyrics.
    Returns a dictionary with recommended values for mood, tempo, genre, voice_type, and pitch.
    """
    default_result = {
        "mood": "Romantic",
        "tempo": "Medium",
        "genre": "Bollywood",
        "voice_type": "Male",
        "pitch": "Medium"
    }

    if not api_key or api_key == "Paste_Your_Real_Gemini_Key_Here" or genai is None:
        return default_result

    p_emotion = emotion_data.get("primary_emotion", "Romantic") if emotion_data else "Romantic"
    intensity = emotion_data.get("emotion_intensity", 0.75) if emotion_data else 0.75

    system_prompt = (
        "You are an expert music producer and AI composer.\n"
        "Recommend the best music generation parameters based on the detected emotion, user's story, and lyrics.\n"
        "You MUST choose exactly ONE option from each of the following categories:\n"
        "- 'mood': [\"Romantic\", \"Happy\", \"Sad\", \"Angry\", \"Energetic\", \"Chill\"]\n"
        "- 'tempo': [\"Medium\", \"Slow\", \"Fast\"]\n"
        "- 'genre': [\"Bollywood\", \"Pop\", \"Rock\", \"Ghazal\", \"Classical\", \"Hip Hop\"]\n"
        "- 'voice_type': [\"Male\", \"Female\", \"Duet\"]\n"
        "- 'pitch': [\"Medium\", \"Low\", \"High\"]\n\n"
        "Respond ONLY with a valid JSON object matching this exact format:\n"
        '{"mood": "Sad", "tempo": "Slow", "genre": "Ghazal", "voice_type": "Male", "pitch": "Low"}'
    )

    full_prompt = (
        f"{system_prompt}\n\n"
        f"Detected Emotion: {p_emotion}\n"
        f"Intensity: {intensity}\n"
        f"Story/Prompt: {story_prompt}\n\n"
        f"Lyrics Snippet: {lyrics[:200]}..."
    )

    fallback_models = [
        "gemini-2.5-flash",
        "gemini-flash-lite-latest",
        "gemini-flash-latest"
    ]

    for model_name in fallback_models:
        for attempt in range(max_retries):
            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=full_prompt
                )
                text_out = response.text.strip()
                if text_out.startswith("```json"):
                    text_out = text_out[7:]
                if text_out.startswith("```"):
                    text_out = text_out[3:]
                if text_out.endswith("```"):
                    text_out = text_out[:-3]
                text_out = text_out.strip()

                parsed = json.loads(text_out)
                
                def get_valid(key, options, default):
                    val = parsed.get(key, "").strip().capitalize()
                    # Handle multi-word cases like "Hip hop" -> "Hip Hop"
                    if key == "genre" and val.lower() == "hip hop": val = "Hip Hop"
                    return val if val in options else default

                return {
                    "mood": get_valid("mood", ["Romantic", "Happy", "Sad", "Angry", "Energetic", "Chill"], "Romantic"),
                    "tempo": get_valid("tempo", ["Medium", "Slow", "Fast"], "Medium"),
                    "genre": get_valid("genre", ["Bollywood", "Pop", "Rock", "Ghazal", "Classical", "Hip Hop"], "Bollywood"),
                    "voice_type": get_valid("voice_type", ["Male", "Female", "Duet"], "Male"),
                    "pitch": get_valid("pitch", ["Medium", "Low", "High"], "Medium")
                }

            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                    safe_print(f"[WARN] Quota exceeded on {model_name}, switching to next fallback...")
                    break
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                break

    return default_result

