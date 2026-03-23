"""
Live P&L Scoreboard — designed for the big screen during the hackathon.
Auto-refreshes every 6 seconds. No login required.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# ── allow imports from parent dir ──────────────────────────────────────────────
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import STARTING_BUDGET, TOTAL_ROUNDS, STOCKS
from db import get_game_state, get_teams, get_round_history, get_trade_log
from utils import dataframe_height, format_gbp, team_cash_signature

# ── page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Live Scoreboard", layout="wide", page_icon="🏆",
                   initial_sidebar_state="collapsed")

# ── CSS: dark cinematic look ───────────────────────────────────────────────────
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
:root{--bg:#06080f}
html,body,[data-testid="stAppViewContainer"]{
    background:var(--bg)!important;color:#f1f5f9!important;
    font-family:'Inter',-apple-system,sans-serif!important}
[data-testid="stAppViewContainer"]{
    background:radial-gradient(ellipse 80% 50% at 20% -20%,rgba(34,211,238,.05) 0%,transparent 70%),
    radial-gradient(ellipse 60% 40% at 80% 110%,rgba(167,139,250,.05) 0%,transparent 60%),var(--bg)!important}
#MainMenu,footer,header,[data-testid="stDecoration"],
[data-testid="stSidebar"]{display:none!important;visibility:hidden!important}
[data-testid="stHeader"]{display:none!important}
@keyframes shimmer{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
@keyframes pulse-glow{0%,100%{opacity:.6}50%{opacity:1}}
@keyframes float-up{0%{opacity:0;transform:translateY(20px)}100%{opacity:1;transform:translateY(0)}}</style>""", unsafe_allow_html=True)

# ── Fullscreen toggle button (injected into parent DOM via component JS) ───────
import streamlit.components.v1 as components
components.html("""
<script>
(function(){
  var doc=window.parent.document;
  if(doc.getElementById('fs-btn'))return;
  var s=doc.createElement('style');
  s.textContent=`
    #fs-btn{position:fixed;top:1rem;right:1rem;z-index:999999;
      background:rgba(17,24,39,.92);border:1px solid #2a3a50;border-radius:10px;
      color:#94a3b8;font-size:1.5rem;padding:.55rem .7rem;cursor:pointer;
      backdrop-filter:blur(8px);transition:all .2s;line-height:1;font-family:sans-serif}
    #fs-btn:hover{color:#22d3ee;border-color:#22d3ee;box-shadow:0 0 14px rgba(34,211,238,.3)}`;
  doc.head.appendChild(s);
  var b=doc.createElement('button');
  b.id='fs-btn';b.title='Toggle fullscreen';b.textContent='⛶';
  b.addEventListener('click',function(){
    if(!doc.fullscreenElement){doc.documentElement.requestFullscreen().catch(function(){})}
    else{doc.exitFullscreen()}
  });
  doc.body.appendChild(b);
})();
</script>
""", height=0)

# ── Team colors palette ────────────────────────────────────────────────────────
TEAM_COLORS = [
    "#22d3ee", "#a78bfa", "#34d399", "#fbbf24", "#fb7185",
    "#f97316", "#818cf8", "#2dd4bf", "#e879f9", "#facc15",
    "#4ade80", "#f472b6", "#38bdf8", "#c084fc", "#fb923c",
]

# ── Load data ──────────────────────────────────────────────────────────────────
gs = get_game_state()
round_num = gs["round"]
phase = gs["phase"]
game_over = gs["game_over"]
teams = get_teams()
history = get_round_history()
all_trades = get_trade_log()
stock = STOCKS[round_num - 1] if round_num <= len(STOCKS) else STOCKS[-1]
_stock_display = stock.upper().replace("_", " ")
total_teams = len(teams)
completed_trades = sum(1 for trade in all_trades if trade.get("qty", 0) > 0)

# ── Phase color ────────────────────────────────────────────────────────────────
_pc = {"submit": "#22d3ee", "trade": "#fbbf24", "reveal": "#34d399"}.get(phase, "#fbbf24")

# ── Hero title block ──────────────────────────────────────────────────────────
st.markdown(
    "<p style='text-align:center;margin:1rem 0 0;'>"
    "<span style='font-size:2.5rem;font-weight:900;letter-spacing:-.03em;"
    "background:linear-gradient(135deg,#22d3ee,#a78bfa,#34d399);"
    "background-size:200% auto;animation:shimmer 4s linear infinite;"
    "-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>"
    "LIVE SCOREBOARD</span></p>",
    unsafe_allow_html=True,
)

