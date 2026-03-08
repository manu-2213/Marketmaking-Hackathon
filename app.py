import streamlit as st
import uuid
from pathlib import Path

from config import STOCKS, TOTAL_ROUNDS
from db import get_game_state, get_teams, get_sessions, get_spreads, get_true_prices, get_positions
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
if "session_id"   not in st.session_state: st.session_state["session_id"]   = str(uuid.uuid4())
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

my_team  = st.session_state["claimed_team"]
is_admin = st.session_state["is_admin"]

# Re-associate session if browser refreshed
if not is_admin and my_team is None:
    for team, sid in sessions.items():
        if sid == SESSION_ID:
            my_team = team
            st.session_state["claimed_team"] = team
            break

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
st.markdown("<br>", unsafe_allow_html=True)

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

# ── Live state-change watcher (non-admin players only) ─────────────────────────
if phase in ("submit", "trade") and not game_over and not is_admin:
    @st.fragment(run_every=10)
    def _state_watcher():
        """Polls for phase/round changes and shows a refresh prompt."""
        latest = get_game_state()
        if latest["phase"] != phase or latest["round"] != round_num or latest["game_over"]:
            st.warning("⚡ The game has moved on!")
            if st.button("🔄 Refresh Page", type="primary", key="_sw_refresh"):
                st.rerun(scope="app")
        else:
            st.caption("")  # keep fragment container alive
    _state_watcher()
