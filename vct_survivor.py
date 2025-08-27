import os
import hashlib
import random
import re
import base64
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st
from zoneinfo import ZoneInfo

# ============================== Page Config ==============================
st.set_page_config(page_title="VCT Random-Fixture Survivor", page_icon="🎯", layout="wide")

# ============================== Constants ==============================
ADMIN_KEY_ENV = "VLMS_ADMIN_KEY"
LOCK_MINUTES_BEFORE = 5
LOCAL_TZ = ZoneInfo("Asia/Kolkata")

REQ_SCHEDULE_COLS = {"stage_id","stage_name","match_id","team_a","team_b","match_time_iso","winner_team"}
REQ_PICKS_COLS    = {"user","stage_id","match_id","pick_team","pick_time_iso"}
REQ_ASSIGN_COLS   = {"user","stage_id","match_id","assigned_time_iso"}

# ============================== Data Directory ==============================
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
SCHEDULE_CSV = DATA_DIR / "schedule.csv"
PICKS_CSV    = DATA_DIR / "picks.csv"
ASSIGN_CSV   = DATA_DIR / "assignments.csv"

# ============================== Riot ID Validation ==============================
def validate_riot_id_format(riot_id):
    if not riot_id or '#' not in riot_id:
        return False
    
    try:
        game_name, tag_line = riot_id.split('#')
        if not (3 <= len(game_name) <= 16):
            return False
        if not re.match(r'^[a-zA-Z0-9\s]+$', game_name):
            return False
        if not (3 <= len(tag_line) <= 5):
            return False
        if not re.match(r'^[a-zA-Z0-9]+$', tag_line):
            return False
        return True
    except:
        return False

