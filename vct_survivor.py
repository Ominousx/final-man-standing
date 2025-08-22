
import os
import hashlib
import random
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

# ---------------- Config ----------------
DATA_DIR = Path("data")
SCHEDULE_CSV = DATA_DIR / "schedule.csv"       # stage_id,stage_name,match_id,team_a,team_b,match_time_iso,winner_team
PICKS_CSV = DATA_DIR / "picks.csv"             # user,stage_id,match_id,pick_team,pick_time_iso
ASSIGN_CSV = DATA_DIR / "assignments.csv"      # user,stage_id,match_id,assigned_time_iso
ADMIN_KEY_ENV = "VLMS_ADMIN_KEY"               # optional: set to enable admin upload
LOCK_MINUTES_BEFORE = 5                        # lock picks X min before match start
UI_TZ_LABEL = "Asia/Kolkata"                   # display-only label

st.set_page_config(page_title="VCT Random-Fixture Survivor", page_icon="🎯", layout="centered")

# ---------------- Utilities ----------------
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

def user_alive(results_df: pd.DataFrame, user: str):
    if results_df.empty: return True
    me = results_df[results_df["user"]==user]
    return not any(me["result"] == "Loss")

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

# ---------------- App ----------------
ensure_files()
schedule_df = load_schedule()
picks_df = load_picks()
assign_df = load_assignments()
results_df = judge_results(schedule_df, picks_df)
lb_df = compute_leaderboard(results_df)

st.title("🎯 VCT Random-Fixture Survivor")

user = st.text_input("Enter username:", value="", placeholder="e.g., sushant")
if not user:
    st.info("Enter a username to get your assignment and make a pick.")
    st.stop()

alive = user_alive(results_df, user)
if not alive:
    st.error("You’ve been eliminated. You can still view tables below.")
else:
    st.success(f"Good luck, {user}! (Times shown as **{UI_TZ_LABEL}** label; locks enforced in UTC.)")

st.markdown("---")

# Active stage
act = active_stage(schedule_df)
if not act:
    st.subheader("No active stage")
    st.info("Either the tournament hasn’t started, all matches in the current stage have locked/finished, or schedule is empty.")
else:
    st.subheader(f"Active Stage: **{act['stage_name']}**")
    # only assign if user is alive
    if alive:
        mid, assign_df = get_or_make_assignment(user, act["stage_id"], assign_df, schedule_df)
        if mid is None:
            st.warning("No eligible matches available to assign right now.")
        else:
            # show assignment
            mrow = schedule_df[schedule_df["match_id"]==mid].iloc[0]
            st.markdown(f"**Your match:** `{mid}` — **{mrow['team_a']} vs {mrow['team_b']}**")
            st.caption(f"Match time (UTC): {mrow['match_time_iso']}  •  Pick locks {LOCK_MINUTES_BEFORE} min before start")

            # pick UI
            # if already picked this stage, show it
            existing = picks_df[(picks_df["user"]==user) & (picks_df["stage_id"]==act["stage_id"])]

            if not existing.empty:
                st.info(f"You already picked: **{existing.iloc[0]['pick_team']}**")
            else:
                if not can_pick(schedule_df, mid):
                    st.error("Picks are locked for this match.")
                else:
                    with st.form("pick_form", clear_on_submit=True):
                        pick = st.selectbox("Who wins your assigned match?", options=[mrow["team_a"], mrow["team_b"]])
                        submit = st.form_submit_button("Lock Pick ✅")
                        if submit:
                            if not can_pick(schedule_df, mid):
                                st.error("Picks are locked.")
                            else:
                                picks_df, ok, msg = record_pick(picks_df, user, act["stage_id"], mid, pick)
                                if ok:
                                    save_picks(picks_df)
                                    st.success(msg)
                                else:
                                    st.error(msg)
        save_assign(assign_df)

# My picks & results
st.markdown("---")
st.subheader("My Picks")
mine = picks_df[picks_df["user"]==user].sort_values(["stage_id"])
st.table(mine.reset_index(drop=True))

my_results = judge_results(schedule_df, picks_df)
my_results = my_results[my_results["user"]==user].sort_values(["stage_id"])
if not my_results.empty:
    st.markdown("**My Results**")
    st.table(my_results.reset_index(drop=True))

# Leaderboard
st.markdown("---")
st.subheader("Leaderboard")
st.table(lb_df.reset_index(drop=True))

# Admin (optional)
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
