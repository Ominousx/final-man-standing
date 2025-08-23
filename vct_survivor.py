# vct_survivor.py
import os
import hashlib
import random
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

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
        --accent: #7C3AED;   /* purple */
        --accent2: #06B6D4;  /* cyan */
        --ok: #22c55e;
        --warn: #f59e0b;
        --bad: #ef4444;
    }
    .stApp {
        background:
            radial-gradient(1200px 600px at 20% -10%, rgba(124,58,237,.15), transparent),
            radial-gradient(1200px 600px at 110% 10%, rgba(6,182,212,.12), transparent),
            var(--bg);
        color: var(--text);
        font-family: 'Inter', sans-serif;
    }
    h1, h2, h3, .bigtitle {
        font-family: 'Bebas Neue', sans-serif !important;
        letter-spacing: .5px;
        margin-bottom: .25rem;
    }
    .subtle { color: var(--muted); font-size: 13px; }
    .card {
        border: 1px solid rgba(255,255,255,.08);
        background: linear-gradient(180deg, rgba(255,255,255,.02), rgba(255,255,255,.01));
        border-radius: 20px; padding: 18px 20px;
        box-shadow: 0 8px 24px rgba(0,0,0,.25);
        animation: fadeIn .6s ease both;
    }
    .hero {
        border-radius: 18px; padding: 16px 20px; margin-bottom: 8px;
        background: linear-gradient(120deg, rgba(124,58,237,.18), rgba(6,182,212,.14));
        border: 1px solid rgba(255,255,255,.10);
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(6px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .badge {
        display:inline-block; padding: 6px 10px; border-radius: 999px; font-size: 12px;
        font-weight: 700; letter-spacing:.2px; border:1px solid rgba(255,255,255,.12)
    }
    .alive  { background: rgba(34,197,94,.12);  color:#86efac; }
    .dead   { background: rgba(239,68,68,.12);  color:#fca5a5; }
    .waiting{ background: rgba(245,158,11,.12); color:#fcd34d; }
    div.stButton > button {
        background: linear-gradient(90deg, var(--accent), var(--accent2));
        color: white; border:0; padding: 10px 16px; border-radius: 12px; font-weight: 800;
        box-shadow: 0 6px 18px rgba(124,58,237,.35);
        transition: transform .08s ease, box-shadow .2s ease;
    }
    div.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 8px 22px rgba(124,58,237,.45); }
    div.stButton > button:active { transform: translateY(0); }
    /* tighten table fonts */
    .dataframe tbody td, .dataframe thead th { font-size: 13px; }
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
    """Reproducible choice so refresh spam can’t farm matchups."""
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
    """Assign one random eligible match to the user for this stage (no rerolls).
       If the assigned match becomes ineligible (started/resolved), assign a new one deterministically."""
    cur = assignments_df[(assignments_df["user"]==user) & (assignments_df["stage_id"]==stage_id)]
    pool = eligible_matches(schedule_df, stage_id)
    if pool.empty:
        return None, assignments_df

    if not cur.empty:
        mid = cur.iloc[0]["match_id"]
        still_ok = pool[pool["match_id"]==mid]
        if not still_ok.empty:
            return mid, assignments_df
        # fallback to a new deterministic choice if original died
        new_mid = deterministic_choice(pool["match_id"], user, stage_id, salt="fallback")
        assignments_df.loc[cur.index, ["match_id","assigned_time_iso"]] = [new_mid, now_utc().isoformat()]
        return new_mid, assignments_df

    # first assignment
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
    # prevent multiple picks for same stage
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


# ============================== App ==============================
inject_premium_css()
ensure_files()

schedule_df = load_schedule()
picks_df = load_picks()
assign_df = load_assignments()
results_df = judge_results(schedule_df, picks_df)
lb_df = compute_leaderboard(results_df)

# Header
st.markdown('<div class="hero"><h1>VCT Random-Fixture Survivor</h1><div class="subtle">Pick a match. Pick a winner. Survive.</div></div>', unsafe_allow_html=True)

# Username + Alive badge
c1, c2 = st.columns([1,2])
with c1:
    user = st.text_input("Username", value="", placeholder="e.g., sushant")
with c2:
    alive_badge = ""
    if user:
        is_alive = True
        me = results_df[results_df["user"]==user]
        if not me.empty and any(me["result"]=="Loss"):
            is_alive = False
        alive_badge = badge("ALIVE", "alive") if is_alive else badge("ELIMINATED", "dead")
    st.markdown(f"<div style='text-align:right;margin-top:6px'>{alive_badge}</div>", unsafe_allow_html=True)

if not user:
    st.info("Enter a username to get your assignment and make a pick.")
else:
    # Main two-column layout
    left, right = st.columns([1.3, 1])

    # -------- Left: Active Stage + Assignment --------
    with left:
        st.markdown("### Current Stage")
        act = active_stage(schedule_df)
        if not act:
            st.markdown('<div class="card">No active stage. Upload a schedule or wait for the next stage.</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div class="card"><div style="display:flex;justify-content:space-between;align-items:center;"><div><strong>{act["stage_name"]}</strong></div><div class="subtle">Stage ID: {act["stage_id"]}</div></div>',
                unsafe_allow_html=True
            )
            mid, assign_df = get_or_make_assignment(user, act["stage_id"], assign_df, schedule_df)
            if mid is None:
                st.markdown('<div class="subtle" style="margin-top:8px">No eligible matches to assign right now.</div>', unsafe_allow_html=True)
            else:
                mrow = schedule_df[schedule_df["match_id"]==mid].iloc[0]
                # Assignment details
                colA, colB = st.columns(2)
                with colA:
                    st.markdown(f"**Your match:** `{mid}`")
                    st.markdown(f"**{mrow['team_a']}** vs **{mrow['team_b']}**")
                with colB:
                    dd = countdown_to(mrow['match_time_iso'])
                    st.markdown(f"⏳ **Locks**: {LOCK_MINUTES_BEFORE}m before start")
                    st.caption(f"Match (UTC): {mrow['match_time_iso']} • Starts in: {dd}")

                # Pick UI
                existing = picks_df[(picks_df["user"]==user) & (picks_df["stage_id"]==act["stage_id"])]
                if not existing.empty:
                    st.success(f"You already picked: **{existing.iloc[0]['pick_team']}**")
                else:
                    if not can_pick(schedule_df, mid):
                        st.error("Picks are locked for this match.")
                    else:
                        with st.form("pick_form", clear_on_submit=True):
                            pick = st.selectbox("Who wins your assigned match?", options=[mrow["team_a"], mrow["team_b"]])
                            submitted = st.form_submit_button("Lock Pick ✅")
                            if submitted:
                                if not can_pick(schedule_df, mid):
                                    st.error("Picks are locked.")
                                else:
                                    picks_df, ok, msg = record_pick(picks_df, user, act["stage_id"], mid, pick)
                                    if ok:
                                        save_picks(picks_df)
                                        st.success(msg)
                                        st.balloons()
                                    else:
                                        st.error(msg)
            st.markdown("</div>", unsafe_allow_html=True)
            save_assign(assign_df)

    # -------- Right: My Summary + Quick Leaderboard --------
    with right:
        st.markdown("### My Summary")
        me_res = results_df[results_df["user"]==user]
        wins = int((me_res["result"]=="Win").sum()) if not me_res.empty else 0
        losses = int((me_res["result"]=="Loss").sum()) if not me_res.empty else 0
        waiting = int((me_res["result"]=="Waiting").sum()) if not me_res.empty else 0
        st.markdown(
            f'<div class="card"><div>Wins: <strong>{wins}</strong></div>'
            f'<div>Waiting: <strong>{waiting}</strong></div>'
            f'<div>Losses: <strong style="color:#fca5a5">{losses}</strong></div></div>',
            unsafe_allow_html=True
        )

        st.markdown("### Quick Leaderboard")
        if lb_df.empty:
            st.caption("No picks recorded yet.")
        else:
            st.dataframe(lb_df.head(8), use_container_width=True, hide_index=True)

    # -------- Tabs --------
    st.markdown("---")
    t1, t2, t3 = st.tabs(["📒 My Picks", "🏆 Leaderboard", "🗓️ Schedule"])

    with t1:
        mine = picks_df[picks_df["user"]==user].sort_values(["stage_id"])
        if mine.empty:
            st.caption("No picks yet.")
        else:
            st.dataframe(mine, use_container_width=True, hide_index=True)
        my_results = judge_results(schedule_df, picks_df)
        my_results = my_results[my_results["user"]==user].sort_values(["stage_id"])
        if not my_results.empty:
            st.markdown("**My Results**")
            st.dataframe(my_results, use_container_width=True, hide_index=True)

    with t2:
        if lb_df.empty:
            st.caption("No data to show yet.")
        else:
            st.dataframe(lb_df, use_container_width=True, hide_index=True)

    with t3:
        if schedule_df.empty:
            st.caption("No schedule uploaded.")
        else:
            st.dataframe(schedule_df, use_container_width=True, hide_index=True)

# -------- Admin (optional) --------
with st.expander("Admin"):
    st.caption("Upload/maintain schedule; set env var VLMS_ADMIN_KEY to enable writes.")
    entered = st.text_input("Admin key:", type="password")
    if entered and os.environ.get(ADMIN_KEY_ENV) and entered == os.environ[ADMIN_KEY_ENV]:
        st.success("Admin mode enabled.")
        st.download_button("Download schedule.csv", data=load_schedule().to_csv(index=False), file_name="schedule.csv")
        up = st.file_uploader("Upload updated schedule.csv", type=["csv"])
        if up:
            new_sched = pd.read_csv(up, dtype=str).fillna("")
            needed = {"stage_id","stage_name","match_id","team_a","team_b","match_time_iso","winner_team"}
            missing = needed - set(new_sched.columns)
            if missing:
                st.error(f"Missing columns: {sorted(list(missing))}")
            else:
                new_sched.to_csv(SCHEDULE_CSV, index=False)
                st.success("Schedule updated. Refresh the page.")
        st.caption("Fill `winner_team` after each match finishes (must equal `team_a` or `team_b`).")
        st.dataframe(load_schedule(), use_container_width=True)
    else:
        st.info("Enter a valid admin key to manage the schedule.")
