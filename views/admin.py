import streamlit as st
import pandas as pd

from config import STOCKS, TOTAL_ROUNDS
from db import (
    get_teams, get_sessions, add_team, delete_all_teams, release_team,
    get_trade_log, set_game_state, set_true_price, settle_round, log_round, reset_game,
)
from game import find_market_maker


def render_admin(round_num, stock, phase, spreads, teams, market_maker, true_prices):
    st.markdown("""<div style='background:linear-gradient(135deg,rgba(167,139,250,.06),rgba(34,211,238,.03));
        border:1px solid rgba(167,139,250,.15);border-radius:16px;padding:1.1rem 1.5rem .6rem;margin-bottom:1.5rem;
        position:relative;overflow:hidden;'>
        <div style='position:absolute;top:0;left:0;right:0;height:2px;
                    background:linear-gradient(90deg,#a78bfa,#22d3ee);'></div>
        <div style='font-size:.6rem;letter-spacing:.25em;color:#a78bfa;text-transform:uppercase;
                    font-weight:700;margin-bottom:.5rem;'>🔧 Admin Control Panel</div>
    </div>""", unsafe_allow_html=True)

    tab_teams, tab_phase, tab_danger = st.tabs(["👥 Teams", "⚙️ Phase Controls", "⚠️ Reset"])

    with tab_teams:
        _render_teams_tab()

    with tab_phase:
        _render_phase_tab(round_num, stock, phase, spreads, teams, market_maker, true_prices)

    with tab_danger:
        _render_danger_tab()

    st.markdown("---")


# ── Teams tab ──────────────────────────────────────────────────────────────────

@st.fragment
def _render_teams_tab():
    _teams = get_teams()
    _sessions = get_sessions()
    c1, c2 = st.columns([1, 2])

    with c1:
        with st.form("add_team_form", clear_on_submit=True):
            new_team = st.text_input("", placeholder="Team name…", label_visibility="collapsed")
            submitted = st.form_submit_button("➕ Add Team", type="primary", use_container_width=True)
            if submitted:
                if new_team.strip():
                    if new_team.strip() not in _teams:
                        add_team(new_team.strip())
                        st.toast(f"✅ Added {new_team.strip()}")
                    else:
                        st.warning("Already exists")
                else:
                    st.warning("Enter a name")

    with c2:
        if _teams:
            rows = [{"Team": t, "Status": "🟢 Online" if t in _sessions else "⚪ Not joined",
                      "Cash": f"${_teams[t]['cash']:,.0f}"} for t in sorted(_teams.keys())]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("No teams yet.")

    if _sessions:
        st.markdown("**Release a slot:**")
        rc1, rc2 = st.columns([2, 1])
        with rc1:
            to_rel = st.selectbox("", sorted(_sessions.keys()), label_visibility="collapsed")
        with rc2:
            if st.button("🔓 Release", use_container_width=True):
                release_team(to_rel)
                st.rerun()

    if _teams:
        st.markdown("---")
        if st.button("🗑 Remove All Teams", use_container_width=True):
            delete_all_teams()
            st.rerun()


# ── Phase tab ──────────────────────────────────────────────────────────────────

