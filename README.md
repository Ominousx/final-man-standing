# VCT Random‑Fixture Survivor (Final Man Standing)

A lightweight **Last-Man-Standing** style game tailored for **VCT Champions** formats with groups and double-elimination playoffs.

**How it works**  
- The tournament is divided into **stages** (Group Openers → Winners/Elims → Deciders → Playoffs → Final).  
- When a stage opens, each player is assigned **one random match** from that stage.  
- They pick the **winner of that match only**.  
- **Wrong pick = out.** Correct = advance.  
- No “unique team across the event” rule.

## Quickstart (local)

```bash
# clone or copy this folder locally
cd final-man-standing

# (optional) create a virtual env
python3 -m venv .venv && source .venv/bin/activate

# install deps
pip install -r requirements.txt

# run the app
streamlit run vct_survivor.py
```

The app will use `data/schedule.csv`. This repo ships with a **future-dated random schedule** so you can dry-run immediately.

## Admin (optional)

Set an environment variable before launching to enable the in-app Admin panel:

```bash
export VLMS_ADMIN_KEY="secret123"
streamlit run vct_survivor.py
```

Inside **Admin** you can upload a new `data/schedule.csv` or download the current one.  
Update `winner_team` (must equal `team_a` or `team_b`) as matches finish; the app computes results and the leaderboard.

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub (see below).  
2. In Streamlit Cloud, “**New app**” → select repo → pick `vct_survivor.py` as the **entrypoint**.  
3. (Optional) Add `VLMS_ADMIN_KEY` as an environment variable in the app settings.  
4. Deploy.

## Project structure

```
final-man-standing/
├─ data/
│  └─ schedule.csv           # tournament schedule + winners (to be filled)
├─ vct_survivor.py           # Streamlit app
├─ requirements.txt
├─ .gitignore
├─ LICENSE
└─ README.md
```

## Notes
- Times in `schedule.csv` are **UTC**. Picks lock **5 minutes** before each match start.
- The match assignment is **deterministic** per `(user, stage_id)` so refreshing won’t change your draw.
- You can rename stages or add/remove stages—just keep `stage_id` ascending.

---

✍️ **Credits**  
Built by **@Ominousx** 🎮  
For feedback, open an issue or ping on X/Twitter: **_SushantJha**
