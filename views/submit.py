import streamlit as st
import pandas as pd
import html as _html

from config import MIN_SHARES
from db import upsert_spread


def _esc(s):
    return _html.escape(str(s)) if s else ""


def render_submit(is_admin, my_team, round_num, stock, teams, spreads):
    if is_admin:
        return

    left, right = st.columns([1, 1], gap="large")

    with left:
        st.markdown("""<h2 style='font-size:1.8rem;font-weight:800;margin-bottom:.2rem;
            color:#f1f5f9;letter-spacing:-.03em;'>Submit Your Spread</h2>
            <p style='color:#64748b;margin-bottom:1.5rem;font-size:.88rem;'>
            The team with the tightest bid-ask spread becomes market maker.</p>""",
            unsafe_allow_html=True)

        existing = spreads.get(my_team, {})
        already = my_team in spreads

        bid_val = st.number_input("📉 Bid — your buy price ($)", min_value=0.0,
                                   value=float(existing.get("bid", 95.0)), step=0.01)
        ask_val = st.number_input("📈 Ask — your sell price ($)", min_value=0.0,
                                   value=float(existing.get("ask", 105.0)), step=0.01)

        if bid_val >= ask_val:
            st.error("Ask must be greater than bid.")
        else:
            spread_w = ask_val - bid_val
            st.markdown(f"""<div style='background:linear-gradient(135deg,rgba(34,211,238,.06),rgba(52,211,153,.04));
                border:1px solid rgba(34,211,238,.2);border-radius:14px;
                padding:.9rem 1.1rem;margin:.6rem 0;font-family:JetBrains Mono,monospace;
                position:relative;overflow:hidden;'>
                <div style='position:absolute;top:0;left:0;right:0;height:2px;
                            background:linear-gradient(90deg,#22d3ee,#34d399);opacity:.5;'></div>
                <span style='color:#64748b;font-size:.7rem;font-weight:600;letter-spacing:.1em;'>SPREAD WIDTH</span><br>
                <span style='color:#22d3ee;font-size:1.3rem;font-weight:700;'>${spread_w:.2f}</span>
                {"&nbsp;&nbsp;<span style='color:#fbbf24;font-size:.7rem;font-weight:600;'>✓ SUBMITTED — resubmit to update</span>" if already else ""}
            </div>""", unsafe_allow_html=True)

            if st.button("🔒 Lock In Spread", type="primary", use_container_width=True):
                upsert_spread(round_num, my_team, bid_val, ask_val)
                st.success("Spread submitted ✓")

    with right:
        st.markdown(f"""<h3 style='font-size:.85rem;font-weight:700;color:#7a90a8;
            letter-spacing:.12em;text-transform:uppercase;margin-bottom:1rem;'>
            Submissions — {len(spreads)}/{len(teams)}</h3>""", unsafe_allow_html=True)

        if teams:
            rows = [{"Team": t,
                      "Status": "✅ Submitted" if t in spreads else "⏳ Waiting…",
                      "You": "👈" if t == my_team else ""} for t in sorted(teams.keys())]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.caption("No teams registered yet.")