def _render_phase_tab(round_num, stock, phase, spreads, teams, market_maker, true_prices):
    st.markdown(f"""<div style='background:linear-gradient(135deg,#111827,#1a2332);border:1px solid #2a3a50;border-radius:14px;
        padding:1rem 1.2rem;margin-bottom:1rem;font-family:JetBrains Mono,monospace;font-size:.78rem;
        position:relative;overflow:hidden;'>
        <div style='position:absolute;top:0;left:0;right:0;height:2px;
                    background:linear-gradient(90deg,#a78bfa,#22d3ee);opacity:.5;'></div>
        <div style='display:flex;gap:1.5rem;flex-wrap:wrap;align-items:center;margin-top:.3rem;'>
            <div><span style='color:#64748b;font-size:.65rem;font-weight:600;'>ROUND</span>
                <span style='color:#22d3ee;font-weight:700;margin-left:.4rem;'>{round_num}</span></div>
            <div><span style='color:#64748b;font-size:.65rem;font-weight:600;'>STOCK</span>
                <span style='color:#a78bfa;font-weight:700;margin-left:.4rem;'>{stock.upper()}</span></div>
            <div><span style='color:#64748b;font-size:.65rem;font-weight:600;'>PHASE</span>
                <span style='color:#fbbf24;font-weight:700;margin-left:.4rem;'>{phase.upper()}</span></div>
            <div><span style='color:#64748b;font-size:.65rem;font-weight:600;'>SPREADS</span>
                <span style='color:#f1f5f9;font-weight:700;margin-left:.4rem;'>{len(spreads)} / {len(teams)}</span></div>
        </div>
    </div>""", unsafe_allow_html=True)

    if phase == "submit":
        if spreads:
            rows = [{"Team": t, "Bid": f"${s['bid']:.2f}", "Ask": f"${s['ask']:.2f}",
                      "Spread": f"${s['ask']-s['bid']:.2f}"} for t, s in spreads.items()]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("Waiting for teams to submit spreads.")
        if st.button("⏩ Close Submissions & Open Trading", type="primary", use_container_width=True):
            mm = find_market_maker(spreads)
            if mm:
                set_game_state(market_maker=mm, phase="trade")
                st.rerun()
            else:
                st.error("No spreads submitted yet.")

    elif phase == "trade":
        round_trades = get_trade_log(round_num)
        real_trades = [t for t in round_trades if t.get("qty", 0) > 0]
        st.success(f"Market Maker: **{market_maker}**")
        st.markdown(f"Trades executed: **{len(real_trades)}**")
        if real_trades:
            df_t = pd.DataFrame(real_trades)[["buyer", "seller", "price", "qty", "executed_at"]]
            df_t.columns = ["Buyer", "Seller", "Price", "Qty", "Time"]
            df_t["Price"] = df_t["Price"].apply(lambda v: f"${v:.2f}")
            df_t["Time"] = df_t["Time"].apply(lambda v: str(v)[-15:-7] if v else "")
            st.dataframe(df_t, use_container_width=True, hide_index=True)
        st.markdown("---")
        true_p = st.number_input("True price ($)", min_value=0.0, value=100.0, step=0.01)
        if st.button("✅ Reveal True Price & Settle All Positions", type="primary", use_container_width=True):
            set_true_price(stock, true_p)
            settle_round(round_num, stock, true_p)
            set_game_state(phase="reveal")
            st.rerun()

    elif phase == "reveal":
        tp = true_prices.get(stock)
        st.success(f"True price: **${tp:.2f}**" if tp else "True price set.")
        st.info("All positions settled to cash at the true price.")
        st.markdown("---")
        if round_num < TOTAL_ROUNDS:
            if st.button(f"▶ Start Round {round_num+1} — {STOCKS[round_num].upper()}", type="primary", use_container_width=True):
                log_round(round_num, stock, market_maker, true_prices.get(stock))
                set_game_state(round=round_num + 1, phase="submit", market_maker=None)
                st.rerun()
        else:
            if st.button("🏁 End Game & Show Final Results", type="primary", use_container_width=True):
                log_round(round_num, stock, market_maker, true_prices.get(stock))
                set_game_state(game_over=True)
                st.rerun()


# ── Danger tab ─────────────────────────────────────────────────────────────────

def _render_danger_tab():
    st.warning("This will delete all teams, spreads, trades and reset to round 1.")
    confirm = st.text_input("Type RESET to confirm")
    if st.button("🔄 Reset Entire Game", use_container_width=True):
        if confirm == "RESET":
            reset_game()
            st.rerun()
        else:
            st.error("Type RESET to confirm")
