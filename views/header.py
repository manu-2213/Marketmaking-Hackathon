import streamlit as st
import html as _html

from config import TOTAL_ROUNDS


def _esc(s):
    return _html.escape(str(s)) if s else ""


def render_header(is_admin, my_team, round_num, stock, phase):
    phase_colors = {"submit": "#22d3ee", "trade": "#fbbf24", "reveal": "#34d399"}
    phase_color = phase_colors.get(phase, "#fbbf24")

    if is_admin:
        identity_html = "<span style='font-family:JetBrains Mono,monospace;font-size:.75rem;color:#a78bfa;font-weight:700;'>🔧 Admin</span>"
    else:
        identity_html = f"""<span style='font-family:JetBrains Mono,monospace;font-size:.9rem;font-weight:800;
                     color:#f1f5f9;background:linear-gradient(135deg,rgba(34,211,238,.12),rgba(167,139,250,.08));
                     padding:.35rem .9rem;border-radius:10px;
                     border:1px solid rgba(34,211,238,.25);
                     box-shadow:0 0 12px rgba(34,211,238,.08);'>{_esc(my_team)}</span>"""

    _hdr = (
        "<p style='display:flex;justify-content:space-between;align-items:center;"
        "padding:.6rem 1.25rem;background:linear-gradient(135deg,rgba(17,24,39,.98),rgba(26,35,50,.95));"
        "border:1px solid #2a3a50;border-radius:14px;margin-bottom:1.75rem;"
        "backdrop-filter:blur(16px);box-shadow:0 4px 20px rgba(0,0,0,.3);'>"
        "<span style='display:flex;align-items:center;gap:1.5rem;'>"
        "<span style='font-family:JetBrains Mono,monospace;font-size:.75rem;font-weight:700;"
        "background:linear-gradient(135deg,#22d3ee,#a78bfa);-webkit-background-clip:text;"
        "-webkit-text-fill-color:transparent;letter-spacing:.1em;'>📈 MARKET MAKING</span>"
        "<span style='color:#2a3a50;font-size:1.1rem;'>│</span>"
        f"<span style='font-family:JetBrains Mono,monospace;font-size:.7rem;"
        f"padding:.2rem .6rem;border-radius:6px;background:rgba(167,139,250,.1);"
        f"border:1px solid rgba(167,139,250,.2);color:#a78bfa;font-weight:600;'>{stock.upper()}</span>"
        f"<span style='font-family:JetBrains Mono,monospace;font-size:.7rem;color:#94a3b8;'>RD {round_num}/{TOTAL_ROUNDS}</span>"
        f"<span style='font-family:JetBrains Mono,monospace;font-size:.65rem;"
        f"padding:.15rem .5rem;border-radius:4px;"
        f"background:{phase_color}18;color:{phase_color};font-weight:700;"
        f"letter-spacing:.08em;'>{phase.upper()}</span>"
        "</span>"
        f"{identity_html}"
        "</p>"
    )
    st.markdown(_hdr, unsafe_allow_html=True)
