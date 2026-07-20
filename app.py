import streamlit as st
from utils.llm_api import generate_hindi_lyrics
from utils.music_api import generate_music_task, poll_music_task

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

# ── Session state ─────────────────────────────────────────────────────────
for k, v in [("step", 1), ("lyrics", ""), ("song_url", ""), ("is_generating_music", False)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Pages via tabs ────────────────────────────────────────────────────────
tab_lyrics, tab_music = st.tabs(["♪  Lyrics Studio", "🎛  Music Renderer"])

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
                with st.spinner("Writing poetic Hindi lyrics…"):
                    st.session_state.lyrics = generate_hindi_lyrics(story_prompt)
                    st.session_state.step = 2
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        if st.session_state.step >= 2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-label">📝 Lyric Board</div>', unsafe_allow_html=True)
            if st.session_state.lyrics.startswith("ERROR"):
                st.error(st.session_state.lyrics)
            else:
                st.session_state.lyrics = st.text_area(
                    "Edit your Hindi Lyrics:",
                    value=st.session_state.lyrics,
                    height=400,
                    label_visibility="collapsed",
                )
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

            p1, p2 = st.columns(2)
            with p1:
                mood       = st.selectbox("Mood",       ["Romantic", "Happy", "Sad", "Angry", "Energetic", "Chill"])
                tempo      = st.selectbox("Tempo",      ["Medium", "Slow", "Fast"])
                voice_type = st.selectbox("Voice Type", ["Male", "Female", "Duet"])
            with p2:
                pitch = st.selectbox("Pitch", ["Medium", "Low", "High"])
                style = st.selectbox("Genre/Style", ["Bollywood", "Pop", "Rock", "Ghazal", "Classical", "Hip Hop"])

            st.markdown('<div class="staff-divider"><div class="staff-line"></div><span class="staff-note">𝄞</span><div class="staff-line"></div></div>', unsafe_allow_html=True)
            render_clicked = st.button("🚀  Render Song", use_container_width=True)
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
                            st.session_state.song_url = poll_result["audio_url"]
                            st.session_state.is_generating_music = False
                            st.success("Masterpiece Rendered!")
                        else:
                            st.error(f"Failed to generate: {poll_result.get('message')}")
                            st.session_state.is_generating_music = False
                    else:
                        st.error(f"Failed to submit task: {task_result.get('message')}")
                        st.session_state.is_generating_music = False

            if st.session_state.song_url:
                st.markdown("### 💿 Your Track")
                st.audio(st.session_state.song_url, format="audio/mp3")
                st.balloons()
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