# ── Big round + stock display ──────────────────────────────────────────────────
st.markdown(
    f"<p style='text-align:center;margin:.6rem 0 .1rem;'>"
    f"<span style='font-family:JetBrains Mono,monospace;font-size:6rem;font-weight:900;"
    f"color:#f1f5f9;letter-spacing:-.06em;line-height:1;'>{round_num}</span>"
    f"<span style='font-family:JetBrains Mono,monospace;font-size:1.2rem;font-weight:500;"
    f"color:#475569;vertical-align:super;margin-left:.5em;'>{_stock_display}</span></p>"
    f"<p style='text-align:center;margin:0 0 .6rem;'>"
    f"<span style='display:inline-block;padding:.3rem .9rem;border-radius:8px;"
    f"background:{_pc}18;border:1px solid {_pc}30;"
    f"font-family:JetBrains Mono,monospace;font-size:.75rem;font-weight:700;"
    f"color:{_pc};letter-spacing:.2em;'>{phase.upper()} PHASE</span>"
    f"&nbsp;&nbsp;"
    f"<span style='display:inline-flex;align-items:center;gap:.35rem;"
    f"font-family:JetBrains Mono,monospace;font-size:.6rem;color:#64748b;"
    f"font-weight:600;letter-spacing:.15em;'>"
    f"<span style='width:7px;height:7px;border-radius:50%;background:#22d3ee;"
    f"display:inline-block;box-shadow:0 0 10px #22d3ee;"
    f"animation:pulse-glow 2s ease-in-out infinite;'></span>"
    f"LIVE</span></p>",
    unsafe_allow_html=True,
)

# ── Build cumulative P&L data ──────────────────────────────────────────────────
team_names = sorted(teams.keys())
cumulative = {n: 0.0 for n in team_names}
chart_rounds = [0]
chart_pnl = {n: [0.0] for n in team_names}

if history:
    for h in sorted(history, key=lambda x: x["round"]):
        rnd = h["round"]
        rnd_tp = h.get("true_price", 0) or 0
        for t in all_trades:
            if t["round"] == rnd and t["qty"] > 0:
                cost = t["price"] * t["qty"]
                if t["buyer"] in cumulative:
                    cumulative[t["buyer"]] -= cost
                    cumulative[t["buyer"]] += t["qty"] * rnd_tp
                if t["seller"] in cumulative:
                    cumulative[t["seller"]] += cost
                    cumulative[t["seller"]] -= t["qty"] * rnd_tp
        chart_rounds.append(rnd)
        for n in team_names:
            chart_pnl[n].append(round(cumulative[n], 2))

cash_pnl = {n: teams[n]["cash"] - STARTING_BUDGET for n in team_names}

# ── Last round P&L (change in current round only) ─────────────────────────────
last_round_pnl = {}
for n in team_names:
    if len(chart_pnl[n]) > 1:
        last_round_pnl[n] = chart_pnl[n][-1] - chart_pnl[n][-2]
    else:
        last_round_pnl[n] = chart_pnl[n][-1] if chart_pnl[n] else 0

# ── Ranking cards ──────────────────────────────────────────────────────────────
ranked = sorted(team_names, key=lambda n: cash_pnl[n], reverse=True)
medals = ["🥇", "🥈", "🥉"]

