import streamlit as st
import uuid
from pathlib import Path

from config import STOCKS, TOTAL_ROUNDS
from db import get_game_state, get_teams, get_sessions, get_spreads, get_true_prices, get_positions, get_team_for_session
from utils import spread_signature, team_cash_signature
from views import (
    render_login, render_sidebar, render_header,
    render_admin, render_submit, render_trade, render_reveal,
)
from views.leaderboard import render_leaderboard, render_game_over

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Market Making Hackathon",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded",
)

# ── Load CSS ───────────────────────────────────────────────────────────────────
_css = (Path(__file__).parent / "styles.css").read_text()
st.markdown(f"<style>{_css}</style>", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    # Keep a stable browser identity across full page reloads.
    sid_from_url = st.query_params.get("sid")
    if sid_from_url:
        st.session_state["session_id"] = sid_from_url
    else:
        st.session_state["session_id"] = str(uuid.uuid4())
        st.query_params["sid"] = st.session_state["session_id"]
else:
    # Ensure the URL keeps tracking the current session identity.
    if st.query_params.get("sid") != st.session_state["session_id"]:
        st.query_params["sid"] = st.session_state["session_id"]

if "claimed_team" not in st.session_state: st.session_state["claimed_team"] = None
if "is_admin"     not in st.session_state: st.session_state["is_admin"]     = False
SESSION_ID = st.session_state["session_id"]

# ── Load current game state ────────────────────────────────────────────────────
gs           = get_game_state()
round_num    = gs["round"]
phase        = gs["phase"]
market_maker = gs["market_maker"]
game_over    = gs["game_over"]
stock        = STOCKS[round_num - 1]
teams        = get_teams()
sessions     = get_sessions()
spreads      = get_spreads(round_num)
true_prices  = get_true_prices()
positions    = get_positions()
team_state   = team_cash_signature(teams)
spread_state = spread_signature(spreads)

my_team  = st.session_state["claimed_team"]
is_admin = st.session_state["is_admin"]

# Re-associate session if browser refreshed
if not is_admin and my_team is None:
    hinted_team = st.query_params.get("team")
    if hinted_team and sessions.get(hinted_team) == SESSION_ID:
        my_team = hinted_team
        st.session_state["claimed_team"] = hinted_team
    else:
        matched_team = get_team_for_session(SESSION_ID)
        if matched_team:
            my_team = matched_team
            st.session_state["claimed_team"] = matched_team
            st.query_params["team"] = matched_team

# ── Login gate ─────────────────────────────────────────────────────────────────
if not is_admin and my_team is None:
    render_login(teams, sessions, SESSION_ID)
    st.stop()

# ── Sidebar + Header ──────────────────────────────────────────────────────────
render_sidebar(is_admin, my_team, teams, positions, round_num, stock, phase)
render_header(is_admin, my_team, round_num, stock, phase)

# ── Game over ──────────────────────────────────────────────────────────────────
if game_over:
    render_game_over(teams, is_admin)
    st.stop()

# ── Progress bar ───────────────────────────────────────────────────────────────
st.progress((round_num - 1) / TOTAL_ROUNDS)

# ── Hero: Stock & Round (teams only) ──────────────────────────────────────────
if not is_admin:
    _phase_hints = {
        "submit": "Set your bid &amp; ask prices. The tightest spread becomes market maker.",
        "trade":  "Buy or sell shares from the market maker at their quoted prices.",
        "reveal": "The true price is revealed — all positions are settled to cash.",
    }
    _pc = {"submit": "#22d3ee", "trade": "#fbbf24", "reveal": "#34d399"}.get(phase, "#fbbf24")
    _stock_display = stock.upper().replace("_", " ")
    _hero = (
        f"<p style='text-align:center;font-size:.9rem;letter-spacing:.35em;color:#64748b;"
        f"text-transform:uppercase;font-weight:600;margin-bottom:.3rem;padding-top:1.5rem;'>"
        f"Round {round_num} of {TOTAL_ROUNDS}</p>"
        f"<p style='text-align:center;font-size:3.8rem;font-weight:900;letter-spacing:-.04em;"
        f"background:linear-gradient(135deg,#22d3ee,#a78bfa);-webkit-background-clip:text;"
        f"-webkit-text-fill-color:transparent;line-height:1.1;margin:0 0 .5rem;'>"
        f"{_stock_display}</p>"
        f"<p style='text-align:center;margin:0 0 .6rem;'>"
        f"<span style='display:inline-block;padding:.35rem 1rem;border-radius:8px;"
        f"background:{_pc}18;border:1px solid {_pc}30;"
        f"font-size:.8rem;font-weight:700;color:{_pc};letter-spacing:.18em;"
        f"text-transform:uppercase;'>{phase.upper()} PHASE</span></p>"
        f"<p style='text-align:center;color:#94a3b8;font-size:1.05rem;max-width:520px;"
        f"margin:.2rem auto 1.2rem;line-height:1.5;'>{_phase_hints.get(phase,'')}</p>"
    )
    st.markdown(_hero, unsafe_allow_html=True)

# ── Admin panel ────────────────────────────────────────────────────────────────
if is_admin:
    render_admin(round_num, stock, phase, spreads, teams, market_maker, true_prices)

# ── Phase views ────────────────────────────────────────────────────────────────
if phase == "submit":
    render_submit(is_admin, my_team, round_num, stock, teams, spreads)
elif phase == "trade":
    render_trade(is_admin, my_team, market_maker, round_num, stock, teams, spreads)
elif phase == "reveal":
    render_reveal(my_team, market_maker, round_num, stock, spreads, true_prices)

# ── Leaderboard ────────────────────────────────────────────────────────────────
render_leaderboard(my_team, market_maker, teams, round_num, phase, game_over, is_admin)

# ── Auto-refresh: polls for any game-state change and reruns automatically ─────
if not game_over:
    @st.fragment(run_every=8)
    def _auto_refresh():
        latest_gs = get_game_state()
        latest_spreads = get_spreads(latest_gs["round"])
        latest_teams = get_teams()
        # Detect any meaningful change
        changed = (
            latest_gs["phase"] != phase
            or latest_gs["round"] != round_num
            or latest_gs["game_over"] != game_over
            or latest_gs["market_maker"] != market_maker
            or spread_signature(latest_spreads) != spread_state
            or team_cash_signature(latest_teams) != team_state
        )
        if changed:
            st.rerun(scope="app")
    _auto_refresh()
