import os
import hashlib
import random
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st
from zoneinfo import ZoneInfo

# ============================== Page Config ==============================
st.set_page_config(page_title="VCT Random-Fixture Survivor", page_icon="🎯", layout="wide")

# ============================== Constants ==============================
ADMIN_KEY_ENV = "VLMS_ADMIN_KEY"   # optional: set to enable Admin in-app
LOCK_MINUTES_BEFORE = 5            # picks lock X minutes before match start
LOCAL_TZ = ZoneInfo("Asia/Kolkata")

# Required CSV schemas
REQ_SCHEDULE_COLS = {"stage_id","stage_name","match_id","team_a","team_b","match_time_iso","winner_team"}
REQ_PICKS_COLS    = {"user","stage_id","match_id","pick_team","pick_time_iso"}
REQ_ASSIGN_COLS   = {"user","stage_id","match_id","assigned_time_iso"}

# ============================== Writable Data Dir ==============================
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

# ============================== Material Symbols (kept for header) ==============================
def inject_icons_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24..48,400,0,0');
    .ms { font-family: 'Material Symbols Outlined'; font-weight: normal; font-style: normal;
         font-size: 18px; display:inline-block; line-height: 0; vertical-align: -4px;
         -webkit-font-feature-settings: 'liga'; -webkit-font-smoothing: antialiased; }
    .ms-accent { color: var(--accent, #7C3AED); }
    .main-header {
      display:flex; align-items:center; justify-content:space-between;
      padding: 10px 14px; border-radius: 14px;
      background: linear-gradient(120deg, rgba(124,58,237,.18), rgba(6,182,212,.14));
      border: 1px solid rgba(255,255,255,.10); margin-bottom: 10px;
    }
    .header-title { display:flex; align-items:center; gap:10px; font-size: 24px; font-weight: 800; }
    .user-section { display:flex; flex-direction:column; align-items:flex-end; }
    </style>
    """, unsafe_allow_html=True)

def ms(name: str, size: int = 18, cls: str = "") -> str:
    style = f"font-size:{size}px" if size != 18 else ""
    klass = "ms" + (f" {cls}" if cls else "")
    return f'<span class="{klass}" style="{style}">{name}</span>'

# ============================== Premium styling ==============================
def inject_premium_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24..48,400,0,0');

    :root{
      --bg:#ffffff; --panel:#fafafa; --muted:#6b7280; --text:#111827;
      --accent:#000000; --accent2:#374151; --ok:#059669; --warn:#d97706; --bad:#dc2626;
      --border:#e5e7eb; --hover:#f3f4f6; --shadow:0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
      --shadow-lg:0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
      --shadow-xl:0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    }
    
    /* Global Styles */
    .stApp{ 
      background:var(--bg); 
      color:var(--text); 
      font-family:'Inter',sans-serif;
      overflow-x:hidden;
    }
    
    /* Smooth scrolling and animations */
    * {
      scroll-behavior: smooth;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
      width: 8px;
    }
    
    ::-webkit-scrollbar-track {
      background: var(--panel);
    }
    
    ::-webkit-scrollbar-thumb {
      background: var(--muted);
      border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
      background: var(--accent2);
    }
    
    /* Header with premium styling */
    .main-header{ 
      background:var(--bg); 
      border-bottom:1px solid var(--border); 
      padding:20px 32px; 
      display:flex; 
      justify-content:space-between; 
      align-items:center; 
      position:sticky; 
      top:0; 
      z-index:100;
      box-shadow:var(--shadow);
      backdrop-filter: blur(20px);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .main-header:hover {
      box-shadow: var(--shadow-lg);
    }
    
    .header-title{ 
      font-family:'Inter',sans-serif; 
      font-size:28px; 
      font-weight:800; 
      color:var(--accent);
      letter-spacing:-0.025em;
      display: flex;
      align-items: center;
      gap: 12px;
      transition: all 0.3s ease;
    }
    
    .header-title:hover {
      transform: translateY(-1px);
    }
    
    .user-section{ 
      display:flex; 
      align-items:center; 
      gap:16px; 
      background:var(--panel);
      border:1px solid var(--border); 
      border-radius:12px; 
      padding:12px 20px; 
      font-size:14px;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      cursor: pointer;
    }
    
    .user-section:hover {
      background: var(--hover);
      border-color: var(--accent);
      transform: translateY(-2px);
      box-shadow: var(--shadow-lg);
    }
    
    /* Enhanced Game Cards */
    .game-card{ 
      background:var(--bg); 
      border:1px solid var(--border);
      border-radius:16px; 
      padding:32px; 
      box-shadow:var(--shadow);
      transition:all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
      overflow: hidden;
    }
    
    .game-card::before {
      content: '';
      position: absolute;
      top: 0;
      left: -100%;
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, transparent, rgba(0,0,0,0.02), transparent);
      transition: left 0.5s ease;
    }
    
    .game-card:hover::before {
      left: 100%;
    }
    
    .game-card:hover{
      box-shadow:var(--shadow-xl);
      transform:translateY(-4px);
      border-color: var(--accent);
    }
    
    .leaderboard-container{ 
      background:var(--bg); 
      border:1px solid var(--border); 
      border-radius:12px; 
      padding:4px; 
      box-shadow:var(--shadow);
    }
    
    .leaderboard-row{ 
      display:flex; 
      align-items:center; 
      padding:12px 16px; 
      margin:4px 0;
      background:var(--bg); 
      border-radius:8px; 
      transition:all 0.2s ease; 
      border:1px solid transparent; 
    }
    
    .leaderboard-row:hover{ 
      background:var(--hover); 
      border-color:var(--border);
      transform:translateX(2px); 
    }
    
    .rank-badge{ 
      width:32px; 
      height:32px; 
      display:flex; 
      align-items:center; 
      justify-content:center; 
      border-radius:6px; 
      font-weight:700; 
      margin-right:12px;
      font-size:14px;
    }
    
    .rank-1{background:var(--accent); color:white;}
    .rank-2{background:var(--accent2); color:white;}
    .rank-3{background:var(--muted); color:white;}
    .rank-other{background:var(--panel); color:var(--text); border:1px solid var(--border);}
    
    .status-alive{ 
      background:var(--ok); 
      color:white; 
      padding:4px 12px; 
      border-radius:6px; 
      font-size:11px; 
      font-weight:600; 
      text-transform:uppercase;
      letter-spacing:0.05em;
    }
    
    .status-dead{ 
      background:var(--bad); 
      color:white; 
      padding:4px 12px; 
      border-radius:6px; 
      font-size:11px; 
      font-weight:600; 
      text-transform:uppercase;
      letter-spacing:0.05em;
    }
    
    .stat-card{ 
      background:var(--bg); 
      border:1px solid var(--border); 
      border-radius:12px; 
      padding:20px; 
      text-align:center;
      box-shadow:var(--shadow);
      transition:all 0.2s ease;
    }
    
    .stat-card:hover{
      box-shadow:0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
      transform:translateY(-1px);
    }
    
    .stat-value{ 
      font-size:32px; 
      font-weight:800; 
      color:var(--accent);
      margin-bottom:4px;
    }
    
    .stat-label{ 
      font-size:12px; 
      color:var(--muted); 
      text-transform:uppercase; 
      letter-spacing:0.05em;
      font-weight:500;
    }
    
    #MainMenu, footer{ visibility:hidden; }

    /* Fixed Sidebar with Notion-style Navigation */
    .stSidebar {
      background: #fafbfc !important;
      border-right: 1px solid #e5e7eb !important;
      padding: 20px 0 !important;
      min-height: 100vh !important;
    }
    
    .stSidebar .sidebar-content {
      background: #fafbfc !important;
    }
    
    /* Ensure sidebar takes full height */
    .stSidebar > div {
      background: #fafbfc !important;
      min-height: 100vh !important;
    }
    
    /* Sidebar navigation container */
    .sidebar-nav {
      background: #fafbfc;
      padding: 16px 0;
      border-radius: 0;
    }
    
    /* Enhanced Navigation */
    .nav-row{ 
      display:flex; 
      align-items:center; 
      gap:12px; 
      padding:12px 20px; 
      margin:4px 8px;
      transition:all 0.2s ease; 
      color: #111827;
      font-weight: 600;
      font-size: 14px;
      border-radius: 6px;
      position: relative;
      background: transparent;
    }
    
    .nav-row:hover{ 
      background: #f3f4f6;
      color: #000000;
    }
    
    .nav-row.active{ 
      background: #000000; 
      color: white;
      font-weight: 700;
    }
    
    .nav-label{ 
      font-weight: 600; 
      font-size: 14px;
      color: inherit;
      user-select: none;
      flex: 1;
    }
    
    .nav-row:hover .nav-label {
      color: inherit;
    }
    
    /* Icon styling in navigation */
    .nav-row img {
      width: 20px;
      height: 20px;
      object-fit: contain;
      flex-shrink: 0;
    }
    
    /* Remove any button styling that might interfere */
    .stButton > button {
      background: transparent !important;
      border: none !important;
      box-shadow: none !important;
      padding: 0 !important;
      margin: 0 !important;
      min-height: 0 !important;
      height: auto !important;
    }
    
    .invisible-btn>button{ 
      opacity:0; 
      height:0; 
      padding:0; 
      margin:0; 
    }
    
    /* Form elements */
    .stButton > button {
      background:var(--accent) !important;
      color:white !important;
      border:1px solid var(--accent) !important;
      border-radius:8px !important;
      font-weight:500 !important;
      transition:all 0.2s ease !important;
    }
    
    .stButton > button:hover {
      background:var(--accent2) !important;
      border-color:var(--accent2) !important;
      transform:translateY(-1px) !important;
      box-shadow:0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
    }
    
    .stSelectbox > div > div {
      border:1px solid var(--border) !important;
      border-radius:8px !important;
    }
    
    .stTextInput > div > div > input {
      border:1px solid var(--border) !important;
      border-radius:8px !important;
    }
    
    /* Dataframe styling */
    .stDataFrame {
      border:1px solid var(--border) !important;
      border-radius:8px !important;
    }
    
    /* Success/Error messages */
    .stAlert {
      border-radius:8px !important;
      border:1px solid !important;
    }
    
    /* Badge styling */
    .badge {
      padding:6px 12px;
      border-radius:20px;
      font-size:12px;
      font-weight:600;
      text-transform:uppercase;
      letter-spacing:0.05em;
    }
    
    .badge.alive {
      background:var(--ok);
      color:white;
    }
    
    .badge.dead {
      background:var(--bad);
      color:white;
    }
    
    /* Team logo containers */
    .team-logo-container {
      background:var(--bg);
      border:1px solid var(--border);
      border-radius:12px;
      padding:16px;
      text-align:center;
      transition:all 0.2s ease;
    }
    
    .team-logo-container:hover {
      box-shadow:0 4px 6px -1px rgba(0, 0, 0, 0.1);
      transform:translateY(-1px);
    }
    
    /* VS separator */
    .vs-separator {
      display:flex;
      align-items:center;
      justify-content:center;
      font-size:18px;
      font-weight:600;
      color:var(--muted);
      padding:20px 0;
    }
    
    /* Match info */
    .match-info {
      background:var(--panel);
      border:1px solid var(--border);
      border-radius:8px;
      padding:16px;
      margin:16px 0;
    }
    
    .match-time {
      font-size:14px;
      color:var(--muted);
      margin:4px 0;
    }
    
    /* Pick form */
    .pick-form-container {
      background:var(--bg);
      border:1px solid var(--border);
      border-radius:12px;
      padding:20px;
      margin:16px 0;
    }
    
    /* Info boxes */
    .stAlert[data-baseweb="notification"] {
      border-radius:8px !important;
      border:1px solid var(--border) !important;
    }
    
    /* Metric cards */
    .stMetric {
      background:var(--bg);
      border:1px solid var(--border);
      border-radius:8px;
      padding:16px;
      text-align:center;
    }
    
    .stMetric > div > div {
      color:var(--accent) !important;
      font-weight:700 !important;
    }
    
    .stMetric > div > div:last-child {
      color:var(--muted) !important;
      font-weight:500 !important;
    }
    
    /* Loading Animations */
    @keyframes fadeInUp {
      from {
        opacity: 0;
        transform: translateY(30px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
    
    @keyframes slideInLeft {
      from {
        opacity: 0;
        transform: translateX(-30px);
      }
      to {
        opacity: 1;
        transform: translateX(0);
      }
    }
    
    @keyframes pulse {
      0%, 100% {
        transform: scale(1);
      }
      50% {
        transform: scale(1.05);
      }
    }
    
    /* Apply animations to main elements */
    .game-card, .stat-card, .leaderboard-row {
      animation: fadeInUp 0.6s ease-out;
    }
    
    .nav-row {
      animation: slideInLeft 0.6s ease-out;
    }
    
    /* Success animations */
    .stSuccess {
      animation: pulse 0.6s ease-in-out;
    }
    
    /* Material Icons enhancement */
    .ms {
      transition: all 0.3s ease;
    }
    
    .ms:hover {
      transform: scale(1.1);
    }
    
    .ms-accent { 
      color: var(--accent);
      transition: all 0.3s ease;
    }
    
    .ms-accent:hover {
      color: var(--accent2);
      transform: rotate(5deg);
    }
    </style>
    """, unsafe_allow_html=True)

def badge(text, cls):
    return f'<span class="badge {cls}">{text}</span>'

# ============================== Custom PNG Icons ==============================
# Sidebar PNG icons live in icons/

# Resolve ICON_DIR relative to this file; fallback to CWD if needed
ICON_DIR = Path(__file__).parent / "icons"
if not ICON_DIR.exists():
    ICON_DIR = Path.cwd() / "icons"

import base64
import mimetypes
from typing import Optional

def _data_uri_for_icon(path_or_name: str) -> Optional[str]:
    """Return a data: URI for an image in ICON_DIR (or absolute path)."""
    p = Path(path_or_name)
    if not p.exists():
        p = ICON_DIR / path_or_name  # try inside ICON_DIR
    if not p.exists():
        return None

    mime, _ = mimetypes.guess_type(p.name)
    if not mime:
        mime = "image/png"

    try:
        data = p.read_bytes()
    except Exception:
        return None

    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{b64}"

def icon_html(path_or_name: str, size: int = 18) -> str:
    """
    Render an <img> tag for a sidebar icon using a data: URI.
    `path_or_name` can be a filename in ICON_DIR (e.g., 'home.png')
    or an absolute/relative path.
    """
    uri = _data_uri_for_icon(path_or_name)
    if not uri:
        # graceful fallback: small rounded placeholder block
        return (
            f'<span style="display:inline-block;width:{size}px;height:{size}px;'
            'background:rgba(255,255,255,.08);border-radius:4px;"></span>'
        )
    return (
        f'<img class="nav-icon" src="{uri}" '
        f'style="width:{size}px;height:{size}px;object-fit:contain;vertical-align:-3px;" />'
    )

# ============================== Team Logos ==============================
def get_team_logo_placeholder(team_name):
    """Enhanced colored block fallback when a real logo isn't found."""
    colors = {
        "GEN": "#000000", "GEN.G": "#000000",
        "FPX": "#374151", "FNC": "#6b7280",
        "TL": "#111827", "DRX": "#9ca3af",
        "PRX": "#d1d5db", "T1": "#e5e7eb",
        "EDG": "#000000", "LOUD": "#059669",
        "NRG": "#d97706", "SEN": "#dc2626",
        "100T": "#7c3aed", "LEV": "#06b6d4",
        "NAVI": "#f59e0b", "VIT": "#10b981",
        "TH": "#ef4444", "KC": "#3b82f6"
    }
    color = colors.get((team_name or "").upper(), "#000000")
    return f"""
    <div style="width:90px;height:90px;background:{color};border-radius:16px;display:flex;
                align-items:center;justify-content:center;font-size:22px;font-weight:800;color:white;
                margin:0 auto 8px;box-shadow:0 8px 25px rgba(0,0,0,0.15);
                border:2px solid #e5e7eb;transition:all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                cursor:pointer;position:relative;overflow:hidden;animation:fadeInUp 0.8s ease-out;">
        <div style="position:absolute;top:0;left:-100%;width:100%;height:100%;
                    background:linear-gradient(90deg,transparent,rgba(255,255,255,0.3),transparent);
                    transition:left 0.6s ease;"></div>
        <span style="position:relative;z-index:1;text-shadow:0 2px 4px rgba(0,0,0,0.3);">{(team_name or '')[:3].upper()}</span>
    </div>
    """

def team_logo_html(team_name: str):
    """Try local /icons/<TEAM>.(png|svg|jpg|jpeg|webp) else fallback."""
    t = (team_name or "").strip()
    if not t:
        return get_team_logo_placeholder("—")
    # Try multiple possible icon directories
    icon_dirs = [
        Path("icons"),
        Path(__file__).parent / "icons",
        Path.cwd() / "icons"
    ]
    for icon_dir in icon_dirs:
        if icon_dir.exists():
            base = icon_dir / f"{t.upper()}"
            for ext in (".png", ".svg", ".jpg", ".jpeg", ".webp"):
                p = base.with_suffix(ext)
                if p.exists():
                    try:
                        # Use relative path for Streamlit
                        relative_path = p.relative_to(Path.cwd())
                        return f"""
                        <div class="team-logo-container">
                            <img src="{relative_path}" style="max-width:80px;max-height:80px;border-radius:8px;"/>
                        </div>
                        """
                    except Exception:
                        # Fallback to data URI if relative path fails
                        continue
    return get_team_logo_placeholder(t)

# ============================== Auth / Session ==============================
def init_session_state():
    if 'authenticated' not in st.session_state: st.session_state.authenticated = False
    if 'user_email' not in st.session_state:   st.session_state.user_email = None
    if 'user_name' not in st.session_state:    st.session_state.user_name = None
    if 'current_page' not in st.session_state: st.session_state.current_page = "Home"
    if 'show_google_signin' not in st.session_state: st.session_state.show_google_signin = False

def show_initial_login():
    st.markdown("""
    <style>
    .stApp { background:#ffffff; } #MainMenu, footer, header{visibility:hidden;}
    .login-container{ max-width:400px; margin:100px auto; padding:40px; background:white; border-radius:12px; box-shadow:0 2px 10px rgba(0,0,0,.08);}
    .app-title{ font-size:24px; font-weight:600; color:#111827; margin-bottom:8px;}
    .app-subtitle{ font-size:14px; color:#6b7280; }
    .form-title{ font-size:20px; font-weight:500; text-align:center; margin-bottom:8px;}
    .form-subtitle{ font-size:14px; color:#6b7280; text-align:center; margin-bottom:24px;}
    .divider{ text-align:center; margin:24px 0; color:#6b7280; font-size:14px;}
    .terms-text{ text-align:center; font-size:12px; color:#6b7280; margin-top:24px; line-height:18px;}
    .terms-text a{ color:#000000; text-decoration:none;}
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div class="app-title">VCT SURVIVOR</div>
        <div class="app-subtitle">Official Tournament Prediction Platform</div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="form-title">Create an account</div><div class="form-subtitle">Enter your email to sign up for this app</div>', unsafe_allow_html=True)
        email = st.text_input("Email", placeholder="email@domain.com", key="initial_email", label_visibility="collapsed")

        if st.button("Continue", use_container_width=True, type="primary"):
            if email and '@' in email:
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.session_state.user_name = email.split('@')[0]
                st.success("✓ Account created successfully"); st.balloons(); st.rerun()
            else:
                st.error("Please enter a valid email address")

        st.markdown('<div class="divider">or</div>', unsafe_allow_html=True)

        if st.button("Continue with Google", use_container_width=True):
            st.session_state.show_google_signin = True; st.rerun()

        st.markdown("""
        <div class="terms-text">By clicking continue, you agree to our<br>
        <a href="#">Terms of Service</a> and <a href="#">Privacy Policy</a></div>
        """, unsafe_allow_html=True)

def show_google_signin():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.image("https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png", width=150)
        st.markdown("<div style='text-align:center;font-size:24px;margin:8px 0;'>Sign in</div><div style='text-align:center;color:#6b7280;'>Continue to VCT Survivor</div>", unsafe_allow_html=True)
        email = st.text_input("Email or phone", placeholder="Enter your email", key="google_email", label_visibility="collapsed")
        col_left, col_right = st.columns([1, 1])
        with col_left:
            if st.button("Back"):
                st.session_state.show_google_signin = False; st.rerun()
        with col_right:
            if st.button("Next", use_container_width=True, type="primary"):
                if email and '@' in email:
                    st.session_state.authenticated = True
                    st.session_state.user_email = email
                    st.session_state.user_name = email.split('@')[0]
                    st.session_state.show_google_signin = False
                    st.success("✓ Signed in successfully"); st.balloons(); st.rerun()
                else:
                    st.error("Please enter a valid email address")

# ============================== Data Utils ==============================
def ensure_files():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SCHEDULE_CSV.exists(): pd.DataFrame(columns=sorted(REQ_SCHEDULE_COLS)).to_csv(SCHEDULE_CSV, index=False)
    if not PICKS_CSV.exists():    pd.DataFrame(columns=sorted(REQ_PICKS_COLS)).to_csv(PICKS_CSV, index=False)
    if not ASSIGN_CSV.exists():   pd.DataFrame(columns=sorted(REQ_ASSIGN_COLS)).to_csv(ASSIGN_CSV, index=False)

def _read_csv(path: Path, required: set[str]):
    if not path.exists(): 
        return pd.DataFrame(columns=sorted(required))
    try:
        df = pd.read_csv(path, dtype=str).fillna("")
        # Validate that all required columns exist
        missing = required - set(df.columns)
        if missing:
            st.error(f"`{path.name}` is missing columns: {', '.join(sorted(missing))}")
            return pd.DataFrame(columns=sorted(required))
        return df
    except pd.errors.EmptyDataError:
        st.warning(f"`{path.name}` is empty, creating new file")
        return pd.DataFrame(columns=sorted(required))
    except pd.errors.ParserError as e:
        st.error(f"Failed to parse `{path.name}`: {e}")
        return pd.DataFrame(columns=sorted(required))
    except Exception as e:
        st.error(f"Failed to read `{path.name}`: {e}")
        return pd.DataFrame(columns=sorted(required))

def load_schedule():
    df = _read_csv(SCHEDULE_CSV, REQ_SCHEDULE_COLS)
    if df.empty: 
        df["stage_id"] = pd.Series(dtype="Int64")
    else:        
        df["stage_id"] = pd.to_numeric(df["stage_id"], errors="coerce").fillna(0).astype("Int64")
    return df.sort_values(["stage_id", "match_time_iso"])

def load_picks():
    df = _read_csv(PICKS_CSV, REQ_PICKS_COLS)
    if df.empty: 
        df["stage_id"] = pd.Series(dtype="Int64")
    else:        
        df["stage_id"] = pd.to_numeric(df["stage_id"], errors="coerce").fillna(0).astype("Int64")
    return df

def load_assignments():
    df = _read_csv(ASSIGN_CSV, REQ_ASSIGN_COLS)
    if df.empty: 
        df["stage_id"] = pd.Series(dtype="Int64")
    else:        
        df["stage_id"] = pd.to_numeric(df["stage_id"], errors="coerce").fillna(0).astype("Int64")
    return df

def save_picks(df): df.to_csv(PICKS_CSV, index=False)
def save_assign(df): df.to_csv(ASSIGN_CSV, index=False)

def now_utc(): return datetime.now(timezone.utc)

# ============================== Time Helpers ==============================
def fmt_local(dt_iso: str, fmt: str = "%b %d, %Y • %I:%M %p"):
    dt = pd.to_datetime(dt_iso, utc=True, errors="coerce")
    if pd.isna(dt): return "—"
    return dt.tz_convert(LOCAL_TZ).strftime(fmt)

def fmt_utc(dt_iso: str, fmt: str = "%Y-%m-%d %H:%M UTC"):
    dt = pd.to_datetime(dt_iso, utc=True, errors="coerce")
    if pd.isna(dt): return "—"
    return dt.strftime(fmt)

def countdown_to(dt_iso: str):
    try:
        dt = pd.to_datetime(dt_iso, utc=True, errors="coerce")
        if pd.isna(dt): return "—"
        # Ensure dt is timezone-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        now = now_utc()
        secs = int((dt - now).total_seconds())
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

def lock_deadline(schedule_df, match_id, minutes_before=LOCK_MINUTES_BEFORE):
    row = schedule_df[schedule_df["match_id"]==match_id]
    if row.empty: return now_utc()
    mdt = pd.to_datetime(row.iloc[0]["match_time_iso"], utc=True, errors="coerce")
    if pd.isna(mdt): return now_utc()
    return mdt - pd.Timedelta(minutes=minutes_before)

def can_pick(schedule_df, match_id): return now_utc() < lock_deadline(schedule_df, match_id)

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
        # Handle losses
        losses = results_df[results_df["result"]=="Loss"].sort_values(["user","stage_id"])
        first_loss = losses.groupby("user")["stage_id"].min().rename("first_loss_stage")
        
        # Handle wins
        wins = (results_df[results_df["result"]=="Win"].groupby("user")["stage_id"].count().rename("wins"))
        
        # Create leaderboard
        lb = pd.DataFrame(index=results_df["user"].unique()).join([wins, first_loss])
        lb["wins"] = lb["wins"].fillna(0).astype(int)
        lb["alive"] = lb["first_loss_stage"].isna()
        
        # Sort by alive status (alive first) then by wins (descending)
        return lb.reset_index().rename(columns={"index":"user"}).sort_values(by=["alive","wins"], ascending=[False,False])
    
    except Exception as e:
        st.error(f"Error computing leaderboard: {e}")
        return pd.DataFrame(columns=["user","alive","wins","first_loss_stage"])

def get_or_make_assignment(user, stage_id, assignments_df, schedule_df):
    # Input validation
    if not user or stage_id is None:
        return None, assignments_df
    
    try:
        stage_id = int(stage_id)
    except (ValueError, TypeError):
        return None, assignments_df
    
    # Check existing assignment
    cur = assignments_df[(assignments_df["user"]==user) & (assignments_df["stage_id"]==stage_id)]
    pool = eligible_matches(schedule_df, stage_id)
    
    if pool.empty: 
        return None, assignments_df

    if not cur.empty:
        mid = cur.iloc[0]["match_id"]
        still_ok = pool[pool["match_id"]==mid]
        if not still_ok.empty:
            return mid, assignments_df
        
        # Reassign to a new match if current assignment is no longer valid
        new_mid = deterministic_choice(pool["match_id"], user, stage_id, salt="fallback")
        if new_mid:
            assignments_df.loc[cur.index, ["match_id","assigned_time_iso"]] = [new_mid, now_utc().isoformat()]
            return new_mid, assignments_df

    # Create new assignment
    mid = deterministic_choice(pool["match_id"], user, stage_id)
    if mid:
        new_row = {
            "user": user, 
            "stage_id": stage_id, 
            "match_id": mid, 
            "assigned_time_iso": now_utc().isoformat()
        }
        assignments_df = pd.concat([assignments_df, pd.DataFrame([new_row])], ignore_index=True)
        return mid, assignments_df
    
    return None, assignments_df

def record_pick(picks_df, user, stage_id, match_id, pick_team):
    # Input validation
    if not user or not stage_id or not match_id or not pick_team:
        return picks_df, False, "Missing required fields."
    
    try:
        stage_id = int(stage_id)
    except (ValueError, TypeError):
        return picks_df, False, "Invalid stage ID."
    
    # Check if user already picked for this stage
    dup = picks_df[(picks_df["user"]==user) & (picks_df["stage_id"]==stage_id)]
    if not dup.empty: 
        return picks_df, False, "You already picked for this stage."
    
    # Load schedule to validate match and teams
    sched = load_schedule()
    row = sched[sched["match_id"]==match_id]
    if row.empty: 
        return picks_df, False, "Match not found."
    
    ta, tb = row.iloc[0]["team_a"], row.iloc[0]["team_b"]
    if pick_team not in {ta, tb}: 
        return picks_df, False, "Invalid team selection."
    
    # Check if picks are locked
    if not can_pick(sched, match_id):
        return picks_df, False, "Picks are locked for this match."
    
    # Create new pick record
    new_row = {
        "user": user, 
        "stage_id": stage_id, 
        "match_id": match_id, 
        "pick_team": pick_team, 
        "pick_time_iso": now_utc().isoformat()
    }
    picks_df = pd.concat([picks_df, pd.DataFrame([new_row])], ignore_index=True)
    return picks_df, True, f"Locked {pick_team}"

# ============================== Header ==============================
def render_header():
    name = st.session_state.get("user_name") or "Guest"
    email = st.session_state.get("user_email") or ""
    st.markdown(f"""
    <div class="main-header">
        <div class="header-title">{icon_html("vct.png", 28)} VCT SURVIVOR</div>
        <div class="user-section">
                            <span style="color:#111827;">{ms("person",18)} {name}</span>
                <span style="color:#6b7280; font-size:12px;">{email}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar sign-out row with your PNG icon
    with st.sidebar:
        c1, c2 = st.columns([0.15, 0.85])
        c1.markdown(icon_html("logout.png", 18), unsafe_allow_html=True)
        if c2.button("Sign Out", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_email = None
            st.session_state.user_name = None
            st.session_state.current_page = "Home"
            st.rerun()

# ============================== Sidebar (PNG icons) ==============================
def render_sidebar():
    with st.sidebar:
        st.markdown("## Navigation")

        # Map label -> icon file. Replace with your own filenames if different:
        nav_items = [
            ("Home",        "home.png"),
            ("Leaderboard", "leaderboard.png"),
            ("My Stats",    "leaderboard.png"),   # <- change to your stats icon file, e.g. "stats.png"
            ("Schedule",    "schedule.png"),
            ("Admin",       "setting.png"),       # <- change to your admin icon file if different
        ]

        current = st.session_state.current_page

        for label, icon_file in nav_items:
            active = (current == label)
            
            # Create a container for the navigation row
            col1, col2 = st.columns([0.9, 0.1])
            
            with col1:
                # Show the styled navigation row
                st.markdown(
                    f"""
                    <div class="nav-row {'active' if active else ''}">
                        {icon_html(icon_file, 18)}
                        <span class="nav-label">{label}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            with col2:
                # Small, invisible button that's easier to click
                if st.button("", key=f"nav_{label}", help=label):
                    st.session_state.current_page = label
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
            st.markdown("## 🏳️ Current Match Assignment")
            act = active_stage(schedule_df)
            if not act:
                st.info("No active stage. Wait for the next stage to begin.")
            else:
                with st.container():
                    st.markdown(f"<div class='game-card'><h3 style='color:#000000;'>{act['stage_name']}</h3><p style='color:#6b7280;'>Stage {act['stage_id']}</p></div>", unsafe_allow_html=True)

                    mid, assign_df = get_or_make_assignment(user, act["stage_id"], assign_df, schedule_df)
                    if mid:
                        mrow = schedule_df[schedule_df["match_id"]==mid].iloc[0]
                        st.markdown(f"**Match ID:** `{mid}`")

                        col_team1, col_vs, col_team2 = st.columns([2, 1, 2])
                        with col_team1:
                            st.markdown(team_logo_html(mrow['team_a']), unsafe_allow_html=True)
                            st.markdown(f"<h3 style='text-align:center;color:#111827;margin:0;'>{mrow['team_a']}</h3>", unsafe_allow_html=True)
                        with col_vs:
                            st.markdown("<div style='text-align:center;padding-top:30px;'><h2 style='color:#6b7280;'>VS</h2></div>", unsafe_allow_html=True)
                        with col_team2:
                            st.markdown(team_logo_html(mrow['team_b']), unsafe_allow_html=True)
                            st.markdown(f"<h3 style='text-align:center;color:#111827;margin:0;'>{mrow['team_b']}</h3>", unsafe_allow_html=True)

                        local_str = fmt_local(mrow['match_time_iso'])
                        utc_str = fmt_utc(mrow['match_time_iso'])
                        lock_dt = pd.to_datetime(mrow['match_time_iso'], utc=True, errors="coerce") - pd.Timedelta(minutes=LOCK_MINUTES_BEFORE)
                        lock_str = fmt_local(lock_dt.isoformat())

                        col_time1, col_time2 = st.columns(2)
                        with col_time1:
                            st.markdown(f"⏱️ **Starts in:** {countdown_to(mrow['match_time_iso'])}")
                            st.caption(f"Local: **{local_str}**  ·  <span title='{utc_str}'>UTC shown on hover</span>", unsafe_allow_html=True)
                        with col_time2:
                            st.markdown(f"🔒 **Locks:** {LOCK_MINUTES_BEFORE}m before")
                            st.caption(f"Lock deadline (local): **{lock_str}**")

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
                                        save_picks(picks_df); st.success(msg); st.balloons(); st.rerun()
                                    else:
                                        st.error(msg)
                    save_assign(assign_df)

        with col2:
            st.markdown("## Quick Leaderboard")
            if not lb_df.empty:
                st.markdown('<div class="leaderboard-container">', unsafe_allow_html=True)
                for pos, (_, row) in enumerate(lb_df.head(5).iterrows(), start=1):
                    rank = pos
                    rank_class = f"rank-{rank}" if rank <= 3 else "rank-other"
                    rank_icon = "👑" if rank == 1 else f"#{rank}"
                    st.markdown(f'''
                    <div class="leaderboard-row">
                        <div class="rank-badge {rank_class}">{rank_icon}</div>
                        <div style="flex:1;font-weight:600;">{row['user']}</div>
                        <div style="color:#000000;margin-right:12px;">{row['wins']}W</div>
                        <div class="{'status-alive' if row['alive'] else 'status-dead'}">{'ALIVE' if row['alive'] else 'DEAD'}</div>
                    </div>
                    ''', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"An error occurred while loading the home page: {e}")
        st.info("Please try refreshing the page or contact support if the issue persists.")

def page_leaderboard():
    try:
        results_df = judge_results(load_schedule(), load_picks())
        lb_df = compute_leaderboard(results_df)
        st.markdown("# 🏆 Global Leaderboard")

        if lb_df.empty:
            st.info("No players have made picks yet")
            return

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"<div class='stat-card'><div class='stat-value'>{len(lb_df)}</div><div class='stat-label'>Total Players</div></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='stat-card'><div class='stat-value'>{lb_df['alive'].sum()}</div><div class='stat-label'>Still Alive</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='stat-card'><div class='stat-value'>{(~lb_df['alive']).sum()}</div><div class='stat-label'>Eliminated</div></div>", unsafe_allow_html=True)
        with c4:
            st.markdown(f"<div class='stat-card'><div class='stat-value'>{lb_df['wins'].max() if not lb_df.empty else 0}</div><div class='stat-label'>Max Wins</div></div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="leaderboard-container" style="margin-top: 20px;">', unsafe_allow_html=True)
        for pos, (_, row) in enumerate(lb_df.iterrows(), start=1):
            rank = pos
            rank_class = f"rank-{rank}" if rank <= 3 else "rank-other"
            rank_icon = "👑" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
            stage_info = f" (Stage {int(row['first_loss_stage'])})" if not row['alive'] and pd.notna(row.get('first_loss_stage')) else ""
            st.markdown(f'''
            <div class="leaderboard-row">
                <div class="rank-badge {rank_class}">{rank_icon}</div>
                <div style="flex:1;font-weight:600;color:#111827;">{row['user']}{stage_info}</div>
                <div style="background:#f3f4f6;padding:4px 12px;border-radius:6px;margin-right:12px;color:#000000;border:1px solid #e5e7eb;">{row['wins']} WINS</div>
                <div class="{'status-alive' if row['alive'] else 'status-dead'}">{'ALIVE' if row['alive'] else 'DEAD'}</div>
            </div>
            ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"An error occurred while loading the leaderboard: {e}")
        st.info("Please try refreshing the page or contact support if the issue persists.")

def page_my_stats():
    try:
        user = st.session_state.user_name
        picks_df = load_picks()
        results_df = judge_results(load_schedule(), picks_df)
        my_results = results_df[results_df["user"]==user]

        st.markdown("# 📊 My Statistics")
        c1, c2, c3, c4 = st.columns(4)

        wins = int((my_results["result"]=="Win").sum()) if not my_results.empty else 0
        losses = int((my_results["result"]=="Loss").sum()) if not my_results.empty else 0
        waiting = int((my_results["result"]=="Waiting").sum()) if not my_results.empty else 0
        total = len(my_results)

        with c1: st.metric("Total Picks", total)
        with c2: st.metric("Wins", wins, f"{(wins/total*100):.0f}%" if total > 0 else "—")
        with c3: st.metric("Losses", losses)
        with c4: st.metric("Pending", waiting)

        st.markdown("---")
        st.markdown("## Pick History")
        my_picks = picks_df[picks_df["user"]==user]
        if my_picks.empty: 
            st.info("You haven't made any picks yet")
        else: 
            st.dataframe(my_picks.sort_values("stage_id", ascending=False), use_container_width=True, hide_index=True)
    
    except Exception as e:
        st.error(f"An error occurred while loading your stats: {e}")
        st.info("Please try refreshing the page or contact support if the issue persists.")

def page_schedule():
    try:
        schedule_df = load_schedule()
        st.markdown("# 🗓️ Match Schedule")
        if schedule_df.empty:
            st.info("No matches scheduled yet")
        else:
            df = schedule_df.copy()
            df["match_time_local"] = df["match_time_iso"].apply(fmt_local)
            df["match_time_utc"]   = df["match_time_iso"].apply(fmt_utc)
            st.dataframe(df[["stage_id","stage_name","match_id","team_a","team_b","match_time_local","match_time_utc","winner_team"]],
                         use_container_width=True, hide_index=True)
    
    except Exception as e:
        st.error(f"An error occurred while loading the schedule: {e}")
        st.info("Please try refreshing the page or contact support if the issue persists.")

def page_admin():
    try:
        st.markdown("# ⚙️ Admin Panel")
        entered = st.text_input("Admin key:", type="password")
        if entered and os.environ.get(ADMIN_KEY_ENV) and entered == os.environ.get(ADMIN_KEY_ENV):
            st.success("Admin access granted")
            schedule_df = load_schedule()
            st.download_button("📥 Download schedule.csv", schedule_df.to_csv(index=False), "schedule.csv")
            up = st.file_uploader("📤 Upload new schedule.csv", type=["csv"])
            if up:
                try:
                    new_sched = pd.read_csv(up, dtype=str).fillna("")
                except Exception as e:
                    st.error(f"Failed reading schedule: {e}")
                    return
                missing = REQ_SCHEDULE_COLS - set(new_sched.columns)
                if missing: 
                    st.error(f"Uploaded schedule missing columns: {', '.join(sorted(missing))}")
                else:
                    new_sched.to_csv(SCHEDULE_CSV, index=False)
                    st.success("Schedule updated!")
                    st.rerun()
        else:
            st.info("Enter admin key to access admin features")
    
    except Exception as e:
        st.error(f"An error occurred in the admin panel: {e}")
        st.info("Please try refreshing the page or contact support if the issue persists.")

# ============================== Router ==============================
def main_app():
    inject_icons_css()
    inject_premium_css()
    ensure_files()

    render_header()
    render_sidebar()

    page = st.session_state.current_page
    if page == "Home": page_home()
    elif page == "Leaderboard": page_leaderboard()
    elif page == "My Stats" or page == "Stats": page_my_stats()
    elif page == "Schedule": page_schedule()
    elif page == "Admin": page_admin()
    else: page_home()

# ============================== Entrypoint ==============================
if __name__ == "__main__":
    init_session_state()
    if not st.session_state.authenticated:
        if st.session_state.show_google_signin: show_google_signin()
        else: show_initial_login()
    else:
        main_app()