# ============================== Styling ==============================
def inject_premium_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800;900&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24..48,400,0,0');
    
    :root {
        --bg: #0a0a0a;
        --panel: #1a1a1a;
        --panel-dark: #0f0f0f;
        --text: #ffffff;
        --text-muted: #cccccc;
        --accent: #c8bf9b;
        --accent-glow: #d4ccb0;
        --border: #333333;
        --hover: #2a2a2a;
        --shadow: 0 8px 32px rgba(0, 0, 0, 0.8);
        --shadow-glow: 0 0 20px rgba(200, 191, 155, 0.3);
        --gradient: linear-gradient(135deg, #c8bf9b 0%, #d4ccb0 100%);
    }
    
    .stApp {
        background: var(--bg);
        color: var(--text);
        font-family: 'Poppins', sans-serif;
    }
    
    .ms { 
        font-family: 'Material Symbols Outlined'; 
        font-weight: normal; 
        font-style: normal;
        font-size: 18px; 
        display:inline-block; 
        line-height: 0; 
        vertical-align: -4px;
    }
    
    .main-header {
        background: linear-gradient(135deg, var(--panel) 0%, var(--panel-dark) 100%);
        border-bottom: 2px solid var(--accent);
        box-shadow: var(--shadow);
        padding: 15px 20px;
        margin: 0 10px 20px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .header-title {
        font-family: 'Poppins', sans-serif;
        font-size: 2.2rem;
        font-weight: 800;
        color: var(--text);
        text-shadow: 0 0 20px rgba(200, 191, 155, 0.5);
        display: flex;
        align-items: center;
        gap: 15px;
        flex: 1;
    }
    
    .user-section {
        background: rgba(200, 191, 155, 0.1);
        border: 1px solid var(--accent);
        border-radius: 20px;
        padding: 8px 16px;
        font-weight: 600;
        backdrop-filter: blur(10px);
        box-shadow: var(--shadow-glow);
        white-space: nowrap;
        max-width: 200px;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .game-card {
        background: linear-gradient(145deg, var(--panel) 0%, var(--panel-dark) 100%);
        border: 2px solid var(--border);
        border-radius: 20px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: var(--shadow);
    }
    
    .team-logo-container {
        text-align: center;
        margin: 10px 0;
    }
    
    .leaderboard-container {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 16px;
        margin: 5px 0;
        box-shadow: var(--shadow);
        min-height: 400px;
        overflow-y: auto;
    }
    
    .leaderboard-row {
        background: var(--panel-dark);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 12px 15px;
        margin: 8px 0;
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: all 0.3s ease;
        min-height: 45px;
    }
    
    .rank-badge {
        background: var(--gradient);
        color: var(--bg);
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 10px;
        font-family: 'Poppins', sans-serif;
        font-size: 11px;
        min-width: 20px;
        text-align: center;
    }
    
    .status-alive {
        color: #00ff88;
        font-weight: 600;
        font-size: 10px;
    }
    
    .status-dead {
        color: #ff4444;
        font-weight: 600;
        font-size: 10px;
    }
    
    .badge {
        padding: 5px 12px;
        border-radius: 15px;
        font-weight: 600;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .badge.alive {
        background: linear-gradient(135deg, #00ff88, #00cc66);
        color: var(--bg);
    }
    
    .badge.dead {
        background: linear-gradient(135deg, #ff4444, #cc3333);
        color: var(--bg);
    }
    
    .stButton > button {
        background: var(--gradient);
        color: var(--bg);
        border: none;
        border-radius: 25px;
        padding: 12px 30px;
        font-weight: 700;
        font-size: 16px;
        font-family: 'Poppins', sans-serif;
        box-shadow: var(--shadow-glow);
        transition: all 0.3s ease;
        width: 100%;
        min-height: 50px;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(200, 191, 155, 0.4);
    }
    
    /* Login Page Specific Styles */
    .login-container {
        background: var(--panel);
        border: 2px solid var(--border);
        border-radius: 20px;
        padding: 40px;
        margin: 20px 0;
        box-shadow: var(--shadow);
        max-width: 500px;
        margin: 20px auto;
    }
    
    .google-signin-btn {
        background: #ffffff;
        color: #000000;
        border: none;
        border-radius: 25px;
        padding: 15px 30px;
        font-weight: 600;
        font-size: 16px;
        font-family: 'Poppins', sans-serif;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
        width: 100%;
        min-height: 55px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        margin-bottom: 20px;
        cursor: pointer;
    }
    
    .google-signin-btn:hover {
        background: #f8f9fa;
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.4);
    }
    
    .divider {
        display: flex;
        align-items: center;
        margin: 25px 0;
        text-align: center;
        color: var(--text-muted);
    }
    
    .divider::before,
    .divider::after {
        content: '';
        flex: 1;
        height: 1px;
        background: var(--border);
    }
    
    .divider span {
        padding: 0 15px;
        font-size: 14px;
    }
    
    .continue-btn {
        background: var(--gradient) !important;
        color: var(--bg) !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 15px 30px !important;
        font-weight: 700 !important;
        font-size: 18px !important;
        font-family: 'Poppins', sans-serif !important;
        box-shadow: var(--shadow-glow) !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        min-height: 55px !important;
        margin-top: 10px !important;
    }
    
    .continue-btn:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 25px rgba(200, 191, 155, 0.4) !important;
    }
    
    .continue-btn:disabled {
        background: #666666 !important;
        color: #999999 !important;
        cursor: not-allowed !important;
        transform: none !important;
        box-shadow: none !important;
    }
    
    #MainMenu, footer, header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

def badge(text, cls):
    return f'<span class="badge {cls}">{text}</span>'

def ms(name: str, size: int = 18) -> str:
    return f'<span class="ms" style="font-size:{size}px">{name}</span>'

# ============================== Icons ==============================
ICON_DIR = Path(__file__).parent / "icons"
if not ICON_DIR.exists():
    ICON_DIR = Path.cwd() / "icons"

def _data_uri_for_icon(path_or_name: str) -> Optional[str]:
    p = Path(path_or_name)
    if not p.exists():
        p = ICON_DIR / path_or_name
    if not p.exists():
        return None

    mime, _ = mimetypes.guess_type(p.name)
    if not mime:
        mime = "image/png"

    try:
        data = p.read_bytes()
        b64 = base64.b64encode(data).decode("ascii")
        return f"data:{mime};base64,{b64}"
    except Exception:
        return None

def icon_html(path_or_name: str, size: int = 18) -> str:
    uri = _data_uri_for_icon(path_or_name)
    if not uri:
        return f'<span style="display:inline-block;width:{size}px;height:{size}px;background:rgba(255,255,255,.08);border-radius:4px;"></span>'
    return f'<img src="{uri}" style="width:{size}px;height:{size}px;object-fit:contain;vertical-align:-3px;" />'

# ============================== Team Logos ==============================
def get_team_logo_placeholder(team_name):
    colors = {"PRX": "#d4ccb0", "TALON": "#c8bf9b", "RRQ": "#a89f7e", "BBL": "#b8af8a", "Team Liquid": "#c8bf9b", "GiantX": "#d4ccb0", "NAVI": "#a89f7e", "Sentinels": "#b8af8a", "G2": "#c8bf9b"}
    
    if team_name in ["TBD", "TBA", "—"]:
        display_text = "TBD"
        color = "#6b7280"
    else:
        display_text = (team_name or '')[:3].upper()
        color = colors.get(team_name, "#c8bf9b")
    
    return f"""
    <div style="width:80px;height:80px;background:{color};border-radius:50%;display:flex;
                align-items:center;justify-content:center;font-size:18px;font-weight:700;color:#0a0a0a;
                margin:0 auto;border:3px solid #c8bf9b;">
        <span>{display_text}</span>
    </div>
    """

def team_logo_html(team_name: str):
    t = (team_name or "").strip()
    if not t or any(placeholder in t for placeholder in ["-W", "-L", "TBD", "TBA"]):
        return get_team_logo_placeholder(t or "TBD")
    
    if not os.path.exists("logos"):
        return get_team_logo_placeholder(t)
    
    exact_matches = {
        "BBL": "BBL.png", "Team Liquid": "Team Liquid.png", "Paper Rex": "Paper Rex.png",
        "PRX": "Paper Rex.png", "TALON": "TALON.png", "RRQ": "RRQ.png",
        "GiantX": "GiantX.png", "NAVI": "NAVI.png", "Sentinels": "Sentinels.png",
        "G2": "G2.png", "NRG": "NRG.png", "Cloud9": "Cloud9.png"
    }
    
    logo_path = None
    if t in exact_matches and os.path.exists(f"logos/{exact_matches[t]}"):
        logo_path = f"logos/{exact_matches[t]}"
    
    if logo_path:
        try:
            with open(logo_path, "rb") as img_file:
                img_data = base64.b64encode(img_file.read()).decode()
                return f'<div class="team-logo-container"><img src="data:image/png;base64,{img_data}" style="width:80px;height:80px;border-radius:50%;border:3px solid #c8bf9b;object-fit:cover;" alt="{t}"/></div>'
        except Exception:
            pass
    
    return get_team_logo_placeholder(t)

# ============================== Authentication ==============================
def init_session_state():
    if 'authenticated' not in st.session_state: st.session_state.authenticated = False
    if 'user_email' not in st.session_state: st.session_state.user_email = None
    if 'user_name' not in st.session_state: st.session_state.user_name = None
    if 'riot_id' not in st.session_state: st.session_state.riot_id = None
    if 'current_page' not in st.session_state: st.session_state.current_page = "Home"

def show_initial_login():
    inject_premium_css()
    
    st.markdown("""
    <style>
    .stApp { background:#0a0a0a; }
    .app-title{ 
        font-size: 36px; 
        font-weight: 900; 
        color: #c8bf9b; 
        margin-bottom: 12px; 
        font-family: 'Poppins', sans-serif; 
        text-align: center;
        text-shadow: 0 0 20px rgba(200, 191, 155, 0.5);
    }
    .form-title{ 
        font-size: 22px; 
        font-weight: 600; 
        text-align: center; 
        margin-bottom: 25px; 
        color: #ffffff; 
        font-family: 'Poppins', sans-serif;
    }
    .caution-box{ 
        background: rgba(255, 68, 68, 0.1); 
        border: 2px solid #ff4444; 
        border-radius: 12px; 
        padding: 20px; 
        margin: 25px 0; 
        text-align: center;
    }
    .caution-title{ 
        color: #ff4444; 
        font-weight: 700; 
        font-size: 18px; 
        margin-bottom: 10px;
    }
    .caution-text{ 
        color: #ffaaaa; 
        font-size: 14px; 
        line-height: 1.6;
    }
    /* Override Streamlit button styling for Continue button */
    .stButton > button {
        background: var(--gradient) !important;
        color: var(--bg) !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 15px 30px !important;
        font-weight: 700 !important;
        font-size: 18px !important;
        font-family: 'Poppins', sans-serif !important;
        box-shadow: var(--shadow-glow) !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        min-height: 55px !important;
        margin-top: 15px !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 25px rgba(200, 191, 155, 0.4) !important;
    }
    
    .stButton > button:disabled {
        background: #666666 !important;
        color: #999999 !important;
        cursor: not-allowed !important;
        transform: none !important;
        box-shadow: none !important;
    }
    
    /* Specific styling for enabled continue button */
    .stButton > button:not(:disabled) {
        background: var(--gradient) !important;
        color: var(--bg) !important;
        opacity: 1 !important;
        cursor: pointer !important;
    }
    
    /* Force visibility for continue button */
    div[data-testid="column"] .stButton > button {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<div class="app-title">VCT SURVIVOR</div>', unsafe_allow_html=True)
        st.markdown('<div class="form-title">Join the Competition</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="caution-box">
            <div class="caution-title">⚠️ IMPORTANT</div>
            <div class="caution-text">
                Enter your Riot ID carefully as changes won't be allowed later.<br>
                This will be used to gift the bundle when you win.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        riot_id = st.text_input("Riot ID", placeholder="GameName#TAG", label_visibility="collapsed", key="riot_id_input")
        confirm = st.checkbox("I confirm my Riot ID is correct", key="confirm_riot_id")
        
        # Custom continue button with proper styling
        continue_clicked = st.button("Continue", disabled=not (confirm and riot_id), key="continue_btn", use_container_width=True)
        
        if continue_clicked:
            if riot_id and validate_riot_id_format(riot_id):
                st.session_state.authenticated = True
                st.session_state.user_name = riot_id.split('#')[0]
                st.session_state.riot_id = riot_id
                st.success("Account created successfully!")
                st.rerun()
            else:
                st.error("Invalid Riot ID format. Please use format: GameName#TAG")
        
        # Divider
        st.markdown('<div class="divider"><span>or</span></div>', unsafe_allow_html=True)
        
        # Mock Google Sign-in Button
        st.markdown("""
        <div class="google-signin-btn" onclick="alert('Google Sign-in not implemented in demo')">
            <svg width="20" height="20" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Continue with Google
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

# ============================== Data Functions ==============================
def ensure_files():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SCHEDULE_CSV.exists(): pd.DataFrame(columns=sorted(REQ_SCHEDULE_COLS)).to_csv(SCHEDULE_CSV, index=False)
    if not PICKS_CSV.exists(): pd.DataFrame(columns=sorted(REQ_PICKS_COLS)).to_csv(PICKS_CSV, index=False)
    if not ASSIGN_CSV.exists(): pd.DataFrame(columns=sorted(REQ_ASSIGN_COLS)).to_csv(ASSIGN_CSV, index=False)

def load_schedule():
    try:
        df = pd.read_csv(SCHEDULE_CSV, dtype=str).fillna("")
        df["stage_id"] = pd.to_numeric(df["stage_id"], errors="coerce").fillna(0).astype("Int64")
        return df.sort_values(["stage_id", "match_time_iso"])
    except:
        return pd.DataFrame(columns=sorted(REQ_SCHEDULE_COLS))

def load_picks():
    try:
        df = pd.read_csv(PICKS_CSV, dtype=str).fillna("")
        df["stage_id"] = pd.to_numeric(df["stage_id"], errors="coerce").fillna(0).astype("Int64")
        return df
    except:
        return pd.DataFrame(columns=sorted(REQ_PICKS_COLS))

def load_assignments():
    try:
        df = pd.read_csv(ASSIGN_CSV, dtype=str).fillna("")
        df["stage_id"] = pd.to_numeric(df["stage_id"], errors="coerce").fillna(0).astype("Int64")
        return df
    except:
        return pd.DataFrame(columns=sorted(REQ_ASSIGN_COLS))

def save_picks(df): df.to_csv(PICKS_CSV, index=False)
def save_assign(df): df.to_csv(ASSIGN_CSV, index=False)
def now_utc(): return datetime.now(timezone.utc)

def fmt_local(dt_iso: str, fmt: str = "%b %d, %Y • %I:%M %p"):
    dt = pd.to_datetime(dt_iso, utc=True, errors="coerce")
    if pd.isna(dt): return "—"
    return dt.tz_convert(LOCAL_TZ).strftime(fmt)

def countdown_to(dt_iso: str):
    try:
        dt = pd.to_datetime(dt_iso, utc=True, errors="coerce")
        if pd.isna(dt): return "—"
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
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
    except:
        return "—"

# ============================== Game Logic ==============================
def deterministic_choice(options, user: str, stage_id: int, salt: str = ""):
    if not len(options): return None
    seed_src = f"{user}|{stage_id}|{salt}"
    seed = int(hashlib.sha256(seed_src.encode()).hexdigest(), 16) % (10**8)
    rng = random.Random(seed)
    return rng.choice(list(options))

def eligible_matches(schedule_df: pd.DataFrame, stage_id: int):
    df = schedule_df[(schedule_df["stage_id"] == int(stage_id))].copy()
    df["match_dt"] = pd.to_datetime(df["match_time_iso"], utc=True, errors="coerce")
    return df[(df["winner_team"] == "") & (df["match_dt"] > now_utc())]

def active_stage(schedule_df: pd.DataFrame):
    if schedule_df.empty: return None
    df = schedule_df.copy()
    df["match_dt"] = pd.to_datetime(df["match_time_iso"], utc=True, errors="coerce")
    elig = df[(df["winner_team"] == "") & (df["match_dt"] > now_utc())]
    if elig.empty: return None
    row = elig.sort_values(["stage_id","match_dt"]).iloc[0]
    sid = int(row["stage_id"])
    name_series = schedule_df[schedule_df["stage_id"]==sid]["stage_name"].dropna().astype(str)
    name = name_series.iloc[0] if not name_series.empty else f"Stage {sid}"
    return {"stage_id": sid, "stage_name": name}

def can_pick(schedule_df, match_id):
    row = schedule_df[schedule_df["match_id"]==match_id]
    if row.empty: return False
    mdt = pd.to_datetime(row.iloc[0]["match_time_iso"], utc=True, errors="coerce")
    if pd.isna(mdt): return False
    lock_time = mdt - pd.Timedelta(minutes=LOCK_MINUTES_BEFORE)
    return now_utc() < lock_time

def judge_results(schedule_df: pd.DataFrame, picks_df: pd.DataFrame):
    if picks_df.empty:
        return pd.DataFrame(columns=["user","stage_id","match_id","pick_team","result"])
    merged = picks_df.merge(schedule_df[["match_id","winner_team"]], on="match_id", how="left")
    def r(row):
        w = row.get("winner_team","")
        if w == "": return "Waiting"
        return "Win" if row["pick_team"] == w else "Loss"
    merged["result"] = merged.apply(r, axis=1)
    return merged[["user","stage_id","match_id","pick_team","result"]]

def compute_leaderboard(results_df: pd.DataFrame):
    if results_df.empty:
        return pd.DataFrame(columns=["user","alive","wins","first_loss_stage"])
    
    try:
        all_users = results_df["user"].unique()
        losses = results_df[results_df["result"]=="Loss"]
        first_loss = losses.groupby("user")["stage_id"].min().rename("first_loss_stage") if not losses.empty else pd.Series(name="first_loss_stage", dtype="Int64")
        wins = results_df[results_df["result"]=="Win"].groupby("user")["stage_id"].count().rename("wins") if not results_df[results_df["result"]=="Win"].empty else pd.Series(name="wins", dtype="Int64")
        
        lb = pd.DataFrame({"user": all_users}).set_index("user")
        lb = lb.join([wins, first_loss])
        lb["wins"] = lb["wins"].fillna(0).astype(int)
        lb["alive"] = lb["first_loss_stage"].isna()
        
        return lb.reset_index().sort_values(by=["alive","wins","user"], ascending=[False,False,True])
    except:
        return pd.DataFrame(columns=["user","alive","wins","first_loss_stage"])

def get_or_make_assignment(user, stage_id, assignments_df, schedule_df):
    if not user or stage_id is None:
        return None, assignments_df
    
    try:
        stage_id = int(stage_id)
    except:
        return None, assignments_df
    
    cur = assignments_df[(assignments_df["user"]==user) & (assignments_df["stage_id"]==stage_id)]
    pool = eligible_matches(schedule_df, stage_id)
    
    if pool.empty: 
        return None, assignments_df

    if not cur.empty:
        mid = cur.iloc[0]["match_id"]
        still_ok = pool[pool["match_id"]==mid]
        if not still_ok.empty:
            return mid, assignments_df

    mid = deterministic_choice(pool["match_id"], user, stage_id)
    if mid:
        new_row = {"user": user, "stage_id": stage_id, "match_id": mid, "assigned_time_iso": now_utc().isoformat()}
        assignments_df = pd.concat([assignments_df, pd.DataFrame([new_row])], ignore_index=True)
        return mid, assignments_df
    
    return None, assignments_df

def record_pick(picks_df, user, stage_id, match_id, pick_team):
    if not all([user, stage_id, match_id, pick_team]):
        return picks_df, False, "Missing required fields."
    
    dup = picks_df[(picks_df["user"]==user) & (picks_df["stage_id"]==stage_id)]
    if not dup.empty: 
        return picks_df, False, "You already picked for this stage."
    
    new_row = {"user": user, "stage_id": stage_id, "match_id": match_id, "pick_team": pick_team, "pick_time_iso": now_utc().isoformat()}
    picks_df = pd.concat([picks_df, pd.DataFrame([new_row])], ignore_index=True)
    return picks_df, True, f"Locked {pick_team}"

# ============================== UI Components ==============================
def render_header():
    name = st.session_state.get("user_name") or "Guest"
    riot_id = st.session_state.get("riot_id") or ""
    
    display_name = name[:12] + "..." if len(name) > 12 else name
    display_subtitle = riot_id[:20] + "..." if len(riot_id) > 20 else riot_id
    
    st.markdown(f"""
    <div class="main-header">
        <div class="header-title">{icon_html("vct.png", 35)} VCT SURVIVOR</div>
        <div class="user-section">
            <span style="color:#111827; font-size: 14px;">{ms("person",16)} {display_name}</span>
            <span style="color:#6b7280; font-size:11px; display:block;">{display_subtitle}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    with st.sidebar:
        st.markdown("### Navigation")
        
        nav_buttons = [
            ("Home", "🏠"),
            ("Leaderboard", "🏆"), 
            ("My Stats", "📊"),
            ("Schedule", "📅"),
            ("Admin", "⚙️")
        ]
        
        for button_name, emoji in nav_buttons:
            if st.button(f"{emoji} {button_name}", key=f"nav_{button_name}", use_container_width=True):
                st.session_state.current_page = button_name
                st.rerun()

        st.markdown("---")
        st.markdown("### Quick Stats")

        results_df = judge_results(load_schedule(), load_picks())
        user = st.session_state.get("user_name") or ""
        me = results_df[results_df["user"] == user]

        wins = int((me["result"] == "Win").sum()) if not me.empty else 0
        losses = int((me["result"] == "Loss").sum()) if not me.empty else 0

        c1, c2 = st.columns(2)
        with c1: st.metric("Wins", wins)
        with c2: st.metric("Losses", losses)
        
        st.markdown("---")
        if st.button("Sign Out", key="sign_out"):
            for key in ['authenticated', 'user_email', 'user_name', 'riot_id']:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.current_page = "Home"
            st.rerun()

# ============================== Pages ==============================
def page_home():
    try:
        schedule_df = load_schedule()
        picks_df = load_picks()
        assign_df = load_assignments()
        results_df = judge_results(schedule_df, picks_df)
        lb_df = compute_leaderboard(results_df)
        
        user = st.session_state.user_name
        is_alive = True
        me = results_df[results_df["user"]==user]
        if not me.empty and any(me["result"]=="Loss"): 
            is_alive = False

        st.markdown(f"<div style='text-align:center;margin:20px 0;'>{badge('ALIVE','alive') if is_alive else badge('ELIMINATED','dead')}</div>", unsafe_allow_html=True)

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("## Current Match Assignment")
            act = active_stage(schedule_df)
            if not act:
                st.info("No active stage")
            else:
                st.markdown(f"<div class='game-card'><h3 style='color:var(--text);'>{act['stage_name']}</h3></div>", unsafe_allow_html=True)

                mid, assign_df = get_or_make_assignment(user, act["stage_id"], assign_df, schedule_df)
                if mid:
                    mrow = schedule_df[schedule_df["match_id"]==mid].iloc[0]
                    st.markdown(f"**Match ID:** `{mid}`")

                    col_team1, col_vs, col_team2 = st.columns([2, 1, 2])
                    with col_team1:
                        st.markdown(team_logo_html(mrow['team_a']), unsafe_allow_html=True)
                        st.markdown(f"<h3 style='text-align:center;color:var(--text);'>{mrow['team_a']}</h3>", unsafe_allow_html=True)
                    with col_vs:
                        st.markdown("<div style='text-align:center;padding-top:30px;'><h2 style='color:var(--accent);'>VS</h2></div>", unsafe_allow_html=True)
                    with col_team2:
                        st.markdown(team_logo_html(mrow['team_b']), unsafe_allow_html=True)
                        st.markdown(f"<h3 style='text-align:center;color:var(--text);'>{mrow['team_b']}</h3>", unsafe_allow_html=True)

                    col_time1, col_time2 = st.columns(2)
                    with col_time1:
                        st.markdown(f"Starts in: {countdown_to(mrow['match_time_iso'])}")
                        st.caption(f"Local: **{fmt_local(mrow['match_time_iso'])}**")
                    with col_time2:
                        st.markdown(f"Locks: {LOCK_MINUTES_BEFORE}m before")

                    existing = picks_df[(picks_df["user"]==user) & (picks_df["stage_id"]==act["stage_id"])]
                    if not existing.empty:
                        st.success(f"You picked: **{existing.iloc[0]['pick_team']}**")
                    elif not can_pick(schedule_df, mid):
                        st.error("Picks are locked")
                    else:
                        with st.form("pick_form"):
                            pick = st.selectbox("Select winner:", [mrow["team_a"], mrow["team_b"]])
                            if st.form_submit_button("Lock Pick", use_container_width=True):
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
                current_user = st.session_state.get("user_name", "")
                
                users_to_show = []
                
                # Add top 4
                for i in range(min(4, len(lb_df))):
                    row = lb_df.iloc[i]
                    users_to_show.append({'user': row['user'], 'rank': i+1, 'wins': row['wins'], 'alive': row['alive']})
                
                # Add current user if not in top 4
                current_user_in_top4 = any(u['user'] == current_user for u in users_to_show)
                if not current_user_in_top4:
                    user_row = lb_df[lb_df['user'] == current_user]
                    if not user_row.empty:
                        user_rank = user_row.index[0] + 1
                        users_to_show.append({
                            'user': current_user, 
                            'rank': user_rank, 
                            'wins': user_row.iloc[0]['wins'], 
                            'alive': user_row.iloc[0]['alive']
                        })
                
                st.markdown('<div class="leaderboard-container">', unsafe_allow_html=True)
                for user_data in users_to_show:
                    is_current = user_data['user'] == current_user
                    rank = user_data['rank']
                    
                    username = user_data['user']
                    display_username = username[:8] + "..." if len(username) > 8 else username
                    if is_current:
                        display_username += " (YOU)"
                    
                    if is_current:
                        border = "border: 2px solid #c8bf9b; background: rgba(200, 191, 155, 0.15);"
                        text_style = "font-weight:700; color:#c8bf9b; font-size: 12px;"
                    else:
                        border = ""
                        text_style = "font-weight:500; color:#ffffff; font-size: 12px;"
                    
                    st.markdown(f'''
                    <div class="leaderboard-row" style="{border}">
                        <div class="rank-badge">{rank}</div>
                        <div style="flex:1; {text_style} overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:70px;">{display_username}</div>
                        <div style="background:#f3f4f6;padding:2px 6px;border-radius:4px;color:#000000;font-size:10px;min-width:25px;text-align:center;">{user_data['wins']}W</div>
                        <div class="status-alive">ALIVE</div>
                    </div>
                    ''', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("No players yet")
    
    except Exception as e:
        st.error(f"Error: {e}")

def page_leaderboard():
    results_df = judge_results(load_schedule(), load_picks())
    lb_df = compute_leaderboard(results_df)
    st.markdown("# Global Leaderboard")
    
    if lb_df.empty:
        st.info("No players yet")
    else:
        for pos, (_, row) in enumerate(lb_df.iterrows(), start=1):
            st.markdown(f"**{pos}.** {row['user']} - {row['wins']} wins - {'ALIVE' if row['alive'] else 'DEAD'}")

def page_my_stats():
    user = st.session_state.user_name
    picks_df = load_picks()
    results_df = judge_results(load_schedule(), picks_df)
    my_results = results_df[results_df["user"]==user]

    st.markdown("# My Statistics")
    wins = int((my_results["result"]=="Win").sum()) if not my_results.empty else 0
    losses = int((my_results["result"]=="Loss").sum()) if not my_results.empty else 0
    waiting = int((my_results["result"]=="Waiting").sum()) if not my_results.empty else 0

    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Wins", wins)
    with c2: st.metric("Losses", losses)  
    with c3: st.metric("Pending", waiting)

def page_schedule():
    schedule_df = load_schedule()
    st.markdown("# Match Schedule")
    if schedule_df.empty:
        st.info("No matches scheduled")
    else:
        st.dataframe(schedule_df, use_container_width=True, hide_index=True)

def page_admin():
    st.markdown("# Admin Panel")
    st.info("Admin features go here")

# ============================== Main App ==============================
def main_app():
    inject_premium_css()
    ensure_files()
    render_header()
    render_sidebar()

    page = st.session_state.current_page
    if page == "Home": page_home()
    elif page == "Leaderboard": page_leaderboard()
    elif page == "My Stats": page_my_stats()
    elif page == "Schedule": page_schedule()
    elif page == "Admin": page_admin()

# ============================== Entry Point ==============================
if __name__ == "__main__":
    init_session_state()
    if not st.session_state.authenticated:
        show_initial_login()
    else:
        main_app()
