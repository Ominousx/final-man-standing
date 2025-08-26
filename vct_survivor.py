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
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800;900&display=swap');
    
    :root {
        --bg: #0a0a0a;
        --panel: #1a1a1a;
        --panel-dark: #0f0f0f;
        --text: #ffffff;
        --text-muted: #cccccc;
        --accent: #c8bf9b;
        --accent-glow: #d4ccb0;
        --accent-dark: #a89f7e;
        --border: #333333;
        --hover: #2a2a2a;
        --shadow: 0 8px 32px rgba(0, 0, 0, 0.8);
        --shadow-glow: 0 0 20px rgba(200, 191, 155, 0.3);
        --gradient: linear-gradient(135deg, #c8bf9b 0%, #d4ccb0 100%);
    }
    
    /* Global Styles */
    .stApp {
        background: var(--bg);
        color: var(--text);
        font-family: 'Poppins', sans-serif;
        overflow-x: hidden;
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--panel-dark);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--accent);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-glow);
    }
    
    /* Header Styling */
    .main-header {
        background: linear-gradient(135deg, var(--panel) 0%, var(--panel-dark) 100%);
        border-bottom: 2px solid var(--accent);
        box-shadow: var(--shadow);
        padding: 20px 0;
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: var(--gradient);
        animation: shimmer 3s ease-in-out infinite;
    }
    
    .header-title {
        font-family: 'Poppins', sans-serif;
        font-size: 2.5rem;
        font-weight: 800;
        color: var(--text);
        text-shadow: 0 0 20px rgba(200, 191, 155, 0.5);
        letter-spacing: 1px;
        display: flex;
        align-items: center;
        gap: 15px;
        justify-content: center;
    }
    
    .header-title img {
        filter: drop-shadow(0 0 10px var(--accent));
        animation: pulse 2s ease-in-out infinite;
        width: 45px;
        height: 45px;
        object-fit: contain;
        margin-right: 5px;
    }
    
    .user-section {
        background: rgba(200, 191, 155, 0.1);
        border: 1px solid var(--accent);
        border-radius: 25px;
        padding: 12px 25px;
        color: var(--text);
        font-weight: 600;
        backdrop-filter: blur(10px);
        box-shadow: var(--shadow-glow);
    }
    
    /* Game Card Styling */
    .game-card {
        background: linear-gradient(145deg, var(--panel) 0%, var(--panel-dark) 100%);
        border: 2px solid var(--border);
        border-radius: 20px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: var(--shadow);
        transition: all 0.3s ease;
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
        background: linear-gradient(90deg, transparent, rgba(200, 191, 155, 0.1), transparent);
        transition: left 0.5s ease;
    }
    
    .game-card:hover::before {
        left: 100%;
    }
    
    .game-card:hover {
        border-color: var(--accent);
        box-shadow: var(--shadow-glow);
        transform: translateY(-5px);
    }
    
    .game-card h3 {
        color: var(--accent);
        font-family: 'Poppins', sans-serif;
        font-size: 1.4rem;
        font-weight: 700;
        text-shadow: 0 0 10px rgba(200, 191, 155, 0.3);
        margin-bottom: 15px;
        text-align: center;
    }
    
    /* Team Logo Styling */
    .team-logo-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 20px;
        margin: 20px 0;
    }
    
    .team-logo {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        border: 3px solid var(--accent);
        box-shadow: var(--shadow-glow);
        transition: all 0.3s ease;
        background: var(--panel-dark);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        color: var(--text);
        font-size: 1.2rem;
    }
    
    .team-logo:hover {
        transform: scale(1.1);
        box-shadow: 0 0 30px var(--accent);
    }
    
    /* Team logo image styling */
    .team-logo-container img {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        border: 3px solid var(--accent);
        box-shadow: var(--shadow-glow);
        transition: all 0.3s ease;
        object-fit: cover;
        background: var(--panel-dark);
    }
    
    .team-logo-container img:hover {
        transform: scale(1.1);
        box-shadow: 0 0 30px var(--accent);
        border-color: var(--accent-glow);
    }
    
    .vs-separator {
        font-family: 'Poppins', sans-serif;
        font-size: 2rem;
        font-weight: 800;
        color: var(--accent);
        text-shadow: 0 0 15px rgba(200, 191, 155, 0.5);
        animation: pulse 2s ease-in-out infinite;
    }
    
    /* Match Info Styling */
    .match-info {
        background: rgba(200, 191, 155, 0.05);
        border: 1px solid var(--accent);
        border-radius: 15px;
        padding: 15px;
        margin: 15px 0;
        text-align: center;
    }
    
    .match-time {
        color: var(--accent);
        font-family: 'Poppins', sans-serif;
        font-weight: 500;
        font-size: 1.1rem;
        margin-bottom: 10px;
    }
    
    .match-status {
        color: var(--text-muted);
        font-weight: 500;
    }
    
    /* Pick Form Styling */
    .pick-form-container {
        background: var(--panel-dark);
        border: 2px solid var(--border);
        border-radius: 15px;
        padding: 20px;
        margin: 20px 0;
        text-align: center;
    }
    
    .pick-form-container h4 {
        color: var(--accent);
        font-family: 'Poppins', sans-serif;
        font-weight: 700;
        margin-bottom: 15px;
        text-shadow: 0 0 10px rgba(200, 191, 155, 0.3);
    }
    
    /* Leaderboard Styling */
    .leaderboard-container {
        background: var(--panel);
        border: 2px solid var(--border);
        border-radius: 20px;
        padding: 25px;
        margin: 20px 0;
        box-shadow: var(--shadow);
    }
    
    .leaderboard-container h3 {
        color: var(--accent);
        font-family: 'Poppins', sans-serif;
        font-weight: 700;
        text-align: center;
        margin-bottom: 25px;
        text-shadow: 0 0 15px rgba(200, 191, 155, 0.3);
        font-size: 1.8rem;
    }
    
    .leaderboard-row {
        background: var(--panel-dark);
        border: 1px solid var(--border);
        border-radius: 15px;
        padding: 15px 20px;
        margin: 10px 0;
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: all 0.3s ease;
        animation: slideInLeft 0.6s ease-out;
    }
    
    .leaderboard-row:hover {
        border-color: var(--accent);
        background: var(--hover);
        transform: translateX(10px);
        box-shadow: var(--shadow-glow);
    }
    
    .rank-badge {
        background: var(--gradient);
        color: var(--bg);
        font-weight: 700;
        padding: 8px 15px;
        border-radius: 20px;
        font-family: 'Poppins', sans-serif;
        box-shadow: var(--shadow-glow);
    }
    
    .status-alive {
        color: #00ff88;
        font-weight: 600;
        text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
    }
    
    .status-dead {
        color: #ff4444;
        font-weight: 600;
        text-shadow: 0 0 10px rgba(255, 68, 68, 0.5);
    }
    
    /* Stats Styling */
    .stat-card {
        background: linear-gradient(145deg, var(--panel) 0%, var(--panel-dark) 100%);
        border: 2px solid var(--border);
        border-radius: 20px;
        padding: 25px;
        margin: 20px 0;
        text-align: center;
        box-shadow: var(--shadow);
        transition: all 0.3s ease;
        animation: fadeInUp 0.8s ease-out;
    }
    
    .stat-card:hover {
        border-color: var(--accent);
        transform: translateY(-5px);
        box-shadow: var(--shadow-glow);
    }
    
    .stat-value {
        font-family: 'Poppins', sans-serif;
        font-size: 3rem;
        font-weight: 800;
        color: var(--accent);
        text-shadow: 0 0 20px rgba(200, 191, 155, 0.5);
        margin-bottom: 10px;
    }
    
    .stat-label {
        color: var(--text-muted);
        font-size: 1.2rem;
        font-weight: 400;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-family: 'Poppins', sans-serif;
    }
    
    /* Navigation Styling */
    .stSidebar {
        background: var(--panel-dark);
        border-right: 2px solid var(--accent);
    }
    
    .stSidebar .sidebar-content {
        padding: 20px 0;
    }
    
    .stSidebar > div {
        background: var(--panel-dark);
    }
    
    .sidebar-nav {
        padding: 20px;
    }
    
    .nav-row {
        background: transparent;
        border: 1px solid transparent;
        border-radius: 12px;
        padding: 15px 20px;
        margin: 8px 0;
        color: var(--text);
        font-weight: 600;
        font-size: 16px;
        transition: all 0.3s ease;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 15px;
        position: relative;
        overflow: hidden;
    }
    
    .nav-row::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(200, 191, 155, 0.1), transparent);
        transition: left 0.5s ease;
    }
    
    .nav-row:hover::before {
        left: 100%;
    }
    
    .nav-row:hover {
        background: var(--hover);
        border-color: var(--accent);
        color: var(--accent);
        transform: translateX(10px);
        box-shadow: var(--shadow-glow);
    }
    
    .nav-row.active {
        background: var(--accent);
        color: var(--bg);
        font-weight: 700;
        box-shadow: var(--shadow-glow);
    }
    
    .nav-row.active::before {
        display: none;
    }
    
    .nav-label {
        font-weight: 500;
        font-size: 16px;
        color: inherit;
        user-select: none;
        flex: 1;
        font-family: 'Poppins', sans-serif;
    }
    
    .nav-row img {
        width: 23px;
        height: 23px;
        filter: brightness(0) invert(1);
        transition: all 0.3s ease;
    }
    
    .nav-row:hover img {
        filter: brightness(0) invert(1) sepia(1) saturate(5) hue-rotate(45deg);
    }
    
    .nav-row.active img {
        filter: brightness(0) invert(0);
    }
    
    /* Button Styling */
    .stButton > button {
        background: var(--gradient);
        color: var(--bg);
        border: none;
        border-radius: 25px;
        padding: 12px 30px;
        font-weight: 700;
        font-size: 16px;
        font-family: 'Poppins', sans-serif;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: var(--shadow-glow);
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(200, 191, 155, 0.4);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Form Elements */
    .stSelectbox > div > div {
        background: var(--panel-dark);
        border: 2px solid var(--border);
        border-radius: 12px;
        color: var(--text);
    }
    
    .stSelectbox > div > div:hover {
        border-color: var(--accent);
    }
    
    .stTextInput > div > div > input {
        background: var(--panel-dark);
        border: 2px solid var(--border);
        border-radius: 12px;
        color: var(--text);
        font-family: 'Poppins', sans-serif;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--accent);
        box-shadow: var(--shadow-glow);
    }
    
    /* Data Frame Styling */
    .stDataFrame {
        background: var(--panel-dark);
        border: 2px solid var(--border);
        border-radius: 15px;
        overflow: hidden;
    }
    
    /* Alert Styling */
    .stAlert {
        background: var(--panel-dark);
        border: 2px solid var(--accent);
        border-radius: 15px;
        color: var(--text);
    }
    
    /* Badge Styling */
    .badge {
        background: var(--gradient);
        color: var(--bg);
        padding: 5px 12px;
        border-radius: 15px;
        font-weight: 600;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        box-shadow: var(--shadow-glow);
    }
    
    /* Metric Styling */
    .stMetric {
        background: var(--panel-dark);
        border: 2px solid var(--border);
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        margin: 15px 0;
    }
    
    .stMetric > div > div > div {
        color: var(--accent);
        font-family: 'Poppins', sans-serif;
        font-weight: 700;
        font-size: 2rem;
        text-shadow: 0 0 15px rgba(200, 191, 155, 0.3);
    }
    
    .stMetric > div > div > div:last-child {
        color: var(--text-muted);
        font-size: 1rem;
        font-weight: 400;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-family: 'Poppins', sans-serif;
    }
    
    /* Success Message Styling */
    .stSuccess {
        background: rgba(0, 255, 136, 0.1);
        border: 2px solid #00ff88;
        border-radius: 15px;
        color: #00ff88;
        padding: 20px;
        margin: 20px 0;
        text-align: center;
        font-weight: 600;
        animation: fadeInUp 0.8s ease-out;
    }
    
    /* Animations */
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
    
    @keyframes shimmer {
        0% {
            transform: translateX(-100%);
        }
        100% {
            transform: translateX(100%);
        }
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .header-title {
            font-size: 2rem;
            flex-direction: column;
            gap: 10px;
        }
        
        .game-card {
            padding: 20px;
            margin: 15px 0;
        }
        
        .team-logo {
            width: 60px;
            height: 60px;
            font-size: 1rem;
        }
        
        .vs-separator {
            font-size: 1.5rem;
        }
        
        .stat-value {
            font-size: 2.5rem;
        }
    }
    
    /* Gaming-specific enhancements */
    .stButton > button[data-testid="baseButton-secondary"] {
        background: var(--panel-dark) !important;
        color: var(--text) !important;
        border: 2px solid var(--accent) !important;
        border-radius: 25px !important;
        font-weight: 500 !important;
        font-family: 'Poppins', sans-serif !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button[data-testid="baseButton-secondary"]:hover {
        background: var(--accent) !important;
        color: var(--bg) !important;
        transform: translateY(-2px) !important;
        box-shadow: var(--shadow-glow) !important;
    }
    
    /* Enhanced form styling */
    .stTextInput > div > div > input::placeholder {
        color: var(--text-muted) !important;
        opacity: 0.7 !important;
    }
    
    /* Success/Error message enhancements */
    .stSuccess > div {
        background: rgba(0, 255, 136, 0.1) !important;
        border: 2px solid #00ff88 !important;
        border-radius: 15px !important;
        color: #00ff88 !important;
        font-weight: 600 !important;
    }
    
    .stError > div {
        background: rgba(255, 68, 68, 0.1) !important;
        border: 2px solid #ff4444 !important;
        border-radius: 15px !important;
        color: #ff4444 !important;
        font-weight: 600 !important;
    }
    
    /* Loading spinner enhancement */
    .stSpinner > div {
        border: 3px solid var(--panel-dark) !important;
        border-top: 3px solid var(--accent) !important;
        border-radius: 50% !important;
        width: 40px !important;
        height: 40px !important;
        animation: spin 1s linear infinite !important;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Hide Streamlit default elements */
    #MainMenu, footer, header { visibility: hidden; }
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
        "GEN": "#c8bf9b", "GEN.G": "#c8bf9b",
        "FPX": "#d4ccb0", "FNC": "#a89f7e",
        "TL": "#b8af8a", "DRX": "#c8bf9b",
        "PRX": "#d4ccb0", "T1": "#a89f7e",
        "EDG": "#b8af8a", "LOUD": "#c8bf9b",
        "NRG": "#d4ccb0", "SEN": "#a89f7e",
        "100T": "#b8af8a", "LEV": "#c8bf9b",
        "NAVI": "#d4ccb0", "VIT": "#a89f7e",
        "TH": "#b8af8a", "KC": "#c8bf9b"
    }
    # Special handling for TBD/placeholder cases
    if team_name in ["TBD", "TBA", "—"]:
        display_text = "TBD"
        color = "#6b7280"  # Gray for placeholder
    else:
        display_text = (team_name or '')[:3].upper()
        color = colors.get((team_name or "").upper(), "#c8bf9b")
    
    return f"""
    <div style="width:90px;height:90px;background:linear-gradient(145deg, {color}, {colors.get((team_name or "").upper(), '#a89f7e') if team_name not in ["TBD", "TBA", "—"] else '#9ca3af'});border-radius:50%;display:flex;
                align-items:center;justify-content:center;font-size:22px;font-weight:900;color:#0a0a0a;
                margin:0 auto 8px;box-shadow:0 0 20px rgba(200, 191, 155, 0.3);
                border:3px solid #c8bf9b;transition:all 0.3s ease;
                cursor:pointer;position:relative;overflow:hidden;animation:fadeInUp 0.8s ease-out;">
        <div style="position:absolute;top:0;left:-100%;width:100%;height:100%;
                    background:linear-gradient(90deg,transparent,rgba(200, 191, 155, 0.3),transparent);
                    transition:left 0.6s ease;"></div>
        <span style="position:relative;z-index:1;text-shadow:0 0 10px rgba(200, 191, 155, 0.5);font-family: 'Poppins', sans-serif;font-weight:700;">{display_text}</span>
    </div>
    """

def team_logo_html(team_name: str):
    """Try local /logos/<TEAM>.(png|svg|jpg|jpeg|webp) else fallback."""
    t = (team_name or "").strip()
    if not t:
        return get_team_logo_placeholder("—")
    
    # Skip placeholder team names that aren't actual teams
    if any(placeholder in t for placeholder in ["-W", "-L", "TBD", "TBA"]):
        return get_team_logo_placeholder("TBD")
    
    # Team name mapping for logo files
    team_mapping = {
        "PRX": "Paper Rex",
        "TALON": "TALON",
        "RRQ": "RRQ", 
        "BBL": "BBL",
        "Team Liquid": "Team Liquid",
        "GiantX": "GiantX",
        "NAVI": "NAVI",
        "Sentinels": "Sentinels",
        "G2": "G2",
        "NRG": "NRG",
        "Cloud9": "Cloud9"
    }
    
    # Get the mapped team name
    mapped_name = team_mapping.get(t, t)
    
    # Try multiple possible logo directories
    logo_dirs = [
        Path("logos"),
        Path(__file__).parent / "logos",
        Path.cwd() / "logos"
    ]
    
    for logo_dir in logo_dirs:
        if logo_dir.exists():
            # Try exact match first with mapped name
            base = logo_dir / f"{mapped_name}"
            for ext in (".png", ".svg", ".jpg", ".jpeg", ".webp"):
                p = base.with_suffix(ext)
                if p.exists():
                    try:
                        # Use relative path for Streamlit
                        relative_path = p.relative_to(Path.cwd())
                        return f"""
                        <div class="team-logo-container">
                            <img src="{relative_path}" style="max-width:80px;max-height:80px;border-radius:50%;border:3px solid var(--accent);box-shadow: var(--shadow-glow);"/>
                        </div>
                        """
                    except Exception:
                        continue
            
            # Try case-insensitive match as fallback
            for logo_file in logo_dir.iterdir():
                if logo_file.is_file() and logo_file.suffix.lower() in ['.png', '.svg', '.jpg', '.jpeg', '.webp']:
                    logo_name = logo_file.stem
                    if t.lower() in logo_name.lower() or logo_name.lower() in t.lower():
                        try:
                            relative_path = logo_file.relative_to(Path.cwd())
                            return f"""
                            <div class="team-logo-container">
                                <img src="{relative_path}" style="max-width:80px;max-height:80px;border-radius:50%;border:3px solid var(--accent);box-shadow: var(--shadow-glow);"/>
                            </div>
                            """
                        except Exception:
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
    .stApp { background:#0a0a0a; } #MainMenu, footer, header{visibility:hidden;}
    .login-container{ max-width:400px; margin:100px auto; padding:40px; background:#1a1a1a; border-radius:20px; box-shadow:0 0 30px rgba(200, 191, 155, 0.2); border:2px solid #c8bf9b;}
    .app-title{ font-size:28px; font-weight:900; color:#c8bf9b; margin-bottom:8px; font-family: 'Poppins', sans-serif; text-align:center; text-shadow:0 0 15px rgba(200, 191, 155, 0.5);}
    .app-subtitle{ font-size:16px; color:#cccccc; text-align:center; font-weight:500; }
    .form-title{ font-size:22px; font-weight:700; text-align:center; margin-bottom:8px; color:#ffffff; font-family: 'Poppins', sans-serif;}
    .form-subtitle{ font-size:16px; color:#cccccc; text-align:center; margin-bottom:24px; font-weight:400;}
    .divider{ text-align:center; margin:24px 0; color:#c8bf9b; font-size:16px; font-weight:600;}
    .terms-text{ text-align:center; font-size:14px; color:#cccccc; margin-top:24px; line-height:18px;}
    .terms-text a{ color:#c8bf9b; text-decoration:none; font-weight:600;}
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
        st.markdown("<div style='text-align:center;font-size:28px;margin:8px 0;color:#c8bf9b;font-family: Poppins, sans-serif;font-weight:700;text-shadow:0 0 15px rgba(200, 191, 155, 0.5);'>Sign in</div><div style='text-align:center;color:#cccccc;font-size:16px;font-weight:500;'>Continue to VCT Survivor</div>", unsafe_allow_html=True)
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
        <div class="header-title">{icon_html("vct.png", 45)} VCT SURVIVOR</div>
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
                    st.markdown(f"<div class='game-card'><h3 style='color:var(--text);'>{act['stage_name']}</h3></div>", unsafe_allow_html=True)

                    mid, assign_df = get_or_make_assignment(user, act["stage_id"], assign_df, schedule_df)
                    if mid:
                        mrow = schedule_df[schedule_df["match_id"]==mid].iloc[0]
                        st.markdown(f"**Match ID:** `{mid}`")

                        col_team1, col_vs, col_team2 = st.columns([2, 1, 2])
                        with col_team1:
                            st.markdown(team_logo_html(mrow['team_a']), unsafe_allow_html=True)
                            st.markdown(f"<h3 style='text-align:center;color:var(--text);margin:10px 0;font-family: Poppins, sans-serif;font-weight:700;text-shadow:0 0 10px rgba(200, 191, 155, 0.3);'>{mrow['team_a']}</h3>", unsafe_allow_html=True)
                        with col_vs:
                            st.markdown("<div style='text-align:center;padding-top:30px;'><h2 style='color:var(--accent);font-family: Poppins, sans-serif;font-weight:800;text-shadow:0 0 15px rgba(200, 191, 155, 0.5);'>VS</h2></div>", unsafe_allow_html=True)
                        with col_team2:
                            st.markdown(team_logo_html(mrow['team_b']), unsafe_allow_html=True)
                            st.markdown(f"<h3 style='text-align:center;color:var(--text);margin:10px 0;font-family: Orbitron, monospace;font-weight:700;text-shadow:0 0 10px rgba(200, 191, 155, 0.3);'>{mrow['team_b']}</h3>", unsafe_allow_html=True)

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
            
            # Show data table
            st.markdown("## 📊 Schedule Data")
            st.dataframe(df[["stage_id","stage_name","match_id","team_a","team_b","match_time_local","match_time_utc","winner_team"]],
                         use_container_width=True, hide_index=True)
            
            # Show visual schedule with team logos
            st.markdown("## 🎮 Visual Schedule")
            for _, match in df.iterrows():
                col1, col2, col3, col4 = st.columns([1, 2, 1, 2])
                
                with col1:
                    st.markdown(team_logo_html(match['team_a']), unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"<h4 style='text-align:center;color:var(--text);margin:10px 0;font-family: Orbitron, monospace;font-weight:700;'>{match['team_a']}</h4>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align:center;color:var(--text-muted);margin:5px 0;'>Stage {match['stage_id']}</p>", unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"<div style='text-align:center;padding-top:20px;'><h3 style='color:var(--accent);font-family: Poppins, sans-serif;font-weight:800;'>VS</h3></div>", unsafe_allow_html=True)
                
                with col4:
                    st.markdown(team_logo_html(match['team_b']), unsafe_allow_html=True)
                
                st.markdown(f"<h4 style='text-align:center;color:var(--text);margin:10px 0;font-family: Orbitron, monospace;font-weight:700;'>{match['team_b']}</h4>", unsafe_allow_html=True)
                
                # Match time and status
                st.markdown(f"""
                <div class="match-info">
                    <div class="match-time">⏰ {match['match_time_local']}</div>
                    <div class="match-status">Match ID: {match['match_id']}</div>
                    {f'<div style="color:var(--accent);font-weight:600;margin-top:10px;">🏆 Winner: {match["winner_team"]}</div>' if match['winner_team'] else ''}
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("---")
    
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
