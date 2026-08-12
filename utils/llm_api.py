import os
import json
import time
from dotenv import load_dotenv

load_dotenv()

# ── Gemini SDK ─────────────────────────────────────────────────────────────────
try:
    from google import genai
except ImportError:
    genai = None

# ── Configuration ──────────────────────────────────────────────────────────────
_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Single ordered model list shared by all functions (preferred → last-resort)
FALLBACK_MODELS = [
    "gemini-2.5-flash",
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
]

ALLOWED_EMOTIONS = [
    "Happy", "Sad", "Romantic", "Angry",
    "Motivational", "Nostalgic", "Calm", "Excited",
]

# ── Module-level helpers ───────────────────────────────────────────────────────

def safe_print(msg: str) -> None:
    """Print safely on Windows cp1252 consoles without UnicodeEncodeError."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", "ignore").decode("ascii"))


def _get_client():
    """Return a genai.Client or None if SDK / key unavailable."""
    if genai is None or not _API_KEY or _API_KEY == "Paste_Your_Real_Gemini_Key_Here":
        return None
    return genai.Client(api_key=_API_KEY)


def _is_temporary_error(message: str) -> bool:
    """True for transient API errors worth retrying."""
    msg = message or ""
    return (
        "503" in msg or "429" in msg or "RESOURCE_EXHAUSTED" in msg
        or "quota" in msg.lower() or "rate" in msg.lower()
        or "UNAVAILABLE" in msg or "high demand" in msg.lower()
        or "temporarily" in msg.lower() or "try again later" in msg.lower()
    )


def _is_quota_error(message: str) -> bool:
    """True specifically for quota / rate-limit errors."""
    msg = message or ""
    return "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower()


def _strip_code_fence(text: str) -> str:
    """Strip ```json ... ``` or ``` ... ``` fences."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def detect_emotion(prompt: str, max_retries: int = 2) -> dict:
    """
    Detect primary emotion, intensity (0.0-1.0), and confidence from a story prompt.
    Returns: {"primary_emotion": str, "emotion_intensity": float, "confidence": float}
    Falls back to safe defaults on any failure.
    """
    default_result = {
        "primary_emotion": "Romantic",
        "emotion_intensity": 0.75,
        "confidence": 0.80,
    }

    if not prompt or not prompt.strip():
        return default_result

    client = _get_client()
    if client is None:
        return default_result

    system_prompt = (
        "You are an expert sentiment and emotion analyzer for musical storytelling.\n"
        "Analyze the user's text input and extract:\n"
        "1. 'primary_emotion': Must be EXACTLY ONE of these categories: "
        f"{ALLOWED_EMOTIONS}.\n"
        "2. 'emotion_intensity': A float 0.0-1.0 representing how strongly the emotion "
        "is expressed (e.g. 0.3 mild, 0.9 intense).\n"
        "3. 'confidence': A float 0.0-1.0 representing your classification confidence.\n\n"
        "Respond ONLY with valid JSON:\n"
        '{"primary_emotion": "Sad", "emotion_intensity": 0.85, "confidence": 0.92}'
    )
    full_prompt = f"{system_prompt}\n\nUser Input: {prompt}"

    for model_name in FALLBACK_MODELS:
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=full_prompt,
                )
                parsed = json.loads(_strip_code_fence(response.text))
                emotion = parsed.get("primary_emotion", "").strip().capitalize()
                if emotion not in ALLOWED_EMOTIONS:
                    emotion = next(
                        (e for e in ALLOWED_EMOTIONS if e.lower() == emotion.lower()),
                        "Romantic",
                    )
                intensity = max(0.0, min(1.0, float(parsed.get("emotion_intensity", 0.75))))
                confidence = max(0.0, min(1.0, float(parsed.get("confidence", 0.85))))
                return {
                    "primary_emotion": emotion,
                    "emotion_intensity": round(intensity, 2),
                    "confidence": round(confidence, 2),
                }
            except Exception as exc:
                err = str(exc)
                if _is_quota_error(err):
                    safe_print(f"[WARN] Quota exceeded on {model_name}, trying next model…")
                    break
                if attempt < max_retries - 1:
                    time.sleep(1)

    return default_result


