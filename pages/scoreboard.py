"""
Live P&L Scoreboard — designed for the big screen during the hackathon.
Auto-refreshes every 6 seconds. No login required.
"""

import streamlit as st
import plotly.graph_objects as go

# ── allow imports from parent dir ──────────────────────────────────────────────
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import STARTING_BUDGET, TOTAL_ROUNDS, STOCKS
from db import get_game_state, get_teams, get_round_history, get_trade_log

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
    f"<span style='font-family:JetBrains Mono,monospace;font-size:2rem;font-weight:500;"
    f"color:#475569;vertical-align:super;margin-left:.15em;'>/ {TOTAL_ROUNDS}</span></p>"
    f"<p style='text-align:center;margin:0 0 .4rem;'>"
    f"<span style='font-family:JetBrains Mono,monospace;font-size:1.8rem;font-weight:800;"
    f"letter-spacing:.08em;background:linear-gradient(135deg,#22d3ee,#a78bfa);"
    f"-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>"
    f"{_stock_display}</span></p>"
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

# ── Ranking cards ──────────────────────────────────────────────────────────────
ranked = sorted(team_names, key=lambda n: cash_pnl[n], reverse=True)
medals = ["🥇", "🥈", "🥉"]

if ranked:
    cards_html = "<p style='display:flex;justify-content:center;gap:1.2rem;flex-wrap:wrap;margin:.2rem 0 1rem;'>"
    for i, name in enumerate(ranked):
        pnl = cash_pnl[name]
        col = TEAM_COLORS[i % len(TEAM_COLORS)]
        pnl_color = "#34d399" if pnl >= 0 else "#fb7185"
        medal = medals[i] if i < 3 else f"#{i+1}"
        glow = f"box-shadow:0 0 24px {col}35,inset 0 1px 0 {col}25;" if i < 3 else ""
        scale = "transform:scale(1.08);" if i == 0 else ""
        cards_html += (
            f"<span style='display:inline-block;background:linear-gradient(135deg,#111827,#1a2332);"
            f"border:1px solid {col}40;border-radius:18px;"
            f"padding:1rem 1.6rem;min-width:150px;text-align:center;{glow}{scale}"
            f"animation:float-up .5s ease {i*0.08}s both;'>"
            f"<span style='display:block;font-size:1.8rem;margin-bottom:.15rem;'>{medal}</span>"
            f"<span style='display:block;font-family:JetBrains Mono,monospace;font-size:1.15rem;"
            f"font-weight:800;color:{col};margin-bottom:.3rem;'>{name}</span>"
            f"<span style='display:block;font-family:JetBrains Mono,monospace;font-size:1.5rem;"
            f"font-weight:700;color:{pnl_color};'>${pnl:+,.0f}</span>"
            "</span>"
        )
    cards_html += "</p>"
    st.markdown(cards_html, unsafe_allow_html=True)

# ── P&L chart ─────────────────────────────────────────────────────────────────
if len(chart_rounds) > 1:
    fig = go.Figure()
    for i, name in enumerate(ranked):
        col = TEAM_COLORS[i % len(TEAM_COLORS)]
        fig.add_trace(go.Scatter(
            x=chart_rounds,
            y=chart_pnl[name],
            name=name,
            mode="lines+markers",
            line=dict(color=col, width=3.5, shape="spline", smoothing=1.2),
            marker=dict(size=9, color=col, line=dict(width=2, color="#06080f")),
            hovertemplate=f"<b>{name}</b><br>Round %{{x}}<br>P&L: $%{{y:+,.0f}}<extra></extra>",
        ))

    fig.add_hline(y=0, line_dash="dot", line_color="rgba(51,65,85,.5)", line_width=1)

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#94a3b8"),
        title=None,
        height=500,
        margin=dict(l=70, r=30, t=20, b=70),
        xaxis=dict(
            title=dict(text="Round", font=dict(size=14, color="#64748b")),
            dtick=1,
            gridcolor="rgba(42,58,80,.4)",
            zerolinecolor="rgba(42,58,80,.6)",
            tickfont=dict(size=14, family="JetBrains Mono, monospace"),
        ),
        yaxis=dict(
            title=dict(text="P&L ($)", font=dict(size=14, color="#64748b")),
            gridcolor="rgba(42,58,80,.3)",
            zerolinecolor="rgba(42,58,80,.6)",
            tickfont=dict(size=14, family="JetBrains Mono, monospace"),
            tickprefix="$",
            separatethousands=True,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(size=14, family="JetBrains Mono, monospace", color="#f1f5f9"),
            bgcolor="rgba(0,0,0,0)",
        ),
        hoverlabel=dict(
            bgcolor="#1a2332",
            bordercolor="#2a3a50",
            font=dict(size=14, family="JetBrains Mono, monospace"),
        ),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
else:
    st.markdown(
        "<p style='text-align:center;color:#475569;font-size:1.4rem;"
        "margin:3rem 0;font-weight:600;letter-spacing:.02em;'>"
        "Waiting for the first round to complete…</p>",
        unsafe_allow_html=True,
    )

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
        or set(latest_teams.keys()) != set(teams.keys())
        or any(latest_teams[n]["cash"] != teams[n]["cash"] for n in teams if n in latest_teams)
    )
    if changed:
        st.rerun()

if not game_over:
    _auto_refresh()