if ranked:
    # ── Compact top 6 medal cards ────────────────────────────────────────────────
    cards_html = "<p style='display:flex;justify-content:center;gap:0.8rem;flex-wrap:wrap;margin:.3rem 0 .8rem;'>"
    for i, name in enumerate(ranked[:6]):
        total_pnl = cash_pnl[name]
        col = TEAM_COLORS[i % len(TEAM_COLORS)]
        pnl_color = "#34d399" if total_pnl >= 0 else "#fb7185"
        medal = medals[i] if i < 3 else f"#{i+1}"
        glow = f"box-shadow:0 0 16px {col}35;" if i < 3 else ""
        scale = "transform:scale(1.05);" if i == 0 else ""
        min_width = "160px" if i < 3 else "140px"
        padding = "0.9rem 1rem" if i < 3 else "0.7rem 0.85rem"
        font_sizes = {
            'medal': '2rem' if i < 3 else '1.4rem',
            'name': '1.1rem' if i < 3 else '0.9rem',
            'pnl': '1.4rem' if i < 3 else '1rem'
        }
        cards_html += (
            f"<span style='display:inline-block;background:linear-gradient(135deg,#111827,#1a2332);"
            f"border:1px solid {col}40;border-radius:12px;"
            f"padding:{padding};min-width:{min_width};text-align:center;{glow}{scale}"
            f"animation:float-up .5s ease {i*0.08}s both;'>"
            f"<span style='display:block;font-size:{font_sizes['medal']};margin-bottom:.08rem;'>{medal}</span>"
            f"<span style='display:block;font-family:JetBrains Mono,monospace;font-size:{font_sizes['name']};"
            f"font-weight:700;color:{col};margin-bottom:.2rem;overflow:hidden;text-overflow:ellipsis;'>{name}</span>"
            f"<span style='display:block;font-family:JetBrains Mono,monospace;font-size:{font_sizes['pnl']};"
            f"font-weight:700;color:{pnl_color};'>{format_gbp(total_pnl, signed=True)}</span>"
            "</span>"
        )
    cards_html += "</p>"
    st.markdown(cards_html, unsafe_allow_html=True)

    # ── Side-by-side layout: graph on left, standings on right ───────────────────
    left, right = st.columns([1.15, 1], gap="medium")
    
    # ── P&L chart (left column) ────────────────────────────────────────────────
    with left:
        if len(chart_rounds) > 1:
            import numpy as np
            
            # Find min value across all teams to shift data for log scale
            all_pnl = [val for team_pnl in chart_pnl.values() for val in team_pnl]
            min_pnl = min(all_pnl) if all_pnl else 0
            # Extremely aggressive offset to compress large values massively
            offset = abs(min_pnl) + 10000 if min_pnl < 0 else 10000  # Massive offset for extreme compression
            
            fig = go.Figure()
            chart_names = ranked[: min(10, len(ranked))]
            max_shifted = 0
            
            for i, name in enumerate(chart_names):
                col = TEAM_COLORS[i % len(TEAM_COLORS)]
                original_y = chart_pnl[name]
                shifted_y = [val + offset for val in original_y]  # Shift for log scale
                max_shifted = max(max_shifted, max(shifted_y)) if shifted_y else max_shifted
                
                fig.add_trace(go.Scatter(
                    x=chart_rounds,
                    y=shifted_y,
                    name=name,
                    showlegend=False,
                    mode="lines+markers",
                    line=dict(color=col, width=3.5, shape="spline", smoothing=1.2),
                    marker=dict(size=9, color=col, line=dict(width=2, color="#06080f")),
                    customdata=[format_gbp(value, signed=True) for value in original_y],
                    hovertemplate=f"<b>{name}</b><br>Round %{{x}}<br>P&L: %{{customdata}}<extra></extra>",
                ))

            # Add zero line (shifted)
            fig.add_hline(y=offset, line_dash="dot", line_color="rgba(51,65,85,.5)", line_width=1)
            
            # Generate custom ticks with extreme log spacing
            # Use log spaced values for better readability with very wide range
            tick_values_shifted = np.logspace(0, np.log10(max_shifted + 1) if max_shifted > 1 else 2, 12)
            tick_labels = [format_gbp(v - offset, signed=True) for v in tick_values_shifted]

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", color="#94a3b8"),
                title=None,
                height=500,
                margin=dict(l=50, r=20, t=10, b=50),
                hovermode="x unified",
                xaxis=dict(
                    title=dict(text="Round", font=dict(size=12, color="#64748b")),
                    dtick=1,
                    gridcolor="rgba(42,58,80,.4)",
                    zerolinecolor="rgba(42,58,80,.6)",
                    tickfont=dict(size=12, family="JetBrains Mono, monospace"),
                ),
                yaxis=dict(
                    type="log",
                    gridcolor="rgba(42,58,80,.3)",
                    zerolinecolor="rgba(42,58,80,.6)",
                    tickfont=dict(size=11, family="JetBrains Mono, monospace"),
                    tickvals=tick_values_shifted,
                    ticktext=tick_labels,
                    separatethousands=True,
                ),
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01,
                    font=dict(size=10, family="JetBrains Mono, monospace", color="#f1f5f9"),
                    bgcolor="rgba(0,0,0,.3)",
                ),
                hoverlabel=dict(
                    bgcolor="#1a2332",
                    bordercolor="#2a3a50",
                    font=dict(size=12, family="JetBrains Mono, monospace"),
                    namelength=-1,
                ),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown(
                "<p style='text-align:center;color:#475569;font-size:1.2rem;"
                "margin:2rem 0;font-weight:600;letter-spacing:.02em;'>"
                "Waiting for the first round to complete…</p>",
                unsafe_allow_html=True,
            )
    
    # ── Standings table (right column) ─────────────────────────────────────────
    with right:
        st.markdown(
            "<p style='font-family:JetBrains Mono,monospace;font-size:0.75rem;font-weight:800;"
            "letter-spacing:.12em;color:#94a3b8;text-transform:uppercase;margin:.4rem 0 .6rem;'>"
            "Standings</p>",
            unsafe_allow_html=True,
        )
        
        # Column headers
        board_html = "<div style='display:grid;gap:0.35rem;'>"
        board_html += (
            "<div style='display:grid;grid-template-columns:40px 1fr 1fr 1fr;align-items:center;"
            "gap:0.6rem;padding:0.6rem 0.8rem;font-size:1.05rem;'>"
            f"<span style='font-family:JetBrains Mono,monospace;font-weight:800;color:#94a3b8;'></span>"
            f"<span style='font-family:JetBrains Mono,monospace;font-weight:800;color:#94a3b8;'>Team</span>"
            f"<span style='font-family:JetBrains Mono,monospace;font-weight:800;color:#94a3b8;text-align:right;'>Cash</span>"
            f"<span style='font-family:JetBrains Mono,monospace;font-weight:800;color:#94a3b8;text-align:right;'>PnL Last Round</span>"
            "</div>"
        )
        
        for position, name in enumerate(ranked, start=1):
            round_pnl = last_round_pnl[name]
            round_pnl_color = "#34d399" if round_pnl >= 0 else "#fb7185"
            
            board_html += (
                "<div style='display:grid;grid-template-columns:40px 1fr 1fr 1fr;align-items:center;"
                "gap:0.6rem;background:linear-gradient(135deg,#111827,#1a2332);border:1px solid #243044;"
                "border-radius:8px;padding:0.6rem 0.8rem;font-size:1.19rem;'>"
                f"<span style='font-family:JetBrains Mono,monospace;font-weight:900;color:#64748b;'>#{position}</span>"
                f"<span style='font-family:JetBrains Mono,monospace;font-weight:700;color:#f1f5f9;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>{name}</span>"
                f"<span style='font-family:JetBrains Mono,monospace;font-weight:600;color:#22d3ee;text-align:right;'>{format_gbp(teams[name]['cash'])}</span>"
                f"<span style='font-family:JetBrains Mono,monospace;font-weight:700;color:{round_pnl_color};text-align:right;'>{format_gbp(round_pnl, signed=True)}</span>"
                "</div>"
            )
        board_html += "</div>"
        st.markdown(board_html, unsafe_allow_html=True)

# ── Game over banner ───────────────────────────────────────────────────────────
if game_over and ranked:
    winner = ranked[0]
    st.markdown(
        f"<p style='text-align:center;font-size:4rem;font-weight:900;margin:2rem 0 .3rem;"
        f"background:linear-gradient(135deg,#fbbf24,#fb923c);-webkit-background-clip:text;"
        f"-webkit-text-fill-color:transparent;'>🏁 GAME OVER</p>"
        f"<p style='text-align:center;font-size:2.4rem;font-weight:800;color:#f1f5f9;"
        f"margin:0 0 2rem;'>Winner: {winner} 🎉</p>",
        unsafe_allow_html=True,
    )

# ── Auto-refresh ───────────────────────────────────────────────────────────────
@st.fragment(run_every=6)
def _auto_refresh():
    latest = get_game_state()
    latest_teams = get_teams()
    changed = (
        latest["round"] != round_num
        or latest["phase"] != phase
        or latest["game_over"] != game_over
        or team_cash_signature(latest_teams) != team_cash_signature(teams)
    )
    if changed:
        st.rerun()

if not game_over:
    _auto_refresh()