def generate_hindi_lyrics(
    prompt: str,
    emotion_data: dict = None,
    max_retries: int = 3,
) -> str:
    """
    Generate Hindi lyrics (Devanagari) from a story prompt with optional emotion guidance.
    Returns the lyrics string, or an ERROR: prefixed message on failure.
    """
    if not _API_KEY or _API_KEY == "Paste_Your_Real_Gemini_Key_Here":
        return "ERROR: Gemini API Key is missing or invalid. Please check your .env file."
    if genai is None:
        return "ERROR: The google-genai package is not installed. Run: pip install google-genai"

    emotion_instruction = ""
    if emotion_data and isinstance(emotion_data, dict):
        p_emotion = emotion_data.get("primary_emotion", "Romantic")
        pct = int(emotion_data.get("emotion_intensity", 0.75) * 100)
        emotion_instruction = (
            f"\nIMPORTANT EMOTION DIRECTIVE: The primary emotion is '{p_emotion}' "
            f"at {pct}% intensity. Infuse the Hindi lyrics, poetic imagery, and "
            f"rhyming rhythm deeply with this exact emotion."
        )

    system_prompt = (
        "You are an expert, highly creative music lyricist. "
        "Write a beautiful and rhythmic song based on the user's prompt. "
        "The lyrics MUST be written in the Hindi language (using Devanagari script). "
        "Structure the song clearly with '[Verse 1]', '[Chorus]', '[Verse 2]', "
        "'[Bridge]', and '[Outro]'. "
        "Make sure the lyrics flow well and convey the emotion requested."
        f"{emotion_instruction}"
    )
    full_prompt = f"{system_prompt}\n\nUser Prompt: {prompt}"

    client = _get_client()
    for model_name in FALLBACK_MODELS:
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=full_prompt,
                )
                return response.text.strip()
            except Exception as exc:
                err = str(exc)
                if not _is_temporary_error(err):
                    return f"ERROR generating lyrics: {err}"
                if _is_quota_error(err):
                    safe_print(f"[WARN] Quota exceeded for {model_name}, trying next model…")
                    break
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    safe_print(f"[RETRY] {model_name} — retrying in {wait}s ({attempt+1}/{max_retries})")
                    time.sleep(wait)
                else:
                    safe_print(f"[WARN] {model_name} unavailable after {max_retries} attempts.")

    return (
        "ERROR: Gemini is currently experiencing high demand and all fallback models "
        "are unavailable. Please try again in a few minutes."
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

    if not _API_KEY or _API_KEY == "Paste_Your_Real_Gemini_Key_Here":
        return "ERROR: Gemini API Key is missing or invalid. Please check your .env file."

    if genai is None:
        return "ERROR: The google-genai package is not installed. Run: pip install google-genai"

    instruction = REFINEMENT_PROMPTS.get(action)
    if not instruction:
        return f"ERROR: Invalid refinement action '{action}'."

    full_prompt = f"{instruction}\n\nCURRENT HINDI LYRICS TO REFINE:\n{lyrics}"

    client = _get_client()
    for model_name in FALLBACK_MODELS:
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=full_prompt,
                )
                refined = response.text.strip()
                return refined if refined else lyrics
            except Exception as exc:
                err = str(exc)
                if not _is_temporary_error(err):
                    return f"ERROR refining lyrics: {err}"
                if _is_quota_error(err):
                    safe_print(f"[WARN] Quota exceeded for {model_name}, trying next model…")
                    break
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    safe_print(f"[RETRY] {model_name} — retrying in {wait}s ({attempt+1}/{max_retries})")
                    time.sleep(wait)
                else:
                    safe_print(f"[WARN] {model_name} unavailable after {max_retries} attempts.")

    return (
        "ERROR: Gemini is currently experiencing high demand and all fallback models "
        "are unavailable. Please try again in a few moments."
    )


def recommend_music_parameters(
    emotion_data: dict,
    story_prompt: str,
    lyrics: str,
    max_retries: int = 2,
) -> dict:
    """
    Recommend music generation parameters (mood, tempo, genre, voice_type, pitch)
    based on emotion, story, and lyrics. Returns safe defaults on failure.
    """
    default_result = {
        "mood": "Romantic",
        "tempo": "Medium",
        "genre": "Bollywood",
        "voice_type": "Male",
        "pitch": "Medium",
    }

    client = _get_client()
    if client is None:
        return default_result

    p_emotion = emotion_data.get("primary_emotion", "Romantic") if emotion_data else "Romantic"
    intensity = emotion_data.get("emotion_intensity", 0.75) if emotion_data else 0.75

    system_prompt = (
        "You are an expert music producer and AI composer.\n"
        "Recommend the best music generation parameters based on emotion, story, and lyrics.\n"
        "Choose exactly ONE option from each category:\n"
        "- 'mood': [\"Romantic\", \"Happy\", \"Sad\", \"Angry\", \"Energetic\", \"Chill\"]\n"
        "- 'tempo': [\"Medium\", \"Slow\", \"Fast\"]\n"
        "- 'genre': [\"Bollywood\", \"Pop\", \"Rock\", \"Ghazal\", \"Classical\", \"Hip Hop\"]\n"
        "- 'voice_type': [\"Male\", \"Female\", \"Duet\"]\n"
        "- 'pitch': [\"Medium\", \"Low\", \"High\"]\n\n"
        "Respond ONLY with valid JSON:\n"
        '{"mood": "Sad", "tempo": "Slow", "genre": "Ghazal", "voice_type": "Male", "pitch": "Low"}'
    )
    full_prompt = (
        f"{system_prompt}\n\n"
        f"Detected Emotion: {p_emotion}\n"
        f"Intensity: {intensity}\n"
        f"Story/Prompt: {story_prompt}\n\n"
        f"Lyrics Snippet: {lyrics[:200]}..."
    )

    for model_name in FALLBACK_MODELS:
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=full_prompt,
                )
                parsed = json.loads(_strip_code_fence(response.text))

                def _get_valid(key, options, default):
                    val = parsed.get(key, "").strip().capitalize()
                    if key == "genre" and val.lower() == "hip hop":
                        val = "Hip Hop"
                    return val if val in options else default

                return {
                    "mood":       _get_valid("mood",       ["Romantic", "Happy", "Sad", "Angry", "Energetic", "Chill"], "Romantic"),
                    "tempo":      _get_valid("tempo",      ["Medium", "Slow", "Fast"],                                   "Medium"),
                    "genre":      _get_valid("genre",      ["Bollywood", "Pop", "Rock", "Ghazal", "Classical", "Hip Hop"], "Bollywood"),
                    "voice_type": _get_valid("voice_type", ["Male", "Female", "Duet"],                                   "Male"),
                    "pitch":      _get_valid("pitch",      ["Medium", "Low", "High"],                                    "Medium"),
                }
            except Exception as exc:
                err = str(exc)
                if _is_quota_error(err):
                    safe_print(f"[WARN] Quota exceeded on {model_name}, trying next model…")
                    break
                if attempt < max_retries - 1:
                    time.sleep(1)

    return default_result
