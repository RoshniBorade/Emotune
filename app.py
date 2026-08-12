import pandas as pd
import streamlit as st
from utils.llm_api import generate_hindi_lyrics, refine_hindi_lyrics, detect_emotion, recommend_music_parameters
from utils.music_api import generate_music_task, poll_music_task
from utils.db import (
    save_song, get_recent_songs, get_song_by_id,
    delete_song, update_song_rating,
    save_evaluation, get_all_evaluations, get_evaluation_stats,
    is_db_connected, get_connection_error,
)

st.set_page_config(page_title="EMOTUNE", layout="wide", page_icon="🎵")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Syne:wght@400;600;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Syne', sans-serif;
    }

    /* ── Deep dark background with subtle vinyl grain ── */
    .stApp {
        background-color: #080810;
        background-image:
            radial-gradient(ellipse 80% 60% at 50% -10%, rgba(200, 30, 90, 0.18) 0%, transparent 70%),
            url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.035'/%3E%3C/svg%3E");
        color: #dde2ee;
        min-height: 100vh;
    }

    /* ── Animated waveform decoration ── */
    .wave-bar-row {
        display: flex;
        align-items: flex-end;
        justify-content: center;
        gap: 4px;
        height: 44px;
        margin: 0 auto 6px;
    }
    .wave-bar {
        width: 4px;
        border-radius: 3px;
        background: linear-gradient(to top, #c8195a, #ff6ba8);
        animation: wavePulse 1.4s ease-in-out infinite;
        opacity: 0.7;
    }
    .wave-bar:nth-child(1)  { height: 18px; animation-delay: 0.0s; }
    .wave-bar:nth-child(2)  { height: 30px; animation-delay: 0.1s; }
    .wave-bar:nth-child(3)  { height: 40px; animation-delay: 0.2s; }
    .wave-bar:nth-child(4)  { height: 28px; animation-delay: 0.3s; }
    .wave-bar:nth-child(5)  { height: 36px; animation-delay: 0.4s; }
    .wave-bar:nth-child(6)  { height: 44px; animation-delay: 0.5s; }
    .wave-bar:nth-child(7)  { height: 32px; animation-delay: 0.4s; }
    .wave-bar:nth-child(8)  { height: 38px; animation-delay: 0.3s; }
    .wave-bar:nth-child(9)  { height: 22px; animation-delay: 0.2s; }
    .wave-bar:nth-child(10) { height: 14px; animation-delay: 0.1s; }
    @keyframes wavePulse {
        0%, 100% { transform: scaleY(0.55); opacity: 0.5; }
        50%       { transform: scaleY(1.0);  opacity: 1.0; }
    }

    /* ── Title ── */
    .emotune-title {
        font-family: 'Bebas Neue', sans-serif;
        font-size: clamp(3.4rem, 8vw, 6.5rem);
        letter-spacing: 10px;
        text-align: center;
        line-height: 1;
        background: linear-gradient(100deg, #ffffff 20%, #ff6ba8 60%, #c8195a 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .emotune-sub {
        text-align: center;
        font-size: 0.95rem;
        letter-spacing: 4px;
        text-transform: uppercase;
        color: #6b7280;
        margin-top: 6px;
        margin-bottom: 2.4rem;
        font-weight: 600;
    }

    /* ── Tab nav ── */
    div[data-baseweb="tab-list"] {
        background: rgba(255,255,255,0.04) !important;
        border-radius: 14px !important;
        border: 1px solid rgba(255,255,255,0.07) !important;
        padding: 4px !important;
        gap: 4px !important;
    }
    div[data-baseweb="tab"] {
        border-radius: 10px !important;
        font-family: 'Syne', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        font-size: 0.85rem !important;
        color: #6b7280 !important;
        transition: all 0.25s ease !important;
    }
    div[data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #c8195a, #7b1e8a) !important;
        color: #fff !important;
    }
    div[data-baseweb="tab-highlight"] { display: none !important; }
    div[data-baseweb="tab-border"]    { display: none !important; }

    /* ── Cards / glass panels ── */
    .glass-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 20px;
        padding: 2rem 2.2rem;
        box-shadow: 0 8px 40px rgba(0,0,0,0.5);
        margin-bottom: 1.4rem;
    }

    /* ── Section labels ── */
    .section-label {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.45rem;
        letter-spacing: 4px;
        color: #ff6ba8;
        margin-bottom: 0.7rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* ── Musical staff divider ── */
    .staff-divider {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 1.6rem 0 1.2rem;
        opacity: 0.35;
    }
    .staff-line { flex: 1; height: 1px; background: #c8195a; }
    .staff-note { font-size: 1.2rem; }

    /* ── Text areas ── */
    .stTextArea textarea {
        background-color: rgba(0,0,0,0.45) !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(200,25,90,0.25) !important;
        border-radius: 14px !important;
        font-family: 'Syne', sans-serif !important;
        font-size: 1rem !important;
        line-height: 1.7 !important;
    }
    .stTextArea textarea:focus {
        border-color: #ff6ba8 !important;
        box-shadow: 0 0 0 3px rgba(200,25,90,0.15) !important;
    }

    /* ── Select boxes ── */
    .stSelectbox > div > div {
        background-color: rgba(0,0,0,0.4) !important;
        border: 1px solid rgba(255,255,255,0.09) !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
    }

    /* ── Primary buttons ── */
    div.stButton > button {
        background: linear-gradient(135deg, #c8195a 0%, #7b1e8a 100%);
        color: #fff;
        border: none;
        border-radius: 12px;
        padding: 0.65rem 2.2rem;
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.2rem;
        letter-spacing: 3px;
        transition: all 0.28s ease;
        box-shadow: 0 6px 22px rgba(200,25,90,0.35);
    }
    div.stButton > button:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 10px 28px rgba(200,25,90,0.55);
        color: #fff;
        border: none;
    }

    /* ── Info / warning ── */
    .stAlert { border-radius: 12px !important; }

    /* ── h2 inside tabs ── */
    h2 {
        font-family: 'Bebas Neue', sans-serif !important;
        font-size: 1.6rem !important;
        letter-spacing: 3px !important;
        color: #e2e8f0 !important;
        border-bottom: 1px solid rgba(200,25,90,0.3) !important;
        padding-bottom: 8px !important;
        margin-bottom: 16px !important;
    }

    /* ── Floating music note accents ── */
    .note-accent {
        position: fixed;
        font-size: 1.4rem;
        opacity: 0.06;
        pointer-events: none;
        animation: floatNote 12s ease-in-out infinite;
    }
    .note-accent:nth-child(1) { top: 12%; left:  4%; animation-delay: 0s;  }
    .note-accent:nth-child(2) { top: 30%; right: 3%; animation-delay: 3s;  }
    .note-accent:nth-child(3) { top: 60%; left:  7%; animation-delay: 6s;  }
    .note-accent:nth-child(4) { top: 78%; right: 6%; animation-delay: 9s;  }
    @keyframes floatNote {
        0%,100% { transform: translateY(0px) rotate(-8deg); }
        50%      { transform: translateY(-22px) rotate(8deg); }
    }

    /* ── Spinning vinyl disc on music page ── */
    .vinyl-ring {
        width: 120px; height: 120px;
        border-radius: 50%;
        border: 3px solid rgba(200,25,90,0.4);
        border-top-color: #ff6ba8;
        animation: spin 3s linear infinite;
        margin: 0 auto 1.2rem;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2.8rem;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
</style>

<!-- Floating note accents -->
<div class="note-accent">♪</div>
<div class="note-accent">♫</div>
<div class="note-accent">𝄞</div>
<div class="note-accent">♩</div>
""", unsafe_allow_html=True)

# ── Header ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="wave-bar-row">
  <div class="wave-bar"></div><div class="wave-bar"></div><div class="wave-bar"></div>
  <div class="wave-bar"></div><div class="wave-bar"></div><div class="wave-bar"></div>
  <div class="wave-bar"></div><div class="wave-bar"></div><div class="wave-bar"></div>
  <div class="wave-bar"></div>
</div>
<h1 class="emotune-title">EMOTUNE</h1>
<p class="emotune-sub">AI-Powered Hindi Music Studio</p>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for k, v in [
    ("step",                   1),
    ("lyrics",                 ""),
    ("song_url",               ""),
    ("story_prompt",           ""),   # persisted so Music Renderer can save it
    ("is_generating_music",    False),
    ("emotion_data",           None),
    ("music_params",           None),
    ("recommendation_accepted",False),
    ("show_recommendations",   False),
    ("last_saved_song_id",     None),  # EMO-XXXXXXXX of the most recently saved song
    ("history_selected_id",   None),  # song currently open in History detail view
]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Pages via tabs ────────────────────────────────────────────────────────
tab_lyrics, tab_music, tab_history, tab_eval = st.tabs(["♪  Lyrics Studio", "🎛  Music Renderer", "📚  Song History", "📊  Evaluation Analytics"])

# ════════════════════════════════════════════════════════════════════════════
# PAGE 1 — LYRICS STUDIO
# ════════════════════════════════════════════════════════════════════════════
with tab_lyrics:
    col_left, col_right = st.columns([1, 1.2], gap="large")

    with col_left:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">🎤 The Story</div>', unsafe_allow_html=True)
        story_prompt = st.text_area(
            "What emotion or story inspires this song?",
            placeholder="E.g., A heartbreak song about a rainy night in Mumbai…",
            height=160,
            label_visibility="collapsed",
        )
        st.markdown('<div class="staff-divider"><div class="staff-line"></div><span class="staff-note">♩</span><div class="staff-line"></div></div>', unsafe_allow_html=True)
        if st.button("✨  Generate Poetic Lyrics", use_container_width=True):
            if not story_prompt.strip():
                st.warning("Please enter a story or prompt first!")
            else:
                with st.spinner("Analyzing emotion & writing poetic Hindi lyrics…"):
                    emotion_res = detect_emotion(story_prompt)
                    st.session_state.emotion_data   = emotion_res
                    st.session_state.story_prompt   = story_prompt  # persist for DB save
                    st.session_state.last_saved_song_id = None       # reset on new song
                    st.session_state.song_url       = ""             # clear previous audio
                    gen_result = generate_hindi_lyrics(story_prompt, emotion_data=emotion_res)
                    st.session_state.lyrics = gen_result
                    st.session_state["lyrics_editor"] = gen_result
                    st.session_state.step = 2

        # Display Detected Emotion UI Card if available
        if st.session_state.get("emotion_data"):
            emo = st.session_state.emotion_data
            p_emotion = emo.get("primary_emotion", "Romantic")
            intensity = emo.get("emotion_intensity", 0.75)
            confidence = emo.get("confidence", 0.85)

            EMOJI_MAP = {
                "Happy": "😊",
                "Sad": "😢",
                "Romantic": "❤️",
                "Angry": "🤬",
                "Motivational": "🔥",
                "Nostalgic": "🌧️",
                "Calm": "🌿",
                "Excited": "⚡"
            }
            emoji = EMOJI_MAP.get(p_emotion, "🎵")
            pct = int(intensity * 100)

            st.markdown('<div class="staff-divider"><div class="staff-line"></div><span class="staff-note">🧠</span><div class="staff-line"></div></div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div style="background:rgba(200,25,90,0.12);border:1px solid rgba(255,107,168,0.25);border-radius:14px;padding:1rem;margin-top:0.8rem;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                    <span style="font-weight:700;letter-spacing:1px;font-size:0.95rem;color:#ff6ba8;">
                        {emoji} Detected Emotion: <span style="color:#fff;">{p_emotion}</span>
                    </span>
                    <span style="font-size:0.8rem;color:#a0aec0;background:rgba(0,0,0,0.3);padding:2px 8px;border-radius:10px;">
                        Confidence: {int(confidence*100)}%
                    </span>
                </div>
                <div style="font-size:0.82rem;color:#cbd5e0;margin-bottom:6px;display:flex;justify-content:space-between;">
                    <span>Emotion Intensity</span>
                    <span style="font-weight:700;color:#ff6ba8;">{pct}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(intensity)

        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        if st.session_state.step >= 2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-label">📝 Lyric Board</div>', unsafe_allow_html=True)
            if st.session_state.lyrics.startswith("ERROR"):
                st.error(st.session_state.lyrics)
            else:
                # Apply pending AI refinement update BEFORE widget is instantiated
                if st.session_state.get("_lyrics_pending"):
                    st.session_state["lyrics_editor"] = st.session_state["_lyrics_pending"]
                    st.session_state["_lyrics_pending"] = None

                # Ensure text area editor state is initialized
                if "lyrics_editor" not in st.session_state:
                    st.session_state["lyrics_editor"] = st.session_state.lyrics

                edited_lyrics = st.text_area(
                    "Edit your Hindi Lyrics:",
                    key="lyrics_editor",
                    height=340,
                    label_visibility="collapsed",
                )
                # Keep lyrics state synced with user's manual edits
                st.session_state.lyrics = edited_lyrics

                # ── AI Refinement Toolkit Section ──
                st.markdown('<div class="staff-divider"><div class="staff-line"></div><span class="staff-note">✨</span><div class="staff-line"></div></div>', unsafe_allow_html=True)
                st.markdown('<div style="font-weight:700;letter-spacing:1px;font-size:0.85rem;color:#ff6ba8;margin-bottom:8px;text-transform:uppercase;">🪄 AI Lyrics Refinement Studio</div>', unsafe_allow_html=True)

                ref_c1, ref_c2, ref_c3 = st.columns(3)
                with ref_c1:
                    btn_improve = st.button("✨ Improve Flow", use_container_width=True, help="Enhance vocabulary and poetic cadence")
                    btn_chorus = st.button("🔄 Rewrite Chorus", use_container_width=True, help="Rewrite Chorus to be catchier")
                with ref_c2:
                    btn_emotional = st.button("❤️ More Emotional", use_container_width=True, help="Heighten emotional depth")
                    btn_add_verse = st.button("➕ Add Verse", use_container_width=True, help="Add a new story-matching verse")
                with ref_c3:
                    btn_rhyme = st.button("🎵 Improve Rhyme", use_container_width=True, help="Improve Hindi rhyming scheme (Tukaant)")
                    btn_shorten = st.button("✂️ Shorten Lyrics", use_container_width=True, help="Condense lyrics into shorter track")

                selected_action = None
                action_desc = ""
                if btn_improve:
                    selected_action = "improve"
                    action_desc = "Improving poetic flow & vocabulary..."
                elif btn_emotional:
                    selected_action = "emotional"
                    action_desc = "Heightening emotional depth..."
                elif btn_rhyme:
                    selected_action = "rhyme"
                    action_desc = "Optimizing Hindi rhyming scheme..."
                elif btn_chorus:
                    selected_action = "chorus"
                    action_desc = "Rewriting the Chorus..."
                elif btn_add_verse:
                    selected_action = "add_verse"
                    action_desc = "Adding a new verse..."
                elif btn_shorten:
                    selected_action = "shorten"
                    action_desc = "Condensing song lyrics..."

                if selected_action:
                    with st.spinner(f"🪄 {action_desc}"):
                        current_text = st.session_state.get("lyrics_editor", st.session_state.lyrics)
                        refined_out = refine_hindi_lyrics(current_text, selected_action)
                        if refined_out.startswith("ERROR"):
                            st.error(refined_out)
                        else:
                            st.session_state.lyrics = refined_out
                            st.session_state["_lyrics_pending"] = refined_out
                            st.rerun()

                st.markdown('<div class="staff-divider"><div class="staff-line"></div><span class="staff-note">♫</span><div class="staff-line"></div></div>', unsafe_allow_html=True)
                st.info("✅ Lyrics ready — head to the **Music Renderer** tab to compose your track.")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="height:420px;display:flex;flex-direction:column;align-items:center;
                        justify-content:center;opacity:0.22;border:2px dashed #c8195a;
                        border-radius:20px;gap:12px;">
                <span style="font-size:3rem;">📝</span>
                <span style="font-family:'Bebas Neue',sans-serif;font-size:1.3rem;
                             letter-spacing:4px;color:#c8195a;">
                    Lyric Board Will Appear Here
                </span>
            </div>
            """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# PAGE 2 — MUSIC RENDERER
# ════════════════════════════════════════════════════════════════════════════
with tab_music:
    if st.session_state.step < 2:
        st.markdown("""
        <div style="height:380px;display:flex;flex-direction:column;align-items:center;
                    justify-content:center;opacity:0.25;border:2px dashed #c8195a;
                    border-radius:20px;gap:14px;margin-top:1rem;">
            <span style="font-size:3rem;">🎛️</span>
            <span style="font-family:'Bebas Neue',sans-serif;font-size:1.3rem;
                         letter-spacing:4px;color:#c8195a;">
                Generate Lyrics First on the Lyrics Studio Tab
            </span>
        </div>
        """, unsafe_allow_html=True)
    else:
        col_params, col_render = st.columns([1, 1.2], gap="large")

        with col_params:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-label">🎛️ Studio Parameters</div>', unsafe_allow_html=True)
            st.caption("Set the vibe for your composition.")

            # Default indices
            mood_options = ["Romantic", "Happy", "Sad", "Angry", "Energetic", "Chill"]
            tempo_options = ["Medium", "Slow", "Fast"]
            voice_options = ["Male", "Female", "Duet"]
            pitch_options = ["Medium", "Low", "High"]
            genre_options = ["Bollywood", "Pop", "Rock", "Ghazal", "Classical", "Hip Hop"]

            if not st.session_state.music_params:
                with st.spinner("Analyzing song for AI recommendations..."):
                    story_prompt = getattr(st.session_state, "story_prompt", "")
                    st.session_state.music_params = recommend_music_parameters(
                        st.session_state.emotion_data, story_prompt, st.session_state.lyrics
                    )

            rec_params = st.session_state.music_params

            if not st.session_state.recommendation_accepted and not st.session_state.show_recommendations:
                st.markdown("### AI Recommendations Available!")
                st.write(f"**Mood:** {rec_params['mood']} | **Tempo:** {rec_params['tempo']} | **Genre:** {rec_params['genre']}")
                st.write(f"**Voice:** {rec_params['voice_type']} | **Pitch:** {rec_params['pitch']}")
                
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Accept AI Recommendations", use_container_width=True):
                        st.session_state.recommendation_accepted = True
                        st.session_state.show_recommendations = True
                        st.rerun()
                with c2:
                    if st.button("⚙️ Customize Manually", use_container_width=True):
                        st.session_state.show_recommendations = True
                        st.rerun()

            if st.session_state.show_recommendations:
                # If they accepted recommendations, set the default index to the recommended value
                # If not, let them start with defaults or previously set values
                
                def get_idx(options, val):
                    try:
                        return options.index(val)
                    except ValueError:
                        return 0

                idx_mood = get_idx(mood_options, rec_params["mood"]) if st.session_state.recommendation_accepted else 0
                idx_tempo = get_idx(tempo_options, rec_params["tempo"]) if st.session_state.recommendation_accepted else 0
                idx_voice = get_idx(voice_options, rec_params["voice_type"]) if st.session_state.recommendation_accepted else 0
                idx_pitch = get_idx(pitch_options, rec_params["pitch"]) if st.session_state.recommendation_accepted else 0
                idx_genre = get_idx(genre_options, rec_params["genre"]) if st.session_state.recommendation_accepted else 0

                p1, p2 = st.columns(2)
                with p1:
                    mood       = st.selectbox("Mood",       mood_options, index=idx_mood)
                    tempo      = st.selectbox("Tempo",      tempo_options, index=idx_tempo)
                    voice_type = st.selectbox("Voice Type", voice_options, index=idx_voice)
                with p2:
                    pitch = st.selectbox("Pitch", pitch_options, index=idx_pitch)
                    style = st.selectbox("Genre/Style", genre_options, index=idx_genre)

                st.markdown('<div class="staff-divider"><div class="staff-line"></div><span class="staff-note">𝄞</span><div class="staff-line"></div></div>', unsafe_allow_html=True)
                render_clicked = st.button("🚀  Render Song", use_container_width=True)
            else:
                render_clicked = False
            st.markdown('</div>', unsafe_allow_html=True)

            if render_clicked:
                st.session_state.is_generating_music = True

        with col_render:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-label">🎧 Final Render</div>', unsafe_allow_html=True)

            if st.session_state.is_generating_music:
                st.markdown("""
                <div class="vinyl-ring">🎵</div>
                """, unsafe_allow_html=True)
                with st.spinner("Warming up the vocal engine…"):
                    tags = f"{style}, {mood.lower()}, {tempo.lower()} tempo, {voice_type.lower()} vocals, {pitch.lower()} pitch"
                    task_result = generate_music_task(st.session_state.lyrics, tags)

                    if task_result["status"] == "success":
                        task_id = task_result["task_id"]
                        st.info(f"Task ID: {task_id}. Synthesizing audio… (Takes ~1–2 minutes)")
                        poll_result = poll_music_task(task_id)

                        if poll_result["status"] == "success":
                            audio_url = poll_result["audio_url"]
                            st.session_state.song_url          = audio_url
                            st.session_state.is_generating_music = False
                            # Store params so the Save button can use them
                            st.session_state["_rendered_params"] = {
                                "mood": mood, "tempo": tempo,
                                "voice_type": voice_type, "pitch": pitch,
                                "genre": style, "tags": tags,
                            }
                            st.success("🎉 Masterpiece Rendered!")
                        else:
                            st.error(f"Failed to generate: {poll_result.get('message')}")
                            st.session_state.is_generating_music = False
                    else:
                        st.error(f"Failed to submit task: {task_result.get('message')}")
                        st.session_state.is_generating_music = False

            if st.session_state.song_url:
                st.markdown("### 💿 Your Track")
                st.audio(st.session_state.song_url, format="audio/mp3")

                st.markdown('<div class="staff-divider"><div class="staff-line"></div><span class="staff-note">💾</span><div class="staff-line"></div></div>', unsafe_allow_html=True)

                # ── Explicit Save button (only shown after successful render) ──
                if st.session_state.last_saved_song_id:
                    st.success(f"✅ Saved to library as **{st.session_state.last_saved_song_id}** — visit the 📚 Song History tab to view it.")

                    # ── Feature 5: Track Evaluation Form ──
                    st.markdown('<div class="staff-divider"><div class="staff-line"></div><span class="staff-note">⭐</span><div class="staff-line"></div></div>', unsafe_allow_html=True)
                    st.markdown('<div style="font-weight:700;letter-spacing:1px;font-size:0.95rem;color:#ff6ba8;margin-bottom:6px;">📊 Track Evaluation & Feedback</div>', unsafe_allow_html=True)
                    st.caption("Rate this track across 4 dimensions to save human evaluation stats.")

                    eval_c1, eval_c2 = st.columns(2)
                    with eval_c1:
                        rate_emo = st.selectbox("1. Emotion-Lyrics Alignment", options=[5, 4, 3, 2, 1], format_func=lambda x: f"{'★'*x} ({x}/5)", key="eval_emo")
                        rate_lyr = st.selectbox("2. Hindi Lyrics Quality", options=[5, 4, 3, 2, 1], format_func=lambda x: f"{'★'*x} ({x}/5)", key="eval_lyr")
                    with eval_c2:
                        rate_mus = st.selectbox("3. Music Quality", options=[5, 4, 3, 2, 1], format_func=lambda x: f"{'★'*x} ({x}/5)", key="eval_mus")
                        rate_sat = st.selectbox("4. Overall Satisfaction", options=[5, 4, 3, 2, 1], format_func=lambda x: f"{'★'*x} ({x}/5)", key="eval_sat")

                    eval_notes = st.text_input("Optional Feedback / Notes:", placeholder="E.g. Vocals match emotion well, composition is catchy", key="eval_notes")

                    if st.button("⭐  Submit Track Evaluation", use_container_width=True):
                        ok_eval, err_eval = save_evaluation(
                            song_id=st.session_state.last_saved_song_id,
                            emotion_alignment=rate_emo,
                            lyric_quality=rate_lyr,
                            music_quality=rate_mus,
                            overall_satisfaction=rate_sat,
                            feedback_text=eval_notes,
                        )
                        if ok_eval:
                            st.success("🎉 Evaluation saved successfully! Check the 📊 Evaluation Analytics tab to view aggregated metrics.")
                        else:
                            st.error(f"Could not save evaluation: {err_eval}")
                else:
                    if st.button("💾  Save to Song Library", use_container_width=True):
                        rp = st.session_state.get("_rendered_params", {})
                        sid, db_err = save_song(
                            story_prompt = st.session_state.get("story_prompt", ""),
                            emotion      = st.session_state.emotion_data or {},
                            lyrics       = st.session_state.lyrics,
                            music_params = rp,
                            audio_url    = st.session_state.song_url,
                        )
                        if db_err:
                            st.warning(f"Could not save: {db_err}")
                        else:
                            st.session_state.last_saved_song_id = sid
                            st.rerun()

            elif not st.session_state.is_generating_music:
                st.markdown("""
                <div style="height:260px;display:flex;flex-direction:column;align-items:center;
                            justify-content:center;opacity:0.25;gap:12px;">
                    <span style="font-size:3.5rem;">🎙️</span>
                    <span style="font-family:'Bebas Neue',sans-serif;font-size:1.1rem;
                                 letter-spacing:3px;color:#c8195a;">
                        Your Track Will Appear Here
                    </span>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# PAGE 3 — SONG HISTORY  (MongoDB)
# ════════════════════════════════════════════════════════════════════════════
with tab_history:

    # ── Connection status banner ──────────────────────────────────────────
    if is_db_connected():
        st.success("🟢  MongoDB connected", icon="✅")
    else:
        st.warning(
            f"🔴  MongoDB not connected — {get_connection_error()}",
        )
        st.info(
            "**How to connect:**\n"
            "1. Create a free cluster at https://www.mongodb.com/cloud/atlas\n"
            "2. Copy your **Connection String**\n"
            "3. Open `.env` and set `MONGODB_URI=<your string>`\n"
            "4. Restart the app with `streamlit run app.py`"
        )

    if not is_db_connected():
        st.stop()

    # ── Fetch all songs ───────────────────────────────────────────────────
    songs, fetch_err = get_recent_songs(limit=50)
    if fetch_err:
        st.error(f"Could not load songs: {fetch_err}")
        st.stop()

    # ── Empty state ───────────────────────────────────────────────────────
    if not songs:
        st.markdown("""
        <div style="height:300px;display:flex;flex-direction:column;align-items:center;
                    justify-content:center;gap:14px;opacity:0.3;">
            <span style="font-size:4rem;">🎵</span>
            <span style="font-family:'Bebas Neue',sans-serif;font-size:1.3rem;
                         letter-spacing:5px;color:#c8195a;">
                No songs saved yet
            </span>
            <span style="font-size:0.9rem;color:#6b7280;">Render & save your first track in the Music Renderer tab</span>
        </div>
        """, unsafe_allow_html=True)

    else:
        # ── Layout: sidebar list  |  detail panel ────────────────────────
        hist_list_col, hist_detail_col = st.columns([1, 2], gap="large")

        with hist_list_col:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-label">📚 Song Library</div>', unsafe_allow_html=True)
            st.caption(f"{len(songs)} track{'s' if len(songs) != 1 else ''} saved")
            st.markdown('<div class="staff-divider"><div class="staff-line"></div><span class="staff-note">♪</span><div class="staff-line"></div></div>', unsafe_allow_html=True)

            EMOTION_EMOJI = {
                "Happy": "😊", "Sad": "😢", "Romantic": "❤️",
                "Angry": "🤬", "Motivational": "🔥", "Nostalgic": "🌧️",
                "Calm": "🌿", "Excited": "⚡",
            }

            for song in songs:
                sid          = song["song_id"]
                date_label   = song.get("created_at_str", "")[:11]
                emo_name     = song.get("emotion", {}).get("primary_emotion", "")
                genre_label  = song.get("music_params", {}).get("genre", "")
                emo_emoji    = EMOTION_EMOJI.get(emo_name, "🎵")
                rating_stars = "★" * (song.get("rating") or 0)
                is_selected  = (st.session_state.history_selected_id == sid)

                btn_label = (
                    f"{emo_emoji} {date_label}\n"
                    f"{emo_name} · {genre_label}\n"
                    f"{rating_stars or '☆ unrated'}"
                )
                btn_style = "background:rgba(200,25,90,0.18);" if is_selected else ""

                st.markdown(
                    f'<div style="{btn_style}border-radius:10px;margin-bottom:2px;">',
                    unsafe_allow_html=True,
                )
                if st.button(btn_label, key=f"sel_{sid}", use_container_width=True):
                    st.session_state.history_selected_id = sid
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

        # ── Detail panel ──────────────────────────────────────────────────
        with hist_detail_col:
            sel_id = st.session_state.history_selected_id

            if sel_id is None:
                # No song selected yet — prompt user
                st.markdown("""
                <div style="height:380px;display:flex;flex-direction:column;align-items:center;
                            justify-content:center;opacity:0.25;border:2px dashed #c8195a;
                            border-radius:20px;gap:14px;">
                    <span style="font-size:3rem;">◀️</span>
                    <span style="font-family:'Bebas Neue',sans-serif;font-size:1.1rem;
                                 letter-spacing:4px;color:#c8195a;">
                        Select a song to view details
                    </span>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Load full song document
                sel_song, sel_err = get_song_by_id(sel_id)
                if sel_err:
                    st.error(f"Could not load song: {sel_err}")
                else:
                    emo     = sel_song.get("emotion", {})
                    params  = sel_song.get("music_params", {})
                    p_emo   = emo.get("primary_emotion", "—")
                    intens  = int(emo.get("emotion_intensity", 0) * 100)
                    conf    = int(emo.get("confidence", 0) * 100)

                    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

                    # Header row
                    hdr_c1, hdr_c2 = st.columns([3, 1])
                    with hdr_c1:
                        st.markdown(
                            f'<div class="section-label">{EMOTION_EMOJI.get(p_emo, "🎵")} {p_emo} &nbsp;·&nbsp; {params.get("genre","—")}</div>',
                            unsafe_allow_html=True,
                        )
                        st.caption(f"📅 {sel_song.get('created_at_str', '')}  ·  ID: {sel_id}")
                    with hdr_c2:
                        # Rating widget
                        current_rating = sel_song.get("rating") or 0
                        new_rating = st.selectbox(
                            "★ Rate",
                            options=[0, 1, 2, 3, 4, 5],
                            index=current_rating,
                            format_func=lambda x: "☆ Unrated" if x == 0 else "★" * x,
                            key=f"rate_{sel_id}",
                        )
                        if new_rating != current_rating and new_rating > 0:
                            ok, rate_err = update_song_rating(sel_id, new_rating)
                            if rate_err:
                                st.error(rate_err)
                            else:
                                st.rerun()

                    st.markdown('<div class="staff-divider"><div class="staff-line"></div><span class="staff-note">📝</span><div class="staff-line"></div></div>', unsafe_allow_html=True)

                    # Story prompt
                    story = sel_song.get("story_prompt", "")
                    if story:
                        st.markdown(
                            '<span style="color:#ff6ba8;font-weight:700;font-size:0.85rem;'
                            'letter-spacing:1px;text-transform:uppercase;">Original Story</span>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f'<div style="background:rgba(0,0,0,0.3);border-radius:10px;'
                            f'padding:10px 14px;font-size:0.9rem;line-height:1.65;'
                            f'color:#a0aec0;font-style:italic;margin-bottom:10px;">'
                            f'{story}</div>',
                            unsafe_allow_html=True,
                        )

                    # Emotion metrics
                    em_c1, em_c2, em_c3 = st.columns(3)
                    em_c1.metric("Emotion",    p_emo)
                    em_c2.metric("Intensity",  f"{intens}%")
                    em_c3.metric("Confidence", f"{conf}%")

                    st.markdown('<div class="staff-divider"><div class="staff-line"></div><span class="staff-note">🎶</span><div class="staff-line"></div></div>', unsafe_allow_html=True)

                    # Music params chips
                    def _chip(label, val):
                        return (
                            f'<span style="background:rgba(200,25,90,0.15);'
                            f'border:1px solid rgba(255,107,168,0.25);'
                            f'border-radius:20px;padding:3px 12px;font-size:0.82rem;'
                            f'color:#ff6ba8;margin-right:6px;white-space:nowrap;">'
                            f'<b>{label}</b> {val}</span>'
                        )
                    chips_html = (
                        _chip("Mood",   params.get("mood",       "—")) +
                        _chip("Tempo",  params.get("tempo",      "—")) +
                        _chip("Genre",  params.get("genre",      "—")) +
                        _chip("Voice",  params.get("voice_type", "—")) +
                        _chip("Pitch",  params.get("pitch",      "—"))
                    )
                    st.markdown(
                        f'<div style="margin-bottom:14px;flex-wrap:wrap;display:flex;gap:4px;">'
                        f'{chips_html}</div>',
                        unsafe_allow_html=True,
                    )

                    # Full lyrics
                    st.markdown(
                        '<span style="color:#ff6ba8;font-weight:700;font-size:0.85rem;'
                        'letter-spacing:1px;text-transform:uppercase;">Full Lyrics</span>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<div style="background:rgba(0,0,0,0.35);border:1px solid rgba(255,107,168,0.12);'
                        f'border-radius:14px;padding:14px 18px;font-size:0.9rem;'
                        f'line-height:1.8;color:#e2e8f0;white-space:pre-wrap;'
                        f'max-height:280px;overflow-y:auto;margin-bottom:12px;">'
                        f'{sel_song.get("lyrics", "")}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                    # Audio player
                    audio_url = sel_song.get("audio_url")
                    if audio_url:
                        st.markdown(
                            '<span style="color:#ff6ba8;font-weight:700;font-size:0.85rem;'
                            'letter-spacing:1px;text-transform:uppercase;">Audio Track</span>',
                            unsafe_allow_html=True,
                        )
                        st.audio(audio_url, format="audio/mp3")
                    else:
                        st.caption("🔇 No audio URL saved for this track.")

                    st.markdown('<div class="staff-divider"><div class="staff-line"></div><span class="staff-note">⚙️</span><div class="staff-line"></div></div>', unsafe_allow_html=True)

                    # Action buttons
                    act_c1, act_c2, act_c3 = st.columns(3)

                    with act_c1:
                        if st.button("📋  Load into Studio", key=f"load_{sel_id}", use_container_width=True):
                            st.session_state.lyrics          = sel_song.get("lyrics", "")
                            st.session_state["_lyrics_pending"] = sel_song.get("lyrics", "")
                            st.session_state.story_prompt    = sel_song.get("story_prompt", "")
                            st.session_state.emotion_data    = sel_song.get("emotion", {})
                            st.session_state.step            = 2
                            st.session_state.song_url        = sel_song.get("audio_url", "") or ""
                            st.session_state.last_saved_song_id = sel_id
                            st.success("✅ Loaded! Switch to the Lyrics Studio tab.")
                            st.rerun()

                    with act_c2:
                        # Download lyrics as .txt
                        lyrics_bytes = sel_song.get("lyrics", "").encode("utf-8")
                        st.download_button(
                            label="⬇️  Download Lyrics",
                            data=lyrics_bytes,
                            file_name=f"{sel_id}_lyrics.txt",
                            mime="text/plain",
                            key=f"dl_{sel_id}",
                            use_container_width=True,
                        )

                    with act_c3:
                        if st.button("🗑️  Delete Song", key=f"del_{sel_id}", use_container_width=True):
                            ok, del_err = delete_song(sel_id)
                            if ok:
                                st.session_state.history_selected_id = None
                                st.success("Song deleted.")
                                st.rerun()
                            else:
                                st.error(f"Delete failed: {del_err}")

                    st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# PAGE 4 — EVALUATION & ANALYTICS DASHBOARD
# ════════════════════════════════════════════════════════════════════════════
with tab_eval:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">📊 Evaluation & Performance Analytics</div>', unsafe_allow_html=True)
    st.caption("Quantitative analytics and empirical human evaluation results computed directly from database records.")

    if not is_db_connected():
        st.warning(f"🔴 MongoDB not connected — {get_connection_error()}")
        st.stop()

    stats, stats_err = get_evaluation_stats()
    eval_songs, songs_err = get_all_evaluations()

    if stats_err or songs_err:
        st.error(f"Could not load evaluation statistics: {stats_err or songs_err}")
        st.stop()

    if stats.get("total_evaluated", 0) == 0:
        st.markdown("""
        <div style="height:300px;display:flex;flex-direction:column;align-items:center;
                    justify-content:center;gap:14px;opacity:0.4;">
            <span style="font-size:3.5rem;">📊</span>
            <span style="font-family:'Bebas Neue',sans-serif;font-size:1.3rem;
                         letter-spacing:4px;color:#ff6ba8;">
                No Evaluated Songs Yet
            </span>
            <span style="font-size:0.9rem;color:#a0aec0;">
                Render a song in the Music Renderer tab and submit your evaluation to see live metrics here.
            </span>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Top KPI metric cards
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Evaluated Tracks", f"{stats['total_evaluated']}")
        m2.metric("Overall Satisfaction", f"{stats['avg_overall_satisfaction']} / 5.0")
        m3.metric("Emotion Alignment", f"{stats['avg_emotion_alignment']} / 5.0")
        m4.metric("Lyrics Quality", f"{stats['avg_lyric_quality']} / 5.0")
        m5.metric("Music Quality", f"{stats['avg_music_quality']} / 5.0")

        st.markdown('<div class="staff-divider"><div class="staff-line"></div><span class="staff-note">📈</span><div class="staff-line"></div></div>', unsafe_allow_html=True)

        # Charts Section
        c_left, c_right = st.columns(2, gap="large")

        with c_left:
            st.markdown("### 📊 Dimension Averages")
            dim_df = pd.DataFrame({
                "Dimension": ["Emotion Alignment", "Lyrics Quality", "Music Quality", "Overall Satisfaction"],
                "Average Score (1-5)": [
                    stats["avg_emotion_alignment"],
                    stats["avg_lyric_quality"],
                    stats["avg_music_quality"],
                    stats["avg_overall_satisfaction"]
                ]
            }).set_index("Dimension")
            st.bar_chart(dim_df, color="#ff6ba8")

        with c_right:
            st.markdown("### ⭐ Rating Distribution (Overall Satisfaction)")
            counts = stats.get("rating_counts", {})
            dist_df = pd.DataFrame({
                "Star Rating": ["1 Star", "2 Stars", "3 Stars", "4 Stars", "5 Stars"],
                "Count": [counts.get(1, 0), counts.get(2, 0), counts.get(3, 0), counts.get(4, 0), counts.get(5, 0)]
            }).set_index("Star Rating")
            st.bar_chart(dist_df, color="#7b1e8a")

        # Emotion Breakdown Section if available
        emo_stats = stats.get("emotion_stats", {})
        if emo_stats:
            st.markdown('<div class="staff-divider"><div class="staff-line"></div><span class="staff-note">🎭</span><div class="staff-line"></div></div>', unsafe_allow_html=True)
            st.markdown("### 🎭 Performance by Primary Emotion")
            emo_rows = []
            for emo_name, e_data in emo_stats.items():
                emo_rows.append({
                    "Primary Emotion": emo_name,
                    "Tracks Evaluated": e_data["count"],
                    "Avg Emotion Alignment": e_data["avg_alignment"],
                    "Avg Overall Satisfaction": e_data["avg_satisfaction"]
                })
            emo_df = pd.DataFrame(emo_rows).set_index("Primary Emotion")
            st.dataframe(emo_df, use_container_width=True)

        st.markdown('<div class="staff-divider"><div class="staff-line"></div><span class="staff-note">📋</span><div class="staff-line"></div></div>', unsafe_allow_html=True)
        st.markdown("### 📝 Detailed Human Evaluation Records")
        st.caption("Transparent evaluation log stored per track in MongoDB.")

        table_rows = []
        for song in eval_songs:
            e = song.get("evaluation", {})
            emo = song.get("emotion", {})
            table_rows.append({
                "Song ID": song.get("song_id"),
                "Primary Emotion": emo.get("primary_emotion", "—"),
                "Emotion Alignment": f"{e.get('emotion_alignment', '—')}/5",
                "Lyrics Quality": f"{e.get('lyric_quality', '—')}/5",
                "Music Quality": f"{e.get('music_quality', '—')}/5",
                "Overall Satisfaction": f"{e.get('overall_satisfaction', '—')}/5",
                "User Feedback Notes": e.get("feedback_text", "") or "—",
                "Evaluated Date": song.get("created_at_str", "")[:11] if "created_at_str" in song else "—"
            })

        df_logs = pd.DataFrame(table_rows)
        st.dataframe(df_logs, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)