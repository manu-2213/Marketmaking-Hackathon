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

# ── Hero: Stock & Round (teams only) ──────────────────────────────────────────
if not is_admin:
    _phase_hints = {
        "submit": "Set your bid &amp; ask prices. The tightest spread becomes market maker.",
        "trade":  "Buy or sell shares from the market maker at their quoted prices.",
        "reveal": "The true price is revealed — all positions are settled to cash.",
    }
    _pc = {"submit": "#22d3ee", "trade": "#fbbf24", "reveal": "#34d399"}.get(phase, "#fbbf24")
    st.markdown(f"""
    <div class='animate-in' style='text-align:center;padding:2.2rem 1rem 1.6rem;margin-bottom:1.5rem;'>
        <div style='font-size:.9rem;letter-spacing:.35em;color:#64748b;text-transform:uppercase;
                    font-weight:600;margin-bottom:.5rem;'>Round {round_num} of {TOTAL_ROUNDS}</div>
        <div style='font-size:3.8rem;font-weight:900;letter-spacing:-.04em;
                    background:linear-gradient(135deg,#22d3ee,#a78bfa);-webkit-background-clip:text;
                    -webkit-text-fill-color:transparent;line-height:1.1;margin-bottom:.7rem;
                    '>{stock.upper().replace("_"," ")}</div>
        <div style='display:inline-block;padding:.35rem 1rem;border-radius:8px;
                    background:{_pc}18;border:1px solid {_pc}30;
                    font-size:.8rem;font-weight:700;color:{_pc};letter-spacing:.18em;
                    text-transform:uppercase;margin-bottom:.9rem;'>{phase.upper()} PHASE</div>
        <div style='color:#94a3b8;font-size:1.05rem;max-width:520px;margin:.2rem auto 0;
                    line-height:1.5;'>{_phase_hints.get(phase,"")}</div>
    </div>
    """, unsafe_allow_html=True)

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
            or len(latest_spreads) != len(spreads)
            or len(latest_teams) != len(teams)
        )
        if changed:
            st.rerun(scope="app")
    _auto_refresh()
