import streamlit as st
import html as _html

from config import STARTING_BUDGET, TOTAL_ROUNDS
from db import release_team


def _esc(s):
    return _html.escape(str(s)) if s else ""


def render_sidebar(is_admin, my_team, teams, positions, round_num, stock, phase):
    with st.sidebar:
        if is_admin:
            st.markdown("""<div style='padding:.75rem 0 .5rem'>
                <div style='font-size:.6rem;letter-spacing:.25em;color:#22d3ee;text-transform:uppercase;font-weight:600;'>Role</div>
                <div style='font-size:1.3rem;font-weight:800;color:#f1f5f9;margin-top:.2rem;'>🔧 Admin</div>
            </div>""", unsafe_allow_html=True)
            if st.button("🚪 Sign out", use_container_width=True):
                st.session_state["is_admin"] = False
                st.rerun()
        else:
            st.markdown(f"""<div style='padding:1rem 0 .6rem'>
                <div style='font-size:.75rem;letter-spacing:.25em;color:#22d3ee;text-transform:uppercase;font-weight:600;'>Playing as</div>
                <div style='font-size:1.7rem;font-weight:800;color:#f1f5f9;margin-top:.3rem;'>{_esc(my_team)}</div>
            </div>""", unsafe_allow_html=True)

            if teams and my_team in teams:
                cash = teams[my_team]["cash"]
                pnl = cash - STARTING_BUDGET
                pnl_color = "#34d399" if pnl >= 0 else "#fb7185"
                st.markdown(f"""<div style='background:linear-gradient(135deg,#111827,#1a2332);
                    border:1px solid #2a3a50;border-radius:14px;
                    padding:1.2rem 1.3rem;margin:.8rem 0;'>
                    <div style='display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:.6rem;'>
                        <div>
                            <div style='font-size:.7rem;color:#64748b;text-transform:uppercase;letter-spacing:.12em;font-weight:600;'>Cash</div>
                            <div style='font-family:JetBrains Mono,monospace;font-size:1.5rem;font-weight:700;
                                        color:{"#34d399" if cash>=0 else "#fb7185"};margin-top:.2rem;'>${cash:,.0f}</div>
                        </div>
                        <div style='text-align:right;'>
                            <div style='font-size:.7rem;color:#64748b;text-transform:uppercase;letter-spacing:.12em;font-weight:600;'>P&L</div>
                            <div style='font-family:JetBrains Mono,monospace;font-size:1.1rem;font-weight:600;
                                        color:{pnl_color};margin-top:.2rem;'>${pnl:+,.0f}</div>
                        </div>
                    </div>
                    <div style='height:3px;border-radius:2px;background:#1f2b3d;overflow:hidden;'>
                        <div style='height:100%;width:{min(100, max(2, cash / STARTING_BUDGET * 50))}%;
                                    background:linear-gradient(90deg,#22d3ee,#a78bfa);border-radius:2px;'></div>
                    </div>
                </div>""", unsafe_allow_html=True)

                my_pos = [p for p in positions if p["team"] == my_team and p["qty"] != 0]
                if my_pos:
                    st.markdown("""<div style='font-size:.7rem;color:#64748b;text-transform:uppercase;
                        letter-spacing:.12em;font-weight:600;margin-top:1rem;margin-bottom:.5rem;'>Open Positions</div>""",
                        unsafe_allow_html=True)
                    for p in my_pos:
                        qty_color = "#34d399" if p["qty"] > 0 else "#fb7185"
                        side_label = "LONG" if p["qty"] > 0 else "SHORT"
                        st.markdown(f"""<div style='background:#111827;border:1px solid #2a3a50;border-radius:10px;
                            padding:.55rem .9rem;margin:.3rem 0;font-family:JetBrains Mono,monospace;font-size:.9rem;
                            display:flex;justify-content:space-between;align-items:center;'>
                            <div style='display:flex;align-items:center;gap:.5rem;'>
                                <span style='color:#a78bfa;font-weight:600;'>{_esc(p["stock"].upper())}</span>
                                <span style='font-size:.65rem;padding:.15rem .4rem;border-radius:4px;
                                            background:{qty_color}15;color:{qty_color};font-weight:600;'>{side_label}</span>
                            </div>
                            <span style='color:{qty_color};font-weight:700;'>{p["qty"]:+d}</span>
                        </div>""", unsafe_allow_html=True)

            if st.button("🚪 Leave team", use_container_width=True):
                release_team(my_team)
                st.session_state["claimed_team"] = None
                st.rerun()

        st.markdown("---")
        st.markdown(f"""<div style='background:#111827;border:1px solid #2a3a50;border-radius:12px;
                            padding:1rem 1.2rem;font-family:JetBrains Mono,monospace;font-size:.92rem;'>
            <div style='display:flex;justify-content:space-between;margin-bottom:.6rem;'>
                <span style='color:#64748b;font-weight:500;'>ROUND</span>
                <span style='color:#f1f5f9;font-weight:700;'>{round_num} / {TOTAL_ROUNDS}</span>
            </div>
            <div style='display:flex;justify-content:space-between;margin-bottom:.6rem;'>
                <span style='color:#64748b;font-weight:500;'>STOCK</span>
                <span style='color:#22d3ee;font-weight:700;'>{stock.upper()}</span>
            </div>
            <div style='display:flex;justify-content:space-between;'>
                <span style='color:#64748b;font-weight:500;'>PHASE</span>
                <span style='color:#fbbf24;font-weight:700;'>{phase.upper()}</span>
            </div>
        </div>""", unsafe_allow_html=True)
