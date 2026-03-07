import streamlit as st
import pandas as pd
import uuid
import html as _html
from supabase import create_client, Client

def _esc(s: str) -> str:
    """HTML-escape user-controlled strings before embedding in markup."""
    return _html.escape(str(s)) if s else ""

st.set_page_config(
    page_title="Market Making Hackathon",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

:root {
    --bg: #0a0e17;
    --surface: #111827;
    --surface2: #1a2332;
    --surface3: #1f2b3d;
    --surface-hover: #243044;
    --border: #2a3a50;
    --border-light: #334155;
    --accent: #22d3ee;
    --accent-glow: rgba(34,211,238,.15);
    --accent2: #a78bfa;
    --accent2-glow: rgba(167,139,250,.12);
    --green: #34d399;
    --green-glow: rgba(52,211,153,.12);
    --red: #fb7185;
    --red-glow: rgba(251,113,133,.12);
    --warn: #fbbf24;
    --warn-glow: rgba(251,191,36,.1);
    --text: #f1f5f9;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --mm: #c084fc;
    --gradient-primary: linear-gradient(135deg, #22d3ee, #a78bfa);
    --gradient-warm: linear-gradient(135deg, #fbbf24, #fb923c);
    --gradient-cool: linear-gradient(135deg, #34d399, #22d3ee);
}

/* ── Base ── */
html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
}
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(ellipse 80% 50% at 20% -20%, rgba(34,211,238,.04) 0%, transparent 70%),
        radial-gradient(ellipse 60% 40% at 80% 110%, rgba(167,139,250,.04) 0%, transparent 60%),
        radial-gradient(circle at 50% 50%, rgba(34,211,238,.01) 0%, transparent 50%),
        var(--bg) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f1729 0%, #0a0e17 100%) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--gradient-primary);
}

/* ── Hide defaults ── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }
h1, h2, h3, h4 {
    font-family: 'Inter', sans-serif !important;
    letter-spacing: -.03em;
    color: var(--text) !important;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, var(--surface2), var(--surface)) !important;
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
    padding: 1.25rem 1.5rem !important;
    position: relative;
    overflow: hidden;
}
[data-testid="stMetric"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--gradient-primary);
    opacity: .6;
}
[data-testid="stMetricLabel"] {
    color: var(--text-secondary) !important;
    font-size: .7rem !important;
    text-transform: uppercase;
    letter-spacing: .14em;
    font-weight: 600;
}
[data-testid="stMetricValue"] {
    color: var(--accent) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.5rem !important;
    font-weight: 700;
}

/* ── Buttons ── */
[data-testid="stButton"] > button {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 12px !important;
    transition: all .2s cubic-bezier(.4,0,.2,1) !important;
    font-size: .88rem !important;
    padding: .55rem 1.25rem !important;
}
[data-testid="stButton"] > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    background: var(--accent-glow) !important;
    box-shadow: 0 0 24px rgba(34,211,238,.1), 0 4px 12px rgba(0,0,0,.3) !important;
    transform: translateY(-1px) !important;
}
button[kind="primary"] {
    background: linear-gradient(135deg, #22d3ee, #06b6d4) !important;
    border-color: transparent !important;
    color: #0a0e17 !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 16px rgba(34,211,238,.2) !important;
}
button[kind="primary"]:hover {
    background: linear-gradient(135deg, #67e8f9, #22d3ee) !important;
    box-shadow: 0 6px 28px rgba(34,211,238,.35), 0 0 40px rgba(34,211,238,.1) !important;
    transform: translateY(-2px) !important;
}

/* ── Inputs ── */
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input {
    background: var(--surface3) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 12px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: .9rem !important;
    transition: all .2s !important;
}
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextInput"] input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-glow), 0 0 20px rgba(34,211,238,.08) !important;
}
[data-testid="stSelectbox"] > div > div {
    background: var(--surface3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    color: var(--text) !important;
}
div[data-baseweb="select"] span { color: var(--text) !important; }

/* ── DataFrames ── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
    overflow: hidden !important;
    box-shadow: 0 4px 16px rgba(0,0,0,.2) !important;
}
[data-testid="stDataFrame"] th {
    background: var(--surface2) !important;
    color: var(--text-secondary) !important;
    font-size: .68rem !important;
    text-transform: uppercase;
    letter-spacing: .12em;
    font-weight: 600;
}
[data-testid="stDataFrame"] td {
    color: var(--text) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: .8rem !important;
}

/* ── Progress ── */
[data-testid="stProgressBar"] > div > div {
    background: var(--gradient-primary) !important;
    border-radius: 6px !important;
    box-shadow: 0 0 12px rgba(34,211,238,.3) !important;
}
[data-testid="stProgressBar"] > div {
    background: var(--surface2) !important;
    border-radius: 6px !important;
    height: 6px !important;
}

/* ── Alerts ── */
[data-testid="stAlert"] {
    border-radius: 14px !important;
    border-width: 0 0 0 3px !important;
    backdrop-filter: blur(8px);
}
[data-testid="stAlert"][data-type="info"]    { background: rgba(34,211,238,.06) !important; border-color: var(--accent) !important; color: #a5f3fc !important; }
[data-testid="stAlert"][data-type="success"] { background: rgba(52,211,153,.06) !important; border-color: var(--green) !important; color: #a7f3d0 !important; }
[data-testid="stAlert"][data-type="warning"] { background: rgba(251,191,36,.06) !important; border-color: var(--warn) !important; color: #fde68a !important; }
[data-testid="stAlert"][data-type="error"]   { background: rgba(251,113,133,.06) !important; border-color: var(--red) !important; color: #fecdd3 !important; }

/* ── Tabs ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--border) !important;
    gap: .25rem;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    color: var(--text-muted) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 10px 10px 0 0 !important;
    padding: .5rem 1rem !important;
    transition: all .2s !important;
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover {
    color: var(--text-secondary) !important;
    background: var(--surface2) !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
    background: var(--accent-glow) !important;
}

/* ── Radio ── */
[data-testid="stRadio"] label { color: var(--text) !important; font-weight: 500; }

/* ── Expander ── */
[data-testid="stExpander"] {
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    background: var(--surface) !important;
    overflow: hidden;
}
[data-testid="stExpander"] summary { color: var(--text) !important; font-weight: 600; }

/* ── Divider ── */
hr { border-color: var(--border) !important; opacity: .6 !important; }

/* ── Caption ── */
[data-testid="stCaptionContainer"] {
    color: var(--text-muted) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: .68rem !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

/* ── Animations ── */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 8px rgba(34,211,238,.15); }
    50% { box-shadow: 0 0 20px rgba(34,211,238,.3); }
}
@keyframes shimmer {
    0% { background-position: -200% center; }
    100% { background-position: 200% center; }
}
.animate-in { animation: fadeInUp .4s ease-out; }
.glow-pulse { animation: pulse-glow 3s ease-in-out infinite; }
</style>
""", unsafe_allow_html=True)

# ── Session ────────────────────────────────────────────────────────────────────
if "session_id"   not in st.session_state: st.session_state["session_id"]   = str(uuid.uuid4())
if "claimed_team" not in st.session_state: st.session_state["claimed_team"] = None
if "is_admin"     not in st.session_state: st.session_state["is_admin"]     = False
SESSION_ID = st.session_state["session_id"]

STARTING_BUDGET = 100_000
STOCKS          = [f"stock_{i}" for i in range(1, 10)]
TOTAL_ROUNDS    = 9
MIN_SHARES      = 5
ADMIN_PASSWORD  = "admin123"

@st.cache_resource
def get_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
sb = get_supabase()

# ── DB helpers ─────────────────────────────────────────────────────────────────
def get_game_state():
    return sb.table("game_state").select("*").eq("id",1).single().execute().data

def set_game_state(**kw):
    sb.table("game_state").update(kw).eq("id",1).execute()

def get_teams():
    return {r["name"]:r for r in sb.table("teams").select("*").execute().data}

def add_team(name):
    sb.table("teams").insert({"name":name,"cash":STARTING_BUDGET}).execute()

def delete_all_teams():
    sb.table("team_sessions").delete().neq("team","").execute()
    sb.table("teams").delete().neq("name","").execute()

def get_sessions():
    return {r["team"]:r["session_id"] for r in sb.table("team_sessions").select("*").execute().data}

def claim_team(team, sid):
    ex = sb.table("team_sessions").select("*").eq("team",team).execute()
    if ex.data: return ex.data[0]["session_id"] == sid
    sb.table("team_sessions").insert({"team":team,"session_id":sid}).execute()
    return True

def release_team(team):
    sb.table("team_sessions").delete().eq("team",team).execute()

def get_positions():
    return sb.table("positions").select("*").execute().data

def upsert_position(team, stk, dq, dc):
    r = sb.table("positions").select("*").eq("team",team).eq("stock",stk).execute()
    if r.data:
        row=r.data[0]
        sb.table("positions").update({"qty":row["qty"]+dq,"cost_basis":row["cost_basis"]+dc}).eq("id",row["id"]).execute()
    else:
        sb.table("positions").insert({"team":team,"stock":stk,"qty":dq,"cost_basis":dc}).execute()

def update_cash(team, delta):
    teams = get_teams()
    sb.table("teams").update({"cash":teams[team]["cash"]+delta}).eq("name",team).execute()

def get_spreads(rnd):
    return {r["team"]:r for r in sb.table("spreads").select("*").eq("round",rnd).execute().data}

def upsert_spread(rnd, team, bid, ask):
    sb.table("spreads").upsert({"round":rnd,"team":team,"bid":bid,"ask":ask},on_conflict="round,team").execute()

def get_true_prices():
    return {r["stock"]:r["price"] for r in sb.table("true_prices").select("*").execute().data}

def set_true_price(stk, price):
    sb.table("true_prices").upsert({"stock":stk,"price":price}).execute()

def get_trade_log(rnd=None):
    q = sb.table("trade_log").select("*").order("executed_at")
    if rnd: q=q.eq("round",rnd)
    return q.execute().data

def log_trade(rnd,stk,buyer,seller,price,qty):
    sb.table("trade_log").insert({"round":rnd,"stock":stk,"buyer":buyer,"seller":seller,"price":price,"qty":qty}).execute()

def has_traded_this_round(team, rnd):
    """Return True if this team already submitted a trade this round (as buyer or seller, excluding MM fills)."""
    r = sb.table("trade_log").select("*").eq("round",rnd).execute().data
    for t in r:
        if t["buyer"] == team or (t["seller"] == team and t["seller"] != get_game_state()["market_maker"]):
            return True
    return False

def has_passed_this_round(team, rnd):
    """Return True if this team chose to PASS this round."""
    r = sb.table("trade_log").select("*").eq("round", rnd).eq("buyer", team).eq("qty", 0).execute().data
    return len(r) > 0

def log_pass(team, rnd, stk):
    """Record a PASS decision so the team can't change their mind."""
    sb.table("trade_log").insert({"round": rnd, "stock": stk, "buyer": team, "seller": "PASS", "price": 0, "qty": 0}).execute()

def get_round_history():
    return sb.table("round_history").select("*").order("round").execute().data

def log_round(rnd, stk, mm, tp):
    sb.table("round_history").upsert({"round":rnd,"stock":stk,"market_maker":mm,"true_price":tp}).execute()

def settle_round(rnd, stk, true_price):
    """Convert all open positions for this stock to cash at the true price."""
    pos = sb.table("positions").select("*").eq("stock",stk).execute().data
    for p in pos:
        if p["qty"] != 0:
            proceeds = p["qty"] * true_price
            update_cash(p["team"], proceeds)
    # Zero out positions for this stock
    sb.table("positions").update({"qty":0,"cost_basis":0}).eq("stock",stk).execute()

def reset_game():
    for tbl,col in [("trade_log","id"),("round_history","round"),("spreads","id"),
                    ("true_prices","stock"),("positions","id"),("team_sessions","team"),("teams","name")]:
        sb.table(tbl).delete().neq(col,"" if col in("stock","team","name") else 0).execute()
    sb.table("game_state").update({"round":1,"phase":"submit","market_maker":None,"game_over":False}).eq("id",1).execute()

# ── Business logic ─────────────────────────────────────────────────────────────
def find_market_maker(spreads):
    if not spreads: return None
    return min(spreads, key=lambda t:(spreads[t]["ask"]-spreads[t]["bid"],t))

def execute_trade(buyer, seller, stk, price, qty, rnd):
    """Buyer pays ask*qty cash, gets qty shares. Seller gets cash, loses shares."""
    cost = price * qty
    update_cash(buyer, -cost)
    update_cash(seller, +cost)
    upsert_position(buyer, stk, +qty, +cost)
    upsert_position(seller, stk, -qty, -cost)
    log_trade(rnd, stk, buyer, seller, price, qty)

def portfolio_value(name, teams, positions, tp):
    cash = teams[name]["cash"]
    return cash + sum(p["qty"]*tp[p["stock"]] for p in positions if p["team"]==name and p["stock"] in tp)

# ── Load state ─────────────────────────────────────────────────────────────────
gs           = get_game_state()
round_num    = gs["round"]
phase        = gs["phase"]
market_maker = gs["market_maker"]
game_over    = gs["game_over"]
stock        = STOCKS[round_num-1]
teams        = get_teams()
sessions     = get_sessions()
spreads      = get_spreads(round_num)
true_prices  = get_true_prices()
positions    = get_positions()

my_team  = st.session_state["claimed_team"]
is_admin = st.session_state["is_admin"]
if not is_admin and my_team is None:
    for team,sid in sessions.items():
        if sid==SESSION_ID:
            my_team=team; st.session_state["claimed_team"]=team; break

# ══════════════════════════════════════════════════════════════════════════════
# LOGIN GATE
# ══════════════════════════════════════════════════════════════════════════════
if not is_admin and my_team is None:
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
    _,col,_ = st.columns([1,2,1])
    with col:
        st.markdown("<br>", unsafe_allow_html=True)
        mode = st.radio("I am a", ["👥 Team","🔧 Organiser / Admin"], horizontal=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if "Admin" in mode:
            pwd = st.text_input("Admin password", type="password", placeholder="Enter password…")
            if st.button("Enter as Admin", type="primary", use_container_width=True):
                if pwd == ADMIN_PASSWORD:
                    st.session_state["is_admin"] = True; st.rerun()
                else:
                    st.error("Incorrect password")
        else:
            claimed   = set(sessions.keys())
            available = [t for t in sorted(teams.keys()) if t not in claimed]
            if not teams:
                st.info("Waiting for the organiser to register teams.")
            elif not available:
                st.warning("All teams are claimed. Ask the organiser.")
            else:
                chosen = st.selectbox("Select your team", available)
                if st.button("Join Game →", type="primary", use_container_width=True):
                    if claim_team(chosen, SESSION_ID):
                        st.session_state["claimed_team"]=chosen; st.rerun()
                    else:
                        st.error("Just claimed — pick another.")
    st.stop()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    if is_admin:
        st.markdown("""<div style='padding:.75rem 0 .5rem'>
            <div style='font-size:.6rem;letter-spacing:.25em;color:#22d3ee;text-transform:uppercase;font-weight:600;'>Role</div>
            <div style='font-size:1.3rem;font-weight:800;color:#f1f5f9;margin-top:.2rem;'>🔧 Admin</div>
        </div>""", unsafe_allow_html=True)
        if st.button("🚪 Sign out", use_container_width=True):
            st.session_state["is_admin"]=False; st.rerun()
    else:
        st.markdown(f"""<div style='padding:.75rem 0 .5rem'>
            <div style='font-size:.6rem;letter-spacing:.25em;color:#22d3ee;text-transform:uppercase;font-weight:600;'>Playing as</div>
            <div style='font-size:1.3rem;font-weight:800;color:#f1f5f9;margin-top:.2rem;'>{_esc(my_team)}</div>
        </div>""", unsafe_allow_html=True)
        if teams and my_team in teams:
            cash = teams[my_team]["cash"]
            pnl = cash - STARTING_BUDGET
            pnl_color = "#34d399" if pnl >= 0 else "#fb7185"
            st.markdown(f"""<div style='background:linear-gradient(135deg,#111827,#1a2332);
                border:1px solid #2a3a50;border-radius:14px;
                padding:1rem 1.1rem;margin:.6rem 0;'>
                <div style='display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:.5rem;'>
                    <div>
                        <div style='font-size:.55rem;color:#64748b;text-transform:uppercase;letter-spacing:.12em;font-weight:600;'>Cash</div>
                        <div style='font-family:JetBrains Mono,monospace;font-size:1.15rem;font-weight:700;
                                    color:{"#34d399" if cash>=0 else "#fb7185"};margin-top:.15rem;'>${cash:,.0f}</div>
                    </div>
                    <div style='text-align:right;'>
                        <div style='font-size:.55rem;color:#64748b;text-transform:uppercase;letter-spacing:.12em;font-weight:600;'>P&L</div>
                        <div style='font-family:JetBrains Mono,monospace;font-size:.85rem;font-weight:600;
                                    color:{pnl_color};margin-top:.15rem;'>${pnl:+,.0f}</div>
                    </div>
                </div>
                <div style='height:3px;border-radius:2px;background:#1f2b3d;overflow:hidden;'>
                    <div style='height:100%;width:{min(100, max(2, cash / STARTING_BUDGET * 50))}%;
                                background:linear-gradient(90deg,#22d3ee,#a78bfa);border-radius:2px;'></div>
                </div>
            </div>""", unsafe_allow_html=True)
            # ── Portfolio positions ──
            my_pos = [p for p in positions if p["team"] == my_team and p["qty"] != 0]
            if my_pos:
                st.markdown("""<div style='font-size:.55rem;color:#64748b;text-transform:uppercase;
                    letter-spacing:.12em;font-weight:600;margin-top:.8rem;margin-bottom:.4rem;'>Open Positions</div>""", unsafe_allow_html=True)
                for p in my_pos:
                    qty_color = "#34d399" if p["qty"] > 0 else "#fb7185"
                    side_label = "LONG" if p["qty"] > 0 else "SHORT"
                    st.markdown(f"""<div style='background:#111827;border:1px solid #2a3a50;border-radius:10px;
                        padding:.45rem .75rem;margin:.2rem 0;font-family:JetBrains Mono,monospace;font-size:.75rem;
                        display:flex;justify-content:space-between;align-items:center;'>
                        <div style='display:flex;align-items:center;gap:.5rem;'>
                            <span style='color:#a78bfa;font-weight:600;'>{_esc(p["stock"].upper())}</span>
                            <span style='font-size:.55rem;padding:.1rem .35rem;border-radius:4px;
                                        background:{qty_color}15;color:{qty_color};font-weight:600;'>{side_label}</span>
                        </div>
                        <span style='color:{qty_color};font-weight:700;'>{p["qty"]:+d}</span>
                    </div>""", unsafe_allow_html=True)
        if st.button("🚪 Leave team", use_container_width=True):
            release_team(my_team); st.session_state["claimed_team"]=None; st.rerun()
    st.markdown("---")
    st.markdown(f"""<div style='background:#111827;border:1px solid #2a3a50;border-radius:12px;
                        padding:.8rem 1rem;font-family:JetBrains Mono,monospace;font-size:.72rem;'>
        <div style='display:flex;justify-content:space-between;margin-bottom:.4rem;'>
            <span style='color:#64748b;font-weight:500;'>ROUND</span>
            <span style='color:#f1f5f9;font-weight:700;'>{round_num} / {TOTAL_ROUNDS}</span>
        </div>
        <div style='display:flex;justify-content:space-between;margin-bottom:.4rem;'>
            <span style='color:#64748b;font-weight:500;'>STOCK</span>
            <span style='color:#22d3ee;font-weight:700;'>{stock.upper()}</span>
        </div>
        <div style='display:flex;justify-content:space-between;'>
            <span style='color:#64748b;font-weight:500;'>PHASE</span>
            <span style='color:#fbbf24;font-weight:700;'>{phase.upper()}</span>
        </div>
    </div>""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
identity_label = "🔧 Admin" if is_admin else f"🏷 {_esc(my_team)}"
phase_colors = {"submit": "#22d3ee", "trade": "#fbbf24", "reveal": "#34d399"}
phase_color = phase_colors.get(phase, "#fbbf24")
st.markdown(f"""
<div class='animate-in' style='display:flex;justify-content:space-between;align-items:center;
            padding:.6rem 1.25rem;background:linear-gradient(135deg,rgba(17,24,39,.98),rgba(26,35,50,.95));
            border:1px solid #2a3a50;border-radius:14px;margin-bottom:1.75rem;
            backdrop-filter:blur(16px);box-shadow:0 4px 20px rgba(0,0,0,.3);'>
    <div style='display:flex;align-items:center;gap:1.5rem;'>
        <span style='font-family:JetBrains Mono,monospace;font-size:.75rem;font-weight:700;
                     background:linear-gradient(135deg,#22d3ee,#a78bfa);-webkit-background-clip:text;
                     -webkit-text-fill-color:transparent;letter-spacing:.1em;'>📈 MARKET MAKING</span>
        <span style='color:#2a3a50;font-size:1.1rem;'>│</span>
        <div style='display:flex;align-items:center;gap:.75rem;'>
            <span style='font-family:JetBrains Mono,monospace;font-size:.7rem;
                         padding:.2rem .6rem;border-radius:6px;background:rgba(167,139,250,.1);
                         border:1px solid rgba(167,139,250,.2);color:#a78bfa;font-weight:600;'>{stock.upper()}</span>
            <span style='font-family:JetBrains Mono,monospace;font-size:.7rem;color:#94a3b8;'>RD {round_num}/{TOTAL_ROUNDS}</span>
            <span style='font-family:JetBrains Mono,monospace;font-size:.65rem;
                         padding:.15rem .5rem;border-radius:4px;
                         background:{phase_color}18;color:{phase_color};font-weight:700;
                         letter-spacing:.08em;'>{phase.upper()}</span>
        </div>
    </div>
    <span style='font-family:JetBrains Mono,monospace;font-size:.7rem;color:#94a3b8;
                 background:#1a2332;padding:.3rem .8rem;border-radius:8px;
                 border:1px solid #2a3a50;'>{identity_label}</span>
</div>
""", unsafe_allow_html=True)

# ── Game over ──────────────────────────────────────────────────────────────────
if game_over:
    st.balloons()
    st.markdown("""<div class='animate-in' style='text-align:center;padding:2rem 0;'>
        <div style='font-size:4rem;margin-bottom:.5rem;'>🏁</div>
        <h1 style='font-size:3.2rem;font-weight:900;letter-spacing:-.04em;
            background:linear-gradient(135deg,#22d3ee,#a78bfa,#34d399);
            background-size:200% auto;animation:shimmer 3s linear infinite;
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:.5rem;'>
            Final Results</h1>
        <p style='color:#64748b;font-size:.9rem;'>The game has ended. Here are the final standings.</p>
    </div>""", unsafe_allow_html=True)
    rows=[]
    for n in teams:
        t=teams[n]["cash"]  # all settled to cash
        rows.append({"Rank":"","Team":n,"Final Cash":f"${t:,.0f}","P&L":f"${t-STARTING_BUDGET:+,.0f}"})
    df=pd.DataFrame(rows).sort_values("Final Cash",ascending=False).reset_index(drop=True)
    df["Rank"]=["🥇","🥈","🥉"]+[""]*(max(0,len(df)-3))
    st.dataframe(df,use_container_width=True,hide_index=True)
    if is_admin and st.button("🔄 Reset Game",use_container_width=True): reset_game(); st.rerun()
    st.stop()

st.progress((round_num-1)/TOTAL_ROUNDS)
st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN PANEL
# ══════════════════════════════════════════════════════════════════════════════
if is_admin:
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
        @st.fragment
        def _teams_fragment():
            _teams = get_teams()
            _sessions = get_sessions()
            c1,c2 = st.columns([1,2])
            with c1:
                with st.form("add_team_form", clear_on_submit=True):
                    new_team = st.text_input("", placeholder="Team name…", label_visibility="collapsed")
                    submitted = st.form_submit_button("➕ Add Team", type="primary", use_container_width=True)
                    if submitted:
                        if new_team.strip():
                            if new_team.strip() not in _teams:
                                add_team(new_team.strip())
                                st.toast(f"✅ Added {new_team.strip()}")
                            else: st.warning("Already exists")
                        else: st.warning("Enter a name")
            with c2:
                if _teams:
                    rows=[{"Team":t,"Status":"🟢 Online" if t in _sessions else "⚪ Not joined",
                           "Cash":f"${_teams[t]['cash']:,.0f}"} for t in sorted(_teams.keys())]
                    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
                else:
                    st.info("No teams yet.")
            if _sessions:
                st.markdown("**Release a slot:**")
                rc1,rc2=st.columns([2,1])
                with rc1: to_rel=st.selectbox("",sorted(_sessions.keys()),label_visibility="collapsed")
                with rc2:
                    if st.button("🔓 Release",use_container_width=True): release_team(to_rel); st.rerun()
            if _teams:
                st.markdown("---")
                if st.button("🗑 Remove All Teams",use_container_width=True): delete_all_teams(); st.rerun()
        _teams_fragment()

    with tab_phase:
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
                rows=[{"Team":t,"Bid":f"${s['bid']:.2f}","Ask":f"${s['ask']:.2f}",
                       "Spread":f"${s['ask']-s['bid']:.2f}"} for t,s in spreads.items()]
                st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
            else:
                st.info("Waiting for teams to submit spreads.")
            if st.button("⏩ Close Submissions & Open Trading", type="primary", use_container_width=True):
                mm=find_market_maker(spreads)
                if mm: set_game_state(market_maker=mm,phase="trade"); st.rerun()
                else: st.error("No spreads submitted yet.")

        elif phase == "trade":
            round_trades=get_trade_log(round_num)
            real_trades = [t for t in round_trades if t.get("qty", 0) > 0]
            st.success(f"Market Maker: **{market_maker}**")
            st.markdown(f"Trades executed: **{len(real_trades)}**")
            if real_trades:
                df_t=pd.DataFrame(real_trades)[["buyer","seller","price","qty","executed_at"]]
                df_t.columns=["Buyer","Seller","Price","Qty","Time"]
                df_t["Price"]=df_t["Price"].apply(lambda v:f"${v:.2f}")
                df_t["Time"]=df_t["Time"].apply(lambda v:str(v)[-15:-7] if v else "")
                st.dataframe(df_t,use_container_width=True,hide_index=True)
            st.markdown("---")
            true_p=st.number_input("True price ($)", min_value=0.0, value=100.0, step=0.01)
            if st.button("✅ Reveal True Price & Settle All Positions", type="primary", use_container_width=True):
                set_true_price(stock, true_p)
                settle_round(round_num, stock, true_p)
                set_game_state(phase="reveal")
                st.rerun()

        elif phase == "reveal":
            tp=true_prices.get(stock)
            st.success(f"True price: **${tp:.2f}**" if tp else "True price set.")
            st.info("All positions settled to cash at the true price.")
            st.markdown("---")
            if round_num < TOTAL_ROUNDS:
                if st.button(f"▶ Start Round {round_num+1} — {STOCKS[round_num].upper()}", type="primary", use_container_width=True):
                    log_round(round_num,stock,market_maker,true_prices.get(stock))
                    set_game_state(round=round_num+1,phase="submit",market_maker=None)
                    st.rerun()
            else:
                if st.button("🏁 End Game & Show Final Results", type="primary", use_container_width=True):
                    log_round(round_num,stock,market_maker,true_prices.get(stock))
                    set_game_state(game_over=True)
                    st.rerun()

    with tab_danger:
        st.warning("This will delete all teams, spreads, trades and reset to round 1.")
        confirm=st.text_input("Type RESET to confirm")
        if st.button("🔄 Reset Entire Game", use_container_width=True):
            if confirm=="RESET": reset_game(); st.rerun()
            else: st.error("Type RESET to confirm")

    st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# SUBMIT PHASE
# ══════════════════════════════════════════════════════════════════════════════
if phase == "submit":
    if not is_admin:
        left,right = st.columns([1,1],gap="large")
        with left:
            st.markdown("""<h2 style='font-size:1.8rem;font-weight:800;margin-bottom:.2rem;
                color:#f1f5f9;letter-spacing:-.03em;'>Submit Your Spread</h2>
                <p style='color:#64748b;margin-bottom:1.5rem;font-size:.88rem;'>
                The team with the tightest bid-ask spread becomes market maker.</p>""", unsafe_allow_html=True)
            existing=spreads.get(my_team,{})
            already=my_team in spreads
            bid_val=st.number_input("📉 Bid — your buy price ($)", min_value=0.0,
                                    value=float(existing.get("bid",95.0)), step=0.01)
            ask_val=st.number_input("📈 Ask — your sell price ($)", min_value=0.0,
                                    value=float(existing.get("ask",105.0)), step=0.01)
            if bid_val >= ask_val:
                st.error("Ask must be greater than bid.")
            else:
                spread_w=ask_val-bid_val
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
                    upsert_spread(round_num,my_team,bid_val,ask_val)
                    st.success("Spread submitted ✓"); st.rerun()

        with right:
            st.markdown(f"""<h3 style='font-size:.85rem;font-weight:700;color:#7a90a8;
                letter-spacing:.12em;text-transform:uppercase;margin-bottom:1rem;'>
                Submissions — {len(spreads)}/{len(teams)}</h3>""", unsafe_allow_html=True)
            if teams:
                rows=[{"Team":t,
                       "Status":"✅ Submitted" if t in spreads else "⏳ Waiting…",
                       "You":"👈" if t==my_team else ""} for t in sorted(teams.keys())]
                st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
            else:
                st.caption("No teams registered yet.")

# ══════════════════════════════════════════════════════════════════════════════
# TRADE PHASE
# ══════════════════════════════════════════════════════════════════════════════
elif phase == "trade":
    mm_spread=spreads.get(market_maker,{})
    mm_bid=mm_spread.get("bid",0)
    mm_ask=mm_spread.get("ask",0)
    is_mm=(my_team==market_maker)

    # MM hero card
    st.markdown(f"""
    <div class='animate-in' style='background:linear-gradient(135deg,rgba(167,139,250,.08),rgba(34,211,238,.04));
                border:1px solid rgba(167,139,250,.2);border-radius:20px;
                padding:1.6rem 2rem;margin-bottom:1.75rem;position:relative;overflow:hidden;
                box-shadow:0 8px 32px rgba(0,0,0,.2);'>
        <div style='position:absolute;top:0;left:0;right:0;height:2px;
                    background:linear-gradient(90deg,#a78bfa,#22d3ee);'></div>
        <div style='position:absolute;top:1rem;right:1.5rem;font-size:2.5rem;opacity:.12;'>🏦</div>
        <div style='font-size:.6rem;letter-spacing:.3em;color:#a78bfa;text-transform:uppercase;
                    font-weight:700;margin-bottom:.75rem;'>Market Maker This Round</div>
        <div style='font-size:2rem;font-weight:800;color:#f1f5f9;margin-bottom:1.1rem;
                    letter-spacing:-.02em;'>{_esc(market_maker)}</div>
        <div style='display:flex;gap:1.5rem;flex-wrap:wrap;'>
            <div style='background:rgba(52,211,153,.06);border:1px solid rgba(52,211,153,.15);
                        border-radius:12px;padding:.65rem 1rem;min-width:100px;'>
                <div style='font-size:.55rem;color:#64748b;text-transform:uppercase;letter-spacing:.12em;font-weight:600;'>BID</div>
                <div style='font-family:JetBrains Mono,monospace;font-size:1.3rem;font-weight:700;color:#34d399;margin-top:.15rem;'>${mm_bid:.2f}</div>
            </div>
            <div style='background:rgba(34,211,238,.06);border:1px solid rgba(34,211,238,.15);
                        border-radius:12px;padding:.65rem 1rem;min-width:100px;'>
                <div style='font-size:.55rem;color:#64748b;text-transform:uppercase;letter-spacing:.12em;font-weight:600;'>ASK</div>
                <div style='font-family:JetBrains Mono,monospace;font-size:1.3rem;font-weight:700;color:#22d3ee;margin-top:.15rem;'>${mm_ask:.2f}</div>
            </div>
            <div style='background:rgba(251,191,36,.06);border:1px solid rgba(251,191,36,.15);
                        border-radius:12px;padding:.65rem 1rem;min-width:100px;'>
                <div style='font-size:.55rem;color:#64748b;text-transform:uppercase;letter-spacing:.12em;font-weight:600;'>SPREAD</div>
                <div style='font-family:JetBrains Mono,monospace;font-size:1.3rem;font-weight:700;color:#fbbf24;margin-top:.15rem;'>${mm_ask-mm_bid:.2f}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not is_admin:
        left,right=st.columns([1,1],gap="large")
        with left:
            if is_mm:
                st.markdown("""<div style='background:linear-gradient(135deg,rgba(167,139,250,.08),rgba(34,211,238,.04));
                    border:1px solid rgba(167,139,250,.2);border-radius:18px;
                    padding:2rem;text-align:center;position:relative;overflow:hidden;'>
                    <div style='position:absolute;top:0;left:0;right:0;height:2px;
                                background:linear-gradient(90deg,#a78bfa,#22d3ee);'></div>
                    <div style='font-size:3rem;margin-bottom:.75rem;filter:drop-shadow(0 0 12px rgba(167,139,250,.3));'>🏦</div>
                    <div style='font-weight:800;font-size:1.25rem;color:#a78bfa;margin-bottom:.5rem;'>You are the Market Maker</div>
                    <div style='color:#64748b;font-size:.85rem;line-height:1.7;max-width:320px;margin:0 auto;'>
                        You must fill every trade placed against you.<br>
                        You can go negative. Positions settle at true price.
                    </div>
                </div>""", unsafe_allow_html=True)
            else:
                # Check if already traded or passed
                already_traded = has_traded_this_round(my_team, round_num)
                already_passed = has_passed_this_round(my_team, round_num)
                my_cash = teams[my_team]["cash"]

                st.markdown(f"""<h3 style='font-weight:800;font-size:1.25rem;margin-bottom:.25rem;
                    color:#f1f5f9;letter-spacing:-.02em;'>Your Trade Decision</h3>
                    <p style='color:#64748b;font-size:.78rem;margin-bottom:1rem;'>Min {MIN_SHARES} shares per trade</p>""", unsafe_allow_html=True)

                if already_traded or already_passed:
                    if already_passed:
                        st.info("⏭ You passed this round. Wait for the reveal.")
                    else:
                        st.warning("✅ You've already placed your trade this round. Wait for the reveal.")
                else:
                    action=st.radio("Direction",["🟢 BUY shares (at ask)","🔴 SELL shares (at bid)","⏭ PASS (no trade)"],horizontal=True)
                    is_pass="PASS" in action
                    is_buy="BUY" in action

                    if is_pass:
                        st.markdown("""<div style='background:linear-gradient(135deg,rgba(100,116,139,.06),rgba(148,163,184,.04));
                            border:1px solid rgba(100,116,139,.2);border-radius:14px;
                            padding:1rem 1.2rem;margin:.6rem 0;'>
                            <div style='display:flex;align-items:center;gap:.6rem;'>
                                <span style='font-size:1.3rem;'>⏭</span>
                                <span style='color:#94a3b8;font-size:.85rem;font-weight:500;'>You will sit out this round — no position taken.</span>
                            </div>
                        </div>""", unsafe_allow_html=True)
                        if st.button("⏭ Confirm PASS", type="primary", use_container_width=True):
                            log_pass(my_team, round_num, stock)
                            st.info("Passed this round."); st.rerun()
                    else:
                        price=mm_ask if is_buy else mm_bid
                        # Fix: compute sensible max_qty for sells based on affordable short exposure
                        if is_buy:
                            max_qty = int(my_cash // price) if price > 0 else 1
                        else:
                            max_qty = int(my_cash // price) if price > 0 else 1
                        max_qty = max(MIN_SHARES, max_qty)
                        qty=st.number_input("Number of shares",min_value=MIN_SHARES,max_value=max_qty,value=MIN_SHARES,step=1)
                        total_cost=price*qty
                        cash_after=my_cash-total_cost if is_buy else my_cash+total_cost

                        st.markdown(f"""
                        <div style='background:linear-gradient(135deg,#111827,#1a2332);
                                    border:1px solid #2a3a50;border-radius:16px;
                                    padding:1.2rem 1.4rem;margin:1rem 0;font-family:JetBrains Mono,monospace;
                                    position:relative;overflow:hidden;'>
                            <div style='position:absolute;top:0;left:0;right:0;height:2px;
                                        background:{"linear-gradient(90deg,#fb7185,#f43f5e)" if is_buy else "linear-gradient(90deg,#34d399,#22d3ee)"};'></div>
                            <div style='display:grid;grid-template-columns:1fr 1fr;gap:.75rem;'>
                                <div>
                                    <div style='font-size:.6rem;color:#64748b;text-transform:uppercase;letter-spacing:.12em;font-weight:600;'>Price / Share</div>
                                    <div style='font-size:1.05rem;color:#f1f5f9;font-weight:700;margin-top:.2rem;'>${price:.2f}</div>
                                </div>
                                <div>
                                    <div style='font-size:.6rem;color:#64748b;text-transform:uppercase;letter-spacing:.12em;font-weight:600;'>Shares</div>
                                    <div style='font-size:1.05rem;color:#f1f5f9;font-weight:700;margin-top:.2rem;'>{qty:,}</div>
                                </div>
                                <div>
                                    <div style='font-size:.6rem;color:#64748b;text-transform:uppercase;letter-spacing:.12em;font-weight:600;'>Total {"Cost" if is_buy else "Proceeds"}</div>
                                    <div style='font-size:1.15rem;color:{"#fb7185" if is_buy else "#34d399"};font-weight:700;margin-top:.2rem;'>${total_cost:,.0f}</div>
                                </div>
                                <div>
                                    <div style='font-size:.6rem;color:#64748b;text-transform:uppercase;letter-spacing:.12em;font-weight:600;'>Cash After</div>
                                    <div style='font-size:1.15rem;color:{"#34d399" if cash_after>=0 else "#fb7185"};font-weight:700;margin-top:.2rem;'>${cash_after:,.0f}</div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        if is_buy and my_cash < total_cost:
                            st.error(f"Insufficient funds. You have ${my_cash:,.0f}")
                        else:
                            # Two-step confirmation
                            confirm_key = f"confirm_trade_{round_num}"
                            if confirm_key not in st.session_state:
                                st.session_state[confirm_key] = False

                            if not st.session_state[confirm_key]:
                                if st.button(
                                    f"{'🟢 BUY' if is_buy else '🔴 SELL'} {qty} shares @ ${price:.2f} = ${total_cost:,.0f}",
                                    type="primary", use_container_width=True
                                ):
                                    st.session_state[confirm_key] = {"is_buy": is_buy, "qty": qty, "price": price, "total": total_cost}
                                    st.rerun()
                            else:
                                pending = st.session_state[confirm_key]
                                st.warning(f"⚠️ Confirm: {'BUY' if pending['is_buy'] else 'SELL'} {pending['qty']} shares @ ${pending['price']:.2f} for ${pending['total']:,.0f}?")
                                col_yes, col_no = st.columns(2)
                                with col_yes:
                                    if st.button("✅ Confirm", type="primary", use_container_width=True):
                                        if pending["is_buy"]:
                                            execute_trade(my_team,market_maker,stock,pending["price"],pending["qty"],round_num)
                                        else:
                                            execute_trade(market_maker,my_team,stock,pending["price"],pending["qty"],round_num)
                                        st.session_state[confirm_key] = False
                                        st.rerun()
                                with col_no:
                                    if st.button("❌ Cancel", use_container_width=True):
                                        st.session_state[confirm_key] = False
                                        st.rerun()

        with right:
            round_trades=get_trade_log(round_num)
            # Filter out PASS entries for display
            real_trades = [t for t in round_trades if t.get("qty", 0) > 0]
            st.markdown(f"""<div style='display:flex;align-items:center;gap:.75rem;margin-bottom:1rem;'>
                <h3 style='font-weight:800;font-size:1.05rem;color:#f1f5f9;margin:0;letter-spacing:-.02em;'>Trades This Round</h3>
                <span style='font-family:JetBrains Mono,monospace;font-size:.7rem;color:#64748b;
                             background:#111827;padding:.15rem .5rem;border-radius:6px;
                             border:1px solid #2a3a50;font-weight:600;'>{len(real_trades)}</span>
            </div>""", unsafe_allow_html=True)
            if real_trades:
                df_t=pd.DataFrame(real_trades)[["buyer","seller","price","qty","executed_at"]]
                df_t.columns=["Buyer","Seller","Price","Qty","Time"]
                df_t["Price"]=df_t["Price"].apply(lambda v:f"${v:.2f}")
                df_t["Time"]=df_t["Time"].apply(lambda v:str(v)[-15:-7] if v else "")
                st.dataframe(df_t,use_container_width=True,hide_index=True)
            else:
                st.markdown("<p style='color:#64748b;font-size:.85rem;'>No trades yet this round.</p>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# REVEAL PHASE
# ══════════════════════════════════════════════════════════════════════════════
elif phase == "reveal":
    true_price=true_prices.get(stock)
    st.markdown(f"""<div class='animate-in' style='margin-bottom:1.5rem;'>
        <h2 style='font-size:1.8rem;font-weight:800;color:#f1f5f9;letter-spacing:-.03em;margin-bottom:.3rem;'>
            🎯 Round {round_num} Results</h2>
        <p style='color:#64748b;font-size:.85rem;'>{stock.upper()} — all positions settled at true price</p>
    </div>""", unsafe_allow_html=True)
    c1,c2,c3=st.columns(3)
    c1.metric("True Price",f"${true_price:.2f}" if true_price else "?")
    c2.metric("Market Maker",market_maker or "—")
    if true_price and market_maker and market_maker in spreads:
        sp=spreads[market_maker]
        c3.metric("MM Edge / Share",f"${((sp['ask']-true_price)+(true_price-sp['bid']))/2:.2f}")
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("✅ All positions have been settled to cash at the true price.")
    rows=[]
    for t,s in spreads.items():
        inside=(s["bid"]<=true_price<=s["ask"]) if true_price else None
        rows.append({"Team":t,"Bid":f"${s['bid']:.2f}","Ask":f"${s['ask']:.2f}",
                     "Spread":f"${s['ask']-s['bid']:.2f}",
                     "Hit?":"✅ Yes" if inside else ("❌ No" if inside is False else "?"),
                     "MM":"🏦" if t==market_maker else "",
                     "You":"👈" if t==my_team else ""})
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# LEADERBOARD
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""<div style='display:flex;align-items:center;gap:1rem;margin-bottom:1.2rem;'>
    <span style='font-size:1.4rem;font-weight:800;color:#f1f5f9;letter-spacing:-.02em;'>🏆 Live Leaderboard</span>
    <span class='glow-pulse' style='display:inline-flex;align-items:center;gap:.4rem;background:#111827;
                 border:1px solid #2a3a50;border-radius:20px;padding:.2rem .7rem;
                 font-family:JetBrains Mono,monospace;font-size:.6rem;color:#64748b;font-weight:600;'>
        <span style='width:6px;height:6px;border-radius:50%;background:#22d3ee;
                     display:inline-block;box-shadow:0 0 8px #22d3ee;'></span>LIVE
    </span>
</div>""", unsafe_allow_html=True)

if teams:
    rows=[]
    for name in teams:
        cash=teams[name]["cash"]
        pnl=cash-STARTING_BUDGET
        rows.append({
            "":          "🏦" if name==market_maker else "",
            "Team":      name,
            "Cash":      f"${cash:,.0f}",
            "P&L":       f"${pnl:+,.0f}",
            "You":       "👈" if name==my_team else "",
            "_sort_cash": cash,
        })
    lb=sorted(rows,key=lambda r:r["_sort_cash"],reverse=True)
    lb_df=pd.DataFrame(lb).drop(columns=["_sort_cash"]).reset_index(drop=True); lb_df.index+=1
    st.dataframe(lb_df,use_container_width=True)

    history=get_round_history()
    if history:
        # ── P&L chart over rounds ──
        hist_df = pd.DataFrame(history)
        if "round" in hist_df.columns and len(hist_df) > 0:
            chart_data = {"Round": [0], **{n: [0] for n in teams}}
            # Reconstruct running P&L from trade log per round
            all_trades_data = get_trade_log()
            cumulative = {n: 0.0 for n in teams}
            for h in history:
                rnd_num = h["round"]
                rnd_tp  = h.get("true_price", 0) or 0
                # Tally cash changes from trades in this round
                for t in all_trades_data:
                    if t["round"] == rnd_num and t["qty"] > 0:
                        cost = t["price"] * t["qty"]
                        cumulative[t["buyer"]]  -= cost
                        cumulative[t["seller"]] += cost
                        # Settlement at true price
                        cumulative[t["buyer"]]  += t["qty"] * rnd_tp
                        cumulative[t["seller"]] -= t["qty"] * rnd_tp
                chart_data["Round"].append(rnd_num)
                for n in teams:
                    chart_data[n].append(round(cumulative[n], 2))
            chart_df = pd.DataFrame(chart_data).set_index("Round")
            with st.expander("📈 P&L Over Rounds", expanded=True):
                st.line_chart(chart_df, use_container_width=True)

        with st.expander("📋 Round History"):
            st.dataframe(hist_df,use_container_width=True,hide_index=True)
    all_trades=get_trade_log()
    if all_trades:
        with st.expander("📜 Full Trade Log"):
            df_all=pd.DataFrame(all_trades)[["round","stock","buyer","seller","price","qty","executed_at"]]
            df_all.columns=["Round","Stock","Buyer","Seller","Price","Qty","Time"]
            df_all["Price"]=df_all["Price"].apply(lambda v:f"${v:.2f}")
            st.dataframe(df_all,use_container_width=True,hide_index=True)
else:
    st.info("No teams registered yet.")

if phase in ("submit","trade") and not game_over and not is_admin:
    st.markdown("""
    <div style='text-align:center;margin-top:1.5rem;padding:.6rem;'>
        <div style='display:inline-flex;align-items:center;gap:.5rem;
                    background:#111827;border:1px solid #2a3a50;border-radius:20px;
                    padding:.3rem .9rem;'>
            <span style='width:5px;height:5px;border-radius:50%;background:#22d3ee;
                         display:inline-block;animation:pulse-glow 2s ease-in-out infinite;'></span>
            <span style='font-family:JetBrains Mono,monospace;font-size:.6rem;color:#64748b;font-weight:500;'>
                Auto-refreshing every 8s
            </span>
        </div>
    </div>
    <meta http-equiv="refresh" content="8">
    """, unsafe_allow_html=True)