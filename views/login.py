import streamlit as st

from config import ADMIN_PASSWORD
from db import claim_team


def render_login(teams, sessions, session_id):
    """Show the login gate. Returns True if st.stop() should be called."""
    st.markdown("""
    <div class='animate-in' style='text-align:center;padding:5rem 0 2rem'>
        <div style='display:inline-block;padding:.4rem 1.2rem;border-radius:20px;
                    background:linear-gradient(135deg,rgba(34,211,238,.1),rgba(167,139,250,.1));
                    border:1px solid rgba(34,211,238,.2);
                    font-family:JetBrains Mono,monospace;font-size:.65rem;letter-spacing:.3em;
                    color:#22d3ee;text-transform:uppercase;margin-bottom:1.5rem;'>
            HACKATHON 2025
        </div>
        <h1 style='font-size:4.2rem;font-weight:900;letter-spacing:-.05em;margin:0;
                   background:linear-gradient(135deg,#f1f5f9 0%,#94a3b8 50%,#22d3ee 100%);
                   background-size:200% auto;
                   -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                   line-height:1.05;animation:shimmer 4s linear infinite;'>
            Market Making<br>Challenge
        </h1>
        <div style='display:flex;justify-content:center;gap:2rem;margin-top:2rem;'>
            <div style='display:flex;align-items:center;gap:.5rem;'>
                <div style='width:8px;height:8px;border-radius:50%;background:#22d3ee;
                            box-shadow:0 0 10px rgba(34,211,238,.5);'></div>
                <span style='color:#94a3b8;font-size:.85rem;font-weight:500;'>9 Stocks</span>
            </div>
            <div style='display:flex;align-items:center;gap:.5rem;'>
                <div style='width:8px;height:8px;border-radius:50%;background:#a78bfa;
                            box-shadow:0 0 10px rgba(167,139,250,.5);'></div>
                <span style='color:#94a3b8;font-size:.85rem;font-weight:500;'>9 Rounds</span>
            </div>
            <div style='display:flex;align-items:center;gap:.5rem;'>
                <div style='width:8px;height:8px;border-radius:50%;background:#34d399;
                            box-shadow:0 0 10px rgba(52,211,153,.5);'></div>
                <span style='color:#94a3b8;font-size:.85rem;font-weight:500;'>Tightest Spread Wins</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("<br>", unsafe_allow_html=True)
        mode = st.radio("I am a", ["👥 Team", "🔧 Organiser / Admin"], horizontal=True)
        st.markdown("<br>", unsafe_allow_html=True)

        if "Admin" in mode:
            pwd = st.text_input("Admin password", type="password", placeholder="Enter password…")
            if st.button("Enter as Admin", type="primary", use_container_width=True):
                if pwd == ADMIN_PASSWORD:
                    st.session_state["is_admin"] = True
                    st.rerun()
                else:
                    st.error("Incorrect password")
        else:
            claimed = set(sessions.keys())
            available = [t for t in sorted(teams.keys()) if t not in claimed]
            if not teams:
                st.info("Waiting for the organiser to register teams.")
            elif not available:
                st.warning("All teams are claimed. Ask the organiser.")
            else:
                chosen = st.selectbox("Select your team", available)
                if st.button("Join Game →", type="primary", use_container_width=True):
                    if claim_team(chosen, session_id):
                        st.session_state["claimed_team"] = chosen
                        st.query_params["team"] = chosen
                        st.rerun()
                    else:
                        st.error("Just claimed — pick another.")
