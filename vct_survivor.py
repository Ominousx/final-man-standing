import os
import hashlib
import random
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

# ---- Icons + header/sidebar CSS ----
def inject_icons_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24..48,400,0,0');
    .ms {
      font-family: 'Material Symbols Outlined';
      font-weight: normal; font-style: normal;
      font-size: 18px; display:inline-block; line-height: 0;
      vertical-align: -4px; letter-spacing: normal; text-transform: none;
      white-space: nowrap; direction: ltr; -webkit-font-feature-settings: 'liga';
      -webkit-font-smoothing: antialiased;
    }
    .ms-xl { font-size: 28px; vertical-align: -6px; }
    .ms-muted { color: var(--muted, #9CA3AF); }
    .ms-accent { color: var(--accent, #7C3AED); }

    .main-header {
      display:flex; align-items:center; justify-content:space-between;
      padding: 10px 14px; border-radius: 14px;
      background: linear-gradient(120deg, rgba(124,58,237,.18), rgba(6,182,212,.14));
      border: 1px solid rgba(255,255,255,.10);
      margin-bottom: 10px;
    }
    .header-title {
      display:flex; align-items:center; gap:10px;
      font-size: 24px; font-weight: 800; letter-spacing: .5px;
    }
    .user-section { display:flex; flex-direction:column; align-items:flex-end; }
    </style>
    """, unsafe_allow_html=True)

def ms(name: str, size: int = 18, cls: str = "") -> str:
    style = f"font-size:{size}px" if size != 18 else ""
    klass = "ms" + (f" {cls}" if cls else "")
    return f'<span class="{klass}" style="{style}">{name}</span>'

# ============================== Team Logos ==============================
# Using base64 encoded placeholder logos for demo
# In production, store actual logo files locally
def get_team_logo_placeholder(team_name):
    """Generate a styled placeholder for team logos"""
    colors = {
        "GEN": "#FF6B00", "GEN.G": "#FF6B00",
        "FPX": "#E84855", "FNC": "#FF6900",
        "TL": "#0C223F", "DRX": "#5B9BD5",
        "PRX": "#FFEC00", "T1": "#E2012D",
        "EDG": "#000000", "LOUD": "#00FF88",
        "NRG": "#FFF200", "SEN": "#C9003C",
        "100T": "#E70230", "LEV": "#8B00FF",
        "NAVI": "#FFF200", "VIT": "#FFED00",
        "TH": "#FF1744", "KC": "#00D4FF"
    }

    color = colors.get(team_name.upper(), "#7C3AED")
    # Return a colored square as placeholder
    return f"""
    <div style="
        width: 80px;
        height: 80px;
        background: {color};
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        font-weight: bold;
        color: white;
        margin: 0 auto 10px auto;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    ">
        {team_name[:3].upper()}
    </div>
    """

# ============================== Config ==============================
st.set_page_config(page_title="VCT Random-Fixture Survivor", page_icon="🎯", layout="wide")

ADMIN_KEY_ENV = "VLMS_ADMIN_KEY"   # optional: set to enable Admin in-app
LOCK_MINUTES_BEFORE = 5            # picks lock X minutes before match start
UI_TZ_LABEL = "Asia/Kolkata"       # display-only label

# Writable data dir (works locally & on read-only hosts)
def get_writable_data_dir():
    override = os.getenv("FMS_DATA_DIR")
    if override:
        p = Path(override); p.mkdir(parents=True, exist_ok=True); return p
    p = Path("data")
    try:
        p.mkdir(parents=True, exist_ok=True)
        (p/".write_test").write_text("ok"); (p/".write_test").unlink()
        return p
    except Exception:
        pass
    p = Path("/tmp/fms_data"); p.mkdir(parents=True, exist_ok=True); return p

DATA_DIR = get_writable_data_dir()
SCHEDULE_CSV = DATA_DIR / "schedule.csv"       # stage_id,stage_name,match_id,team_a,team_b,match_time_iso,winner_team
PICKS_CSV    = DATA_DIR / "picks.csv"          # user,stage_id,match_id,pick_team,pick_time_iso
ASSIGN_CSV   = DATA_DIR / "assignments.csv"    # user,stage_id,match_id,assigned_time_iso

# ============================== Google Auth ==============================
def init_session_state():
    """Initialize session state for auth and navigation"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Home"
    if 'show_google_signin' not in st.session_state:
        st.session_state.show_google_signin = False

def show_initial_login():
    """Display initial login page with Continue with Google"""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

    .stApp {
        background: #ffffff;
    }

    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .login-container {
        max-width: 400px;
        margin: 100px auto;
        padding: 40px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    }

    .app-logo {
        text-align: center;
        margin-bottom: 32px;
    }

    .app-title {
        font-size: 24px;
        font-weight: 600;
        color: #202124;
        margin-bottom: 8px;
    }

    .app-subtitle {
        font-size: 14px;
        color: #5f6368;
    }

    .form-title {
        font-size: 20px;
        font-weight: 500;
        color: #202124;
        text-align: center;
        margin-bottom: 8px;
    }

    .form-subtitle {
        font-size: 14px;
        color: #5f6368;
        text-align: center;
        margin-bottom: 24px;
    }

    .divider {
        text-align: center;
        margin: 24px 0;
        color: #5f6368;
        font-size: 14px;
    }

    .terms-text {
        text-align: center;
        font-size: 12px;
        color: #5f6368;
        margin-top: 24px;
        line-height: 18px;
    }

    .terms-text a {
        color: #1a73e8;
        text-decoration: none;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        # App branding
        st.markdown("""
        <div class="app-logo">
            <div class="app-title">VCT SURVIVOR</div>
            <div class="app-subtitle">Official Tournament Prediction Platform</div>
        </div>
        """, unsafe_allow_html=True)

        # Form title and subtitle
        st.markdown("""
        <div class="form-title">Create an account</div>
        <div class="form-subtitle">Enter your email to sign up for this app</div>
        """, unsafe_allow_html=True)

        # Email input
        email = st.text_input("Email", placeholder="email@domain.com", key="initial_email", label_visibility="collapsed")

        # Continue button
        if st.button("Continue", use_container_width=True, type="primary"):
            if email and '@' in email:
                st.session_state.temp_email = email
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.session_state.user_name = email.split('@')[0]
                st.success("✓ Account created successfully")
                st.balloons()
                st.rerun()
            else:
                st.error("Please enter a valid email address")

        # Divider
        st.markdown('<div class="divider">or</div>', unsafe_allow_html=True)

        # Google Sign In button
        google_col = st.columns([1])[0]
        with google_col:
            # Display Google logo and text as HTML
            st.markdown("""
            <div style="background: white; border: 1px solid #dadce0; border-radius: 4px; padding: 10px; margin-bottom: 8px; cursor: pointer; transition: all 0.2s;">
                <div style="display: flex; align-items: center; justify-content: center; gap: 8px;">
                    <svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg">
                        <path d="M17.64 9.20c0-.63-.06-1.25-.16-1.84H9v3.49h4.84c-.21 1.13-.86 2.08-1.83 2.72v2.26h2.96c1.73-1.59 2.73-3.94 2.73-6.73z" fill="#4285F4"/>
                        <path d="M9 18c2.47 0 4.54-.82 6.05-2.21l-2.96-2.26c-.82.55-1.86.87-3.09.87-2.38 0-4.39-1.61-5.11-3.77H.86v2.34C2.35 15.96 5.46 18 9 18z" fill="#34A853"/>
                        <path d="M3.89 10.63c-.18-.55-.29-1.14-.29-1.73s.10-1.18.29-1.73V4.83H.86C.31 5.93 0 7.14 0 8.50s.31 2.57.86 3.67l3.03-2.34z" fill="#FBBC04"/>
                        <path d="M9 3.58c1.34 0 2.54.46 3.48 1.36l2.61-2.61C13.54.82 11.47 0 9 0 5.46 0 2.35 2.04.86 4.83l3.03 2.34c.72-2.16 2.73-3.77 5.11-3.77z" fill="#EA4335"/>
                    </svg>
                    <span style="color: #3c4043; font-weight: 500; font-size: 14px;">Continue with Google</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Invisible button overlay - fixed the parameter issue
            if st.button("", key="google_btn", use_container_width=True):
                st.session_state.show_google_signin = True
                st.rerun()

        # Apple Sign In button
        apple_col = st.columns([1])[0]
        with apple_col:
            # Display Apple logo and text as HTML
            st.markdown("""
            <div style="background: black; border-radius: 4px; padding: 10px; margin-bottom: 8px; cursor: pointer; transition: all 0.2s;">
                <div style="display: flex; align-items: center; justify-content: center; gap: 8px;">
                    <svg width="18" height="18" viewBox="0 0 814 1000" xmlns="http://www.w3.org/2000/svg">
                        <path d="M788.1 340.9c-5.8 4.5-108.2 62.2-108.2 190.5 0 148.4 130.3 200.9 134.2 202.2-.6 3.2-20.7 71.9-68.7 141.9-42.8 61.6-87.5 123.1-155.5 123.1s-85.5-39.5-164-39.5c-76.5 0-103.7 40.8-165.9 40.8s-105.6-57-155.5-127C46.7 790.7 0 663 0 541.8c0-194.4 126.4-297.5 250.8-297.5 66.1 0 121.2 43.4 162.7 43.4 39.5 0 101.1-46 176.3-46 28.5 0 130.9 2.6 198.3 99.2zm-234-181.5c31.1-36.9 53.1-88.1 53.1-139.3 0-7.1-.6-14.3-1.9-20.1-50.6 1.9-110.8 33.7-147.1 75.8-28.5 32.4-55.1 83.6-55.1 135.5 0 7.8 1.3 15.6 1.9 18.1 3.2.6 8.4 1.3 13.6 1.3 45.4 0 102.5-30.4 135.5-71.3z" fill="white"/>
                    </svg>
                    <span style="color: white; font-weight: 500; font-size: 14px;">Continue with Apple</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Invisible button overlay - fixed the parameter issue
            if st.button("", key="apple_btn", use_container_width=True):
                st.info("Apple Sign In coming soon")

        # Terms
        st.markdown("""
        <div class="terms-text">
            By clicking continue, you agree to our<br>
            <a href="#">Terms of Service</a> and <a href="#">Privacy Policy</a>
        </div>
        """, unsafe_allow_html=True)

def show_google_signin():
    """Display Google sign-in page"""
    st.markdown("""
    <style>
    .google-signin-container {
        max-width: 450px;
        margin: 80px auto;
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        padding: 48px 40px 36px;
    }

    .google-logo-container {
        text-align: center;
        margin-bottom: 24px;
    }

    .signin-title {
        text-align: center;
        font-size: 24px;
        font-weight: 400;
        color: #202124;
        margin-bottom: 8px;
    }

    .signin-subtitle {
        text-align: center;
        font-size: 16px;
        color: #5f6368;
        margin-bottom: 32px;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        # Google logo
        st.image("https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png", width=150)

        st.markdown("""
        <div class="signin-title">Sign in</div>
        <div class="signin-subtitle">Continue to VCT Survivor</div>
        """, unsafe_allow_html=True)

        # Email input
        email = st.text_input("Email or phone", placeholder="Enter your email", key="google_email", label_visibility="collapsed")

        # Forgot email link
        st.markdown("""
        <div style='margin-top: 8px; margin-bottom: 24px;'>
            <a href='#' style='color: #1a73e8; font-size: 14px; text-decoration: none;'>Forgot email?</a>
        </div>
        """, unsafe_allow_html=True)

        # Privacy notice
        st.markdown("""
        <div style='color: #5f6368; font-size: 14px; line-height: 20px; margin-bottom: 32px;'>
            Not your computer? Use Guest mode to sign in privately.
            <a href='#' style='color: #1a73e8; text-decoration: none;'>Learn more</a>
        </div>
        """, unsafe_allow_html=True)

        # Buttons
        col_left, col_right = st.columns([1, 1])
        with col_left:
            st.markdown("""
            <div style='text-align: center; padding-top: 10px;'>
                <a href='#' style='color: #1a73e8; text-decoration: none; font-size: 14px;'>Create account</a>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Back", key="back_btn"):
                st.session_state.show_google_signin = False
                st.rerun()
        with col_right:
            if st.button("Next", use_container_width=True, type="primary"):
                if email and '@' in email:
                    st.session_state.authenticated = True
                    st.session_state.user_email = email
                    st.session_state.user_name = email.split('@')[0]
                    st.session_state.show_google_signin = False
                    st.success("✓ Signed in successfully")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Please enter a valid email address")

# ============================== Premium styling ==============================
def inject_premium_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Bebas+Neue&display=swap');

    :root {
        --bg: #0B0F19;
        --panel: #101826;
        --muted: #9CA3AF;
        --text: #E5E7EB;
        --accent: #7C3AED;
        --accent2: #06B6D4;
        --ok: #22c55e;
        --warn: #f59e0b;
        --bad: #ef4444;
    }

    .stApp {
        background: linear-gradient(135deg, #0B0F19 0%, #1a1f2e 100%);
        color: var(--text);
    }

    /* Navigation Sidebar */
    .nav-sidebar {
        background: rgba(16, 24, 38, 0.95);
        border-right: 1px solid rgba(124,58,237,0.2);
        padding: 20px;
        height: 100vh;
    }

    .nav-item {
        padding: 12px 16px;
        margin: 8px 0;
        border-radius: 10px;
        color: #9CA3AF;
        cursor: pointer;
        transition: all 0.2s;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .nav-item:hover {
        background: rgba(124,58,237,0.1);
        color: #E5E7EB;
        transform: translateX(4px);
    }

    .nav-item.active {
        background: linear-gradient(90deg, rgba(124,58,237,0.2), rgba(6,182,212,0.1));
        color: white;
        border-left: 3px solid var(--accent);
    }

    /* Header */
    .main-header {
        background: rgba(16, 24, 38, 0.8);
        backdrop-filter: blur(10px);
        border-bottom: 1px solid rgba(124,58,237,0.2);
        padding: 16px 32px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        position: sticky;
        top: 0;
        z-index: 100;
    }

    .header-title {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 32px;
        letter-spacing: 2px;
        background: linear-gradient(90deg, var(--accent), var(--accent2));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .user-section {
        display: flex;
        align-items: center;
        gap: 16px;
        background: rgba(124,58,237,0.1);
        border: 1px solid rgba(124,58,237,0.3);
        border-radius: 12px;
        padding: 8px 16px;
    }

    /* Cards */
    .game-card {
        background: rgba(16, 24, 38, 0.6);
        border: 1px solid rgba(124,58,237,0.2);
        border-radius: 16px;
        padding: 24px;
        backdrop-filter: blur(10px);
    }

    /* Leaderboard Styling */
    .leaderboard-container {
        background: linear-gradient(135deg, rgba(124,58,237,0.05), rgba(6,182,212,0.03));
        border: 1px solid rgba(124,58,237,0.2);
        border-radius: 16px;
        padding: 4px;
    }

    .leaderboard-row {
        display: flex;
        align-items: center;
        padding: 10px 16px;
        margin: 4px 0;
        background: rgba(16,24,38,0.4);
        border-radius: 12px;
        transition: all 0.2s ease;
        border: 1px solid transparent;
    }

    .leaderboard-row:hover {
        transform: translateX(4px);
        background: rgba(124,58,237,0.1);
        border: 1px solid rgba(124,58,237,0.3);
    }

    .rank-badge {
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        font-weight: 800;
        margin-right: 12px;
    }

    .rank-1 { background: linear-gradient(135deg, #FFD700, #FFA500); color: white; }
    .rank-2 { background: linear-gradient(135deg, #C0C0C0, #808080); color: white; }
    .rank-3 { background: linear-gradient(135deg, #CD7F32, #8B4513); color: white; }
    .rank-other { background: rgba(124,58,237,0.2); color: #A78BFA; }

    .status-alive {
        background: linear-gradient(90deg, #22c55e, #16a34a);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
    }

    .status-dead {
        background: linear-gradient(90deg, #ef4444, #dc2626);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
    }

    /* Stats Cards */
    .stat-card {
        background: linear-gradient(135deg, rgba(124,58,237,0.1), rgba(6,182,212,0.05));
        border: 1px solid rgba(124,58,237,0.2);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }

    .stat-value {
        font-size: 28px;
        font-weight: 800;
        color: var(--accent);
    }

    .stat-label {
        font-size: 12px;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Badges */
    .badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }

    .alive { background: rgba(34,197,94,.12); color: #86efac; }
    .dead { background: rgba(239,68,68,.12); color: #fca5a5; }

    /* Hide Streamlit defaults */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Buttons */
    div.stButton > button {
        background: linear-gradient(90deg, var(--accent), var(--accent2));
        color: white;
        border: 0;
        padding: 10px 24px;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s;
    }

    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(124,58,237,0.4);
    }
    </style>
    """, unsafe_allow_html=True)

def badge(text, cls):
    return f'<span class="badge {cls}">{text}</span>'

# ============================== Data utils ==============================
def ensure_files():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SCHEDULE_CSV.exists():
        pd.DataFrame(columns=[
            "stage_id","stage_name","match_id","team_a","team_b","match_time_iso","winner_team"
        ]).to_csv(SCHEDULE_CSV, index=False)
    if not PICKS_CSV.exists():
        pd.DataFrame(columns=["user","stage_id","match_id","pick_team","pick_time_iso"]).to_csv(PICKS_CSV, index=False)
    if not ASSIGN_CSV.exists():
        pd.DataFrame(columns=["user","stage_id","match_id","assigned_time_iso"]).to_csv(ASSIGN_CSV, index=False)

def load_schedule():
    df = pd.read_csv(SCHEDULE_CSV, dtype=str).fillna("")
    if df.empty:
        df["stage_id"] = pd.Series(dtype="Int64")
    else:
        df["stage_id"] = pd.to_numeric(df["stage_id"], errors="coerce").astype("Int64")
    return df.sort_values(["stage_id", "match_time_iso"])

def load_picks():
    if not PICKS_CSV.exists():
        return pd.DataFrame(columns=["user","stage_id","match_id","pick_team","pick_time_iso"])
    df = pd.read_csv(PICKS_CSV, dtype=str).fillna("")
    if df.empty:
        df["stage_id"] = pd.Series(dtype="Int64")
    else:
        df["stage_id"] = pd.to_numeric(df["stage_id"], errors="coerce").astype("Int64")
    return df

def load_assignments():
    if not ASSIGN_CSV.exists():
        return pd.DataFrame(columns=["user","stage_id","match_id","assigned_time_iso"])
    df = pd.read_csv(ASSIGN_CSV, dtype=str).fillna("")
    if df.empty:
        df["stage_id"] = pd.Series(dtype="Int64")
    else:
        df["stage_id"] = pd.to_numeric(df["stage_id"], errors="coerce").astype("Int64")
    return df

def save_picks(df): df.to_csv(PICKS_CSV, index=False)
def save_assign(df): df.to_csv(ASSIGN_CSV, index=False)

def now_utc():
    return datetime.now(timezone.utc)

# ============================== Game logic ==============================
def deterministic_choice(options, user: str, stage_id: int, salt: str = ""):
    """Reproducible choice so refresh spam can't farm matchups."""
    if not len(options):
        return None
    seed_src = f"{user}|{stage_id}|{salt}"
    seed = int(hashlib.sha256(seed_src.encode()).hexdigest(), 16) % (10**8)
    rng = random.Random(seed)
    return rng.choice(list(options))

def eligible_matches(schedule_df: pd.DataFrame, stage_id: int):
    df = schedule_df[(schedule_df["stage_id"] == stage_id)].copy()
    df["match_dt"] = pd.to_datetime(df["match_time_iso"], utc=True, errors="coerce")
    return df[(df["winner_team"] == "") & (df["match_dt"] > now_utc())]

def active_stage(schedule_df: pd.DataFrame):
    """Earliest stage with any match not started & undecided."""
    if schedule_df.empty:
        return None
    df = schedule_df.copy()
    df["match_dt"] = pd.to_datetime(df["match_time_iso"], utc=True, errors="coerce")
    elig = df[(df["winner_team"] == "") & (df["match_dt"] > now_utc())]
    if elig.empty:
        return None
    row = elig.sort_values(["stage_id","match_dt"]).iloc[0]
    sid = int(row["stage_id"])
    name = schedule_df[schedule_df["stage_id"]==sid]["stage_name"].dropna().astype(str).iloc[0]
    return {"stage_id": sid, "stage_name": name}

def lock_deadline(schedule_df, match_id, minutes_before=LOCK_MINUTES_BEFORE):
    row = schedule_df[schedule_df["match_id"]==match_id].iloc[0]
    mdt = pd.to_datetime(row["match_time_iso"], utc=True, errors="coerce")
    return mdt - pd.Timedelta(minutes=minutes_before)

def can_pick(schedule_df, match_id):
    return now_utc() < lock_deadline(schedule_df, match_id)

def judge_results(schedule_df: pd.DataFrame, picks_df: pd.DataFrame):
    if picks_df.empty:
        return pd.DataFrame(columns=["user","stage_id","match_id","pick_team","result"])
    merged = picks_df.merge(
        schedule_df[["match_id","winner_team"]], on="match_id", how="left"
    )
    def r(row):
        w = row.get("winner_team","")
        if w == "": return "Waiting"
        return "Win" if row["pick_team"] == w else "Loss"
    merged["result"] = merged.apply(r, axis=1)
    return merged[["user","stage_id","match_id","pick_team","result"]]

def compute_leaderboard(results_df: pd.DataFrame):
    if results_df.empty:
        return pd.DataFrame(columns=["user","alive","wins","first_loss_stage"])
    losses = results_df[results_df["result"]=="Loss"].sort_values(["user","stage_id"])
    first_loss = losses.groupby("user")["stage_id"].min().rename("first_loss_stage")
    wins = (results_df[results_df["result"]=="Win"].groupby("user")["stage_id"].count().rename("wins"))
    lb = pd.DataFrame(index=results_df["user"].unique()).join([wins, first_loss])
    lb["wins"] = lb["wins"].fillna(0).astype(int)
    lb["alive"] = lb["first_loss_stage"].isna()
    return lb.reset_index().rename(columns={"index":"user"}).sort_values(by=["alive","wins"], ascending=[False,False])

def get_or_make_assignment(user, stage_id, assignments_df, schedule_df):
    """Assign one random eligible match to the user for this stage (no rerolls)."""
    cur = assignments_df[(assignments_df["user"]==user) & (assignments_df["stage_id"]==stage_id)]
    pool = eligible_matches(schedule_df, stage_id)
    if pool.empty:
        return None, assignments_df

    if not cur.empty:
        mid = cur.iloc[0]["match_id"]
        still_ok = pool[pool["match_id"]==mid]
        if not still_ok.empty:
            return mid, assignments_df
        new_mid = deterministic_choice(pool["match_id"], user, stage_id, salt="fallback")
        assignments_df.loc[cur.index, ["match_id","assigned_time_iso"]] = [new_mid, now_utc().isoformat()]
        return new_mid, assignments_df

    mid = deterministic_choice(pool["match_id"], user, stage_id)
    new_row = {
        "user": user,
        "stage_id": int(stage_id),
        "match_id": mid,
        "assigned_time_iso": now_utc().isoformat()
    }
    assignments_df = pd.concat([assignments_df, pd.DataFrame([new_row])], ignore_index=True)
    return mid, assignments_df

def record_pick(picks_df, user, stage_id, match_id, pick_team):
    dup = picks_df[(picks_df["user"]==user) & (picks_df["stage_id"]==stage_id)]
    if not dup.empty:
        return picks_df, False, "You already picked for this stage."
    new_row = {
        "user": user,
        "stage_id": int(stage_id),
        "match_id": match_id,
        "pick_team": pick_team,
        "pick_time_iso": now_utc().isoformat()
    }
    picks_df = pd.concat([picks_df, pd.DataFrame([new_row])], ignore_index=True)
    return picks_df, True, f"Locked {pick_team}"

def countdown_to(dt_iso: str):
    try:
        dt = pd.to_datetime(dt_iso, utc=True, errors="coerce")
        if pd.isna(dt): return "—"
        secs = int((dt - now_utc()).total_seconds())
        if secs <= 0: return "Starting"
        m, s = divmod(secs, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        parts = []
        if d: parts.append(f"{d}d")
        if h or d: parts.append(f"{h}h")
        parts.append(f"{m}m")
        return " ".join(parts)
    except Exception:
        return "—"

# ============================== Page Components ==============================
def render_header():
    """Render the main header with user info (icons, no emojis)"""
    name = st.session_state.get("user_name") or "Guest"
    email = st.session_state.get("user_email") or ""

    st.markdown(f"""
    <div class="main-header">
        <div class="header-title">
            {ms("sports_esports", 28, "ms-accent")}
            <div>VCT SURVIVOR</div>
        </div>
        <div class="user-section">
            <span style="color: #E5E7EB;">{ms("person",18)} {name}</span>
            <span style="color: #9CA3AF; font-size: 12px;">{email}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar sign-out (icon + button)
    with st.sidebar:
        c1, c2 = st.columns([0.15, 0.85])
        c1.markdown(ms("logout", 18, "ms-muted"), unsafe_allow_html=True)
        if c2.button("Sign Out", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_email = None
            st.session_state.user_name = None
            st.session_state.current_page = "Home"
            st.rerun()

def render_sidebar():
    """Render navigation sidebar (icons + buttons)"""
    with st.sidebar:
        st.markdown("## Navigation")
        nav_items = [
            ("home",            "Home"),
            ("leaderboard",     "Leaderboard"),
            ("insights",        "My Stats"),
            ("calendar_month",  "Schedule"),
            ("settings",        "Admin"),
        ]
        for icon_name, label in nav_items:
            c1, c2 = st.columns([0.18, 0.82])
            c1.markdown(ms(icon_name, 18, "ms-muted"), unsafe_allow_html=True)
            if c2.button(label, key=f"nav_{label}", use_container_width=True):
                st.session_state.current_page = label  # keep a clean page key
                st.rerun()

        st.markdown("---")
        st.markdown("### Quick Stats")

        results_df = judge_results(load_schedule(), load_picks())
        user = st.session_state.get("user_name") or ""
        me = results_df[results_df["user"] == user]

        wins = int((me["result"] == "Win").sum()) if not me.empty else 0
        losses = int((me["result"] == "Loss").sum()) if not me.empty else 0

        c1, c2 = st.columns(2)
        with c1:
            st.metric("Wins", wins)
        with c2:
            st.metric("Losses", losses)

def page_home():
    """Home page with current match assignment"""
    schedule_df = load_schedule()
    picks_df = load_picks()
    assign_df = load_assignments()
    results_df = judge_results(schedule_df, picks_df)
    lb_df = compute_leaderboard(results_df)
    user = st.session_state.user_name

    # Check if alive
    is_alive = True
    me = results_df[results_df["user"]==user]
    if not me.empty and any(me["result"]=="Loss"):
        is_alive = False

    # Status badge
    st.markdown(f"""
    <div style='text-align: center; margin: 20px 0;'>
        {badge("ALIVE", "alive") if is_alive else badge("ELIMINATED", "dead")}
    </div>
    """, unsafe_allow_html=True)

    # Main content
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"## {ms('flag',22,'ms-accent')} Current Match Assignment", unsafe_allow_html=True)
        act = active_stage(schedule_df)
        if not act:
            st.info("No active stage. Wait for the next stage to begin.")
        else:
            with st.container():
                st.markdown(f"""
                <div class="game-card">
                    <h3 style='color: #A78BFA;'>{act["stage_name"]}</h3>
                    <p style='color: #9CA3AF;'>Stage {act["stage_id"]}</p>
                </div>
                """, unsafe_allow_html=True)

                mid, assign_df = get_or_make_assignment(user, act["stage_id"], assign_df, schedule_df)
                if mid:
                    mrow = schedule_df[schedule_df["match_id"]==mid].iloc[0]

                    # Match display with team logos
                    st.markdown(f"**Match ID:** `{mid}`")

                    col_team1, col_vs, col_team2 = st.columns([2, 1, 2])

                    with col_team1:
                        st.markdown(get_team_logo_placeholder(mrow['team_a']), unsafe_allow_html=True)
                        st.markdown(f"<h3 style='text-align: center; color: #E5E7EB; margin: 0;'>{mrow['team_a']}</h3>", unsafe_allow_html=True)

                    with col_vs:
                        st.markdown("""
                        <div style="text-align: center; padding-top: 30px;">
                            <h2 style="color: #9CA3AF;">VS</h2>
                        </div>
                        """, unsafe_allow_html=True)

                    with col_team2:
                        st.markdown(get_team_logo_placeholder(mrow['team_b']), unsafe_allow_html=True)
                        st.markdown(f"<h3 style='text-align: center; color: #E5E7EB; margin: 0;'>{mrow['team_b']}</h3>", unsafe_allow_html=True)

                    # Match timing info
                    col_time1, col_time2 = st.columns(2)
                    with col_time1:
                        st.markdown(f"⏱️ **Starts in:** {countdown_to(mrow['match_time_iso'])}")
                    with col_time2:
                        st.markdown(f"🔒 **Locks:** {LOCK_MINUTES_BEFORE}m before")

                    # Pick form
                    existing = picks_df[(picks_df["user"]==user) & (picks_df["stage_id"]==act["stage_id"])]
                    if not existing.empty:
                        st.success(f"✅ You picked: **{existing.iloc[0]['pick_team']}**")
                    elif not can_pick(schedule_df, mid):
                        st.error("Picks are locked for this match")
                    else:
                        with st.form("pick_form"):
                            pick = st.selectbox("Select winner:", [mrow["team_a"], mrow["team_b"]])
                            if st.form_submit_button("Lock Pick ✅", use_container_width=True):
                                picks_df, ok, msg = record_pick(picks_df, user, act["stage_id"], mid, pick)
                                if ok:
                                    save_picks(picks_df)
                                    st.success(msg)
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error(msg)
                save_assign(assign_df)

    with col2:
        st.markdown("## Quick Leaderboard")
        if not lb_df.empty:
            st.markdown('<div class="leaderboard-container">', unsafe_allow_html=True)
            for idx, row in lb_df.head(5).iterrows():
                rank = idx + 1
                rank_class = f"rank-{rank}" if rank <= 3 else "rank-other"
                rank_icon = "👑" if rank == 1 else f"#{rank}"

                st.markdown(f'''
                <div class="leaderboard-row">
                    <div class="rank-badge {rank_class}">{rank_icon}</div>
                    <div style="flex: 1; font-weight: 600;">{row['user']}</div>
                    <div style="color: #A78BFA; margin-right: 12px;">{row['wins']}W</div>
                    <div class="{'status-alive' if row['alive'] else 'status-dead'}">
                        {'ALIVE' if row['alive'] else 'DEAD'}
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

def page_leaderboard():
    """Full leaderboard page"""
    results_df = judge_results(load_schedule(), load_picks())
    lb_df = compute_leaderboard(results_df)

    st.markdown("# 🏆 Global Leaderboard")

    if lb_df.empty:
        st.info("No players have made picks yet")
    else:
        # Stats summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{len(lb_df)}</div>
                <div class="stat-label">Total Players</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{lb_df['alive'].sum()}</div>
                <div class="stat-label">Still Alive</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{(~lb_df['alive']).sum()}</div>
                <div class="stat-label">Eliminated</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{lb_df['wins'].max() if not lb_df.empty else 0}</div>
                <div class="stat-label">Max Wins</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Full leaderboard
        st.markdown('<div class="leaderboard-container" style="margin-top: 20px;">', unsafe_allow_html=True)
        for idx, row in lb_df.iterrows():
            rank = idx + 1
            rank_class = f"rank-{rank}" if rank <= 3 else "rank-other"
            rank_icon = "👑" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"

            stage_info = f" (Stage {int(row['first_loss_stage'])})" if not row['alive'] and pd.notna(row.get('first_loss_stage')) else ""

            st.markdown(f'''
            <div class="leaderboard-row">
                <div class="rank-badge {rank_class}">{rank_icon}</div>
                <div style="flex: 1; font-weight: 600; color: #E5E7EB;">{row['user']}{stage_info}</div>
                <div style="background: rgba(124,58,237,0.2); padding: 4px 12px; border-radius: 20px; margin-right: 12px; color: #A78BFA;">{row['wins']} WINS</div>
                <div class="{'status-alive' if row['alive'] else 'status-dead'}">
                    {'ALIVE' if row['alive'] else 'DEAD'}
                </div>
            </div>
            ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

def page_my_stats():
    """Personal statistics page"""
    user = st.session_state.user_name
    picks_df = load_picks()
    results_df = judge_results(load_schedule(), picks_df)
    my_results = results_df[results_df["user"]==user]

    st.markdown("# 📊 My Statistics")

    # Stats cards
    col1, col2, col3, col4 = st.columns(4)

    wins = int((my_results["result"]=="Win").sum()) if not my_results.empty else 0
    losses = int((my_results["result"]=="Loss").sum()) if not my_results.empty else 0
    waiting = int((my_results["result"]=="Waiting").sum()) if not my_results.empty else 0
    total = len(my_results)

    with col1:
        st.metric("Total Picks", total)
    with col2:
        st.metric("Wins", wins, f"{wins/total*100:.0f}%" if total > 0 else "—")
    with col3:
        st.metric("Losses", losses)
    with col4:
        st.metric("Pending", waiting)

    st.markdown("---")

    # Pick history
    st.markdown("## Pick History")
    my_picks = picks_df[picks_df["user"]==user]
    if my_picks.empty:
        st.info("You haven't made any picks yet")
    else:
        st.dataframe(my_picks.sort_values("stage_id", ascending=False), use_container_width=True, hide_index=True)

def page_schedule():
    """Schedule page"""
    schedule_df = load_schedule()

    st.markdown("# 🗓️ Match Schedule")

    if schedule_df.empty:
        st.info("No matches scheduled yet")
    else:
        st.dataframe(schedule_df, use_container_width=True, hide_index=True)

def page_admin():
    """Admin page"""
    st.markdown("# ⚙️ Admin Panel")

    entered = st.text_input("Admin key:", type="password")
    if entered and os.environ.get(ADMIN_KEY_ENV) and entered == os.environ[ADMIN_KEY_ENV]:
        st.success("Admin access granted")

        schedule_df = load_schedule()
        st.download_button("📥 Download schedule.csv", schedule_df.to_csv(index=False), "schedule.csv")

        up = st.file_uploader("📤 Upload new schedule.csv", type=["csv"])
        if up:
            new_sched = pd.read_csv(up, dtype=str).fillna("")
            new_sched.to_csv(SCHEDULE_CSV, index=False)
            st.success("Schedule updated!")
            st.rerun()
    else:
        st.info("Enter admin key to access admin features")

# ============================== Main App ==============================
def main_app():
    inject_premium_css()
    ensure_files()

    render_header()
    render_sidebar()

    # Route to appropriate page
    page = st.session_state.current_page

    if page == "Home":
        page_home()
    elif page == "Leaderboard":
        page_leaderboard()
    elif page == "My Stats" or page == "Stats":
        page_my_stats()
    elif page == "Schedule":
        page_schedule()
    elif page == "Admin":
        page_admin()
    else:
        page_home()

# ============================== Main Entry Point ==============================
if __name__ == "__main__":
    init_session_state()

    if not st.session_state.authenticated:
        if st.session_state.show_google_signin:
            show_google_signin()
        else:
            show_initial_login()
    else:
        main_app()
