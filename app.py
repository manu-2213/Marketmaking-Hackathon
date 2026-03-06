import streamlit as st
import pandas as pd
import uuid
from supabase import create_client, Client

st.set_page_config(
    page_title="Market Making Hackathon",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;700;800&display=swap');
:root {
    --bg:#07090f; --surface:#0f1520; --surface2:#161f2e; --surface3:#1c2a3e;
    --border:#253347; --accent:#00ffaa; --accent2:#38bdf8; --accent3:#818cf8;
    --danger:#f87171; --warn:#fbbf24; --green:#4ade80;
    --text:#f1f5f9; --muted:#7a90a8; --mm:#c084fc;
}
html,body,[data-testid="stAppViewContainer"]{
    background:var(--bg)!important;color:var(--text)!important;
    font-family:'Syne',sans-serif!important;
}
[data-testid="stAppViewContainer"]{
    background:
        radial-gradient(ellipse 90% 45% at 50% -10%,rgba(0,255,170,.06) 0%,transparent 65%),
        radial-gradient(ellipse 55% 35% at 90% 90%,rgba(56,189,248,.05) 0%,transparent 55%),
        var(--bg)!important;
}
[data-testid="stSidebar"]{
    background:var(--surface)!important;
    border-right:1px solid var(--border)!important;
}
#MainMenu,footer,header{visibility:hidden;}
[data-testid="stDecoration"]{display:none;}
h1,h2,h3,h4{font-family:'Syne',sans-serif!important;letter-spacing:-.02em;color:var(--text)!important;}

/* Metrics */
[data-testid="stMetric"]{
    background:var(--surface2)!important;
    border:1px solid var(--border)!important;
    border-radius:12px!important;padding:1.1rem 1.25rem!important;
}
[data-testid="stMetricLabel"]{color:#94a3b8!important;font-size:.72rem!important;text-transform:uppercase;letter-spacing:.12em;font-weight:600;}
[data-testid="stMetricValue"]{color:var(--accent)!important;font-family:'Space Mono',monospace!important;font-size:1.5rem!important;font-weight:700;}

/* Buttons */
[data-testid="stButton"]>button{
    background:var(--surface2)!important;border:1px solid var(--border)!important;
    color:var(--text)!important;font-family:'Syne',sans-serif!important;
    font-weight:700!important;border-radius:9px!important;transition:all .18s!important;
    font-size:.9rem!important;
}
[data-testid="stButton"]>button:hover{
    border-color:var(--accent)!important;color:var(--accent)!important;
    background:rgba(0,255,170,.07)!important;box-shadow:0 0 20px rgba(0,255,170,.12)!important;
}
button[kind="primary"]{
    background:var(--accent)!important;border-color:var(--accent)!important;
    color:#020c0a!important;font-weight:800!important;
}
button[kind="primary"]:hover{
    background:#00e699!important;border-color:#00e699!important;color:#020c0a!important;
    box-shadow:0 0 28px rgba(0,255,170,.35)!important;
}

/* Inputs */
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input{
    background:var(--surface3)!important;border:1px solid var(--border)!important;
    color:var(--text)!important;border-radius:9px!important;
    font-family:'Space Mono',monospace!important;font-size:.95rem!important;
}
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextInput"] input:focus{
    border-color:var(--accent)!important;box-shadow:0 0 0 2px rgba(0,255,170,.15)!important;
}
[data-testid="stSelectbox"]>div>div{
    background:var(--surface3)!important;border:1px solid var(--border)!important;
    border-radius:9px!important;color:var(--text)!important;
}
div[data-baseweb="select"] span{color:var(--text)!important;}

/* DataFrames */
[data-testid="stDataFrame"]{border:1px solid var(--border)!important;border-radius:12px!important;overflow:hidden!important;}
[data-testid="stDataFrame"] th{background:var(--surface2)!important;color:#94a3b8!important;font-size:.7rem!important;text-transform:uppercase;letter-spacing:.1em;}
[data-testid="stDataFrame"] td{color:var(--text)!important;font-family:'Space Mono',monospace!important;font-size:.82rem!important;}

/* Progress */
[data-testid="stProgressBar"]>div>div{background:linear-gradient(90deg,var(--accent),var(--accent2))!important;border-radius:4px!important;}
[data-testid="stProgressBar"]>div{background:var(--surface2)!important;border-radius:4px!important;}

/* Alerts */
[data-testid="stAlert"]{border-radius:10px!important;border-width:0 0 0 3px!important;}
[data-testid="stAlert"][data-type="info"]{background:rgba(56,189,248,.08)!important;border-color:var(--accent2)!important;color:#bae6fd!important;}
[data-testid="stAlert"][data-type="success"]{background:rgba(74,222,128,.08)!important;border-color:var(--green)!important;color:#bbf7d0!important;}
[data-testid="stAlert"][data-type="warning"]{background:rgba(251,191,36,.08)!important;border-color:var(--warn)!important;color:#fde68a!important;}
[data-testid="stAlert"][data-type="error"]{background:rgba(248,113,113,.08)!important;border-color:var(--danger)!important;color:#fecaca!important;}

/* Tabs */
[data-testid="stTabs"] [data-baseweb="tab-list"]{background:var(--surface)!important;border-bottom:1px solid var(--border)!important;gap:.5rem;}
[data-testid="stTabs"] [data-baseweb="tab"]{color:var(--muted)!important;font-family:'Syne',sans-serif!important;font-weight:600!important;border-radius:8px 8px 0 0!important;}
[data-testid="stTabs"] [aria-selected="true"]{color:var(--accent)!important;border-bottom:2px solid var(--accent)!important;}

/* Radio */
[data-testid="stRadio"] label{color:var(--text)!important;font-weight:600;}

/* Expander */
[data-testid="stExpander"]{border:1px solid var(--border)!important;border-radius:11px!important;background:var(--surface)!important;}
[data-testid="stExpander"] summary{color:var(--text)!important;font-weight:600;}

/* Divider */
hr{border-color:var(--border)!important;opacity:1!important;}

/* Caption */
[data-testid="stCaptionContainer"]{color:var(--muted)!important;font-family:'Space Mono',monospace!important;font-size:.68rem!important;}

/* Scrollbar */
::-webkit-scrollbar{width:4px;height:4px;}
::-webkit-scrollbar-track{background:var(--bg);}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px;}
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
    <div style='text-align:center;padding:4rem 0 1.5rem'>
        <div style='font-family:Space Mono,monospace;font-size:.7rem;letter-spacing:.35em;
                    color:#00ffaa;text-transform:uppercase;margin-bottom:.75rem;'>
            HACKATHON 2025
        </div>
        <h1 style='font-size:3.8rem;font-weight:800;letter-spacing:-.04em;margin:0;
                   background:linear-gradient(135deg,#f1f5f9 20%,#7a90a8 100%);
                   -webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1.1;'>
            Market Making<br>Challenge
        </h1>
        <p style='color:#7a90a8;margin-top:1.25rem;font-size:1rem;letter-spacing:.02em;'>
            9 stocks &nbsp;·&nbsp; 9 rounds &nbsp;·&nbsp; tightest spread wins
        </p>
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
        st.markdown("""<div style='padding:.5rem 0 .25rem'>
            <div style='font-size:.6rem;letter-spacing:.25em;color:#00ffaa;text-transform:uppercase;'>Role</div>
            <div style='font-size:1.25rem;font-weight:800;color:#f1f5f9;'>🔧 Admin</div>
        </div>""", unsafe_allow_html=True)
        if st.button("🚪 Sign out", use_container_width=True):
            st.session_state["is_admin"]=False; st.rerun()
    else:
        st.markdown(f"""<div style='padding:.5rem 0 .25rem'>
            <div style='font-size:.6rem;letter-spacing:.25em;color:#00ffaa;text-transform:uppercase;'>Playing as</div>
            <div style='font-size:1.25rem;font-weight:800;color:#f1f5f9;'>{my_team}</div>
        </div>""", unsafe_allow_html=True)
        if teams and my_team in teams:
            cash = teams[my_team]["cash"]
            st.markdown(f"""<div style='background:#0f1520;border:1px solid #253347;border-radius:10px;
                padding:.75rem 1rem;margin:.5rem 0;font-family:Space Mono,monospace;'>
                <div style='font-size:.6rem;color:#7a90a8;text-transform:uppercase;letter-spacing:.1em;'>Cash balance</div>
                <div style='font-size:1.1rem;font-weight:700;color:{"#4ade80" if cash>=0 else "#f87171"};margin-top:.2rem;'>${cash:,.0f}</div>
            </div>""", unsafe_allow_html=True)
        if st.button("🚪 Leave team", use_container_width=True):
            release_team(my_team); st.session_state["claimed_team"]=None; st.rerun()
    st.markdown("---")
    st.markdown(f"""<div style='font-family:Space Mono,monospace;font-size:.72rem;color:#7a90a8;line-height:1.8;'>
        Round &nbsp;&nbsp;<span style='color:#f1f5f9;font-weight:700;'>{round_num} / {TOTAL_ROUNDS}</span><br>
        Stock &nbsp;&nbsp;<span style='color:#00ffaa;font-weight:700;'>{stock.upper()}</span><br>
        Phase &nbsp;&nbsp;<span style='color:#fbbf24;font-weight:700;'>{phase.upper()}</span>
    </div>""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
identity_label = "🔧 Admin" if is_admin else f"🏷 {my_team}"
st.markdown(f"""
<div style='display:flex;justify-content:space-between;align-items:center;
            padding:.65rem 1.25rem;background:rgba(15,21,32,.95);
            border:1px solid #253347;border-radius:12px;margin-bottom:1.75rem;
            backdrop-filter:blur(12px);'>
    <div style='display:flex;align-items:center;gap:1.75rem;'>
        <span style='font-family:Space Mono,monospace;font-size:.8rem;color:#00ffaa;
                     letter-spacing:.12em;font-weight:700;'>📈 MARKET MAKING</span>
        <span style='color:#253347;font-size:1.2rem;'>|</span>
        <span style='font-family:Space Mono,monospace;font-size:.75rem;color:#94a3b8;'>
            <span style='color:#c084fc;font-weight:700;'>{stock.upper()}</span>
            &nbsp;·&nbsp; RD {round_num}/{TOTAL_ROUNDS}
            &nbsp;·&nbsp; <span style='color:#fbbf24;'>{phase.upper()}</span>
        </span>
    </div>
    <span style='font-family:Space Mono,monospace;font-size:.75rem;color:#94a3b8;
                 background:#161f2e;padding:.3rem .75rem;border-radius:20px;
                 border:1px solid #253347;'>{identity_label}</span>
</div>
""", unsafe_allow_html=True)

# ── Game over ──────────────────────────────────────────────────────────────────
if game_over:
    st.balloons()
    st.markdown("""<h1 style='text-align:center;font-size:3.2rem;font-weight:800;
        background:linear-gradient(135deg,#00ffaa,#38bdf8);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:2rem;'>
        🏁 Final Results</h1>""", unsafe_allow_html=True)
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
    st.markdown("""<div style='background:rgba(192,132,252,.05);border:1px solid rgba(192,132,252,.2);
        border-radius:14px;padding:1rem 1.5rem .5rem;margin-bottom:1.5rem;'>
        <div style='font-size:.65rem;letter-spacing:.25em;color:#c084fc;text-transform:uppercase;
                    font-weight:700;margin-bottom:.75rem;'>🔧 Admin Control Panel</div>
    </div>""", unsafe_allow_html=True)

    tab_teams, tab_phase, tab_danger = st.tabs(["👥 Teams", "⚙️ Phase Controls", "⚠️ Reset"])

    with tab_teams:
        c1,c2 = st.columns([1,2])
        with c1:
            new_team = st.text_input("", placeholder="Team name…", label_visibility="collapsed")
            if st.button("➕ Add Team", type="primary", use_container_width=True):
                if new_team.strip():
                    if new_team.strip() not in teams: add_team(new_team.strip()); st.rerun()
                    else: st.warning("Already exists")
                else: st.warning("Enter a name")
        with c2:
            if teams:
                rows=[{"Team":t,"Status":"🟢 Online" if t in sessions else "⚪ Not joined",
                       "Cash":f"${teams[t]['cash']:,.0f}"} for t in sorted(teams.keys())]
                st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
            else:
                st.info("No teams yet.")
        if sessions:
            st.markdown("**Release a slot:**")
            rc1,rc2=st.columns([2,1])
            with rc1: to_rel=st.selectbox("",sorted(sessions.keys()),label_visibility="collapsed")
            with rc2:
                if st.button("🔓 Release",use_container_width=True): release_team(to_rel); st.rerun()
        if teams:
            st.markdown("---")
            if st.button("🗑 Remove All Teams",use_container_width=True): delete_all_teams(); st.rerun()

    with tab_phase:
        st.markdown(f"""<div style='background:#0f1520;border:1px solid #253347;border-radius:10px;
            padding:.9rem 1.1rem;margin-bottom:1rem;font-family:Space Mono,monospace;font-size:.8rem;line-height:2;'>
            Round &nbsp;<b style='color:#00ffaa;'>{round_num}</b> &nbsp;·&nbsp;
            Stock &nbsp;<b style='color:#c084fc;'>{stock.upper()}</b> &nbsp;·&nbsp;
            Phase &nbsp;<b style='color:#fbbf24;'>{phase.upper()}</b><br>
            Spreads in: &nbsp;<b style='color:#f1f5f9;'>{len(spreads)} / {len(teams)}</b>
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
            st.success(f"Market Maker: **{market_maker}**")
            st.markdown(f"Trades executed: **{len(round_trades)}**")
            if round_trades:
                df_t=pd.DataFrame(round_trades)[["buyer","seller","price","qty","executed_at"]]
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
            st.markdown("""<h2 style='font-size:1.9rem;font-weight:800;margin-bottom:.3rem;
                color:#f1f5f9;'>Submit Your Spread</h2>
                <p style='color:#7a90a8;margin-bottom:1.5rem;font-size:.92rem;'>
                Tightest bid-ask spread = market maker this round.</p>""", unsafe_allow_html=True)
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
                st.markdown(f"""<div style='background:rgba(0,255,170,.06);
                    border:1px solid rgba(0,255,170,.25);border-radius:10px;
                    padding:.8rem 1rem;margin:.6rem 0;font-family:Space Mono,monospace;'>
                    <span style='color:#7a90a8;font-size:.75rem;'>SPREAD WIDTH</span><br>
                    <span style='color:#00ffaa;font-size:1.2rem;font-weight:700;'>${spread_w:.2f}</span>
                    {"&nbsp;&nbsp;<span style='color:#fbbf24;font-size:.75rem;'>✅ SUBMITTED — resubmit to update</span>" if already else ""}
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
    <div style='background:linear-gradient(135deg,rgba(192,132,252,.1),rgba(56,189,248,.07));
                border:1px solid rgba(192,132,252,.3);border-radius:16px;
                padding:1.4rem 1.75rem;margin-bottom:1.75rem;'>
        <div style='font-size:.65rem;letter-spacing:.25em;color:#c084fc;text-transform:uppercase;
                    font-weight:700;margin-bottom:.6rem;'>🏦 Market Maker This Round</div>
        <div style='font-size:2.1rem;font-weight:800;color:#f1f5f9;margin-bottom:.9rem;'>{market_maker}</div>
        <div style='display:flex;gap:2.5rem;'>
            <div>
                <div style='font-size:.65rem;color:#7a90a8;text-transform:uppercase;letter-spacing:.1em;margin-bottom:.2rem;'>BID (sells to MM)</div>
                <div style='font-family:Space Mono,monospace;font-size:1.4rem;font-weight:700;color:#4ade80;'>${mm_bid:.2f}</div>
            </div>
            <div>
                <div style='font-size:.65rem;color:#7a90a8;text-transform:uppercase;letter-spacing:.1em;margin-bottom:.2rem;'>ASK (buys from MM)</div>
                <div style='font-family:Space Mono,monospace;font-size:1.4rem;font-weight:700;color:#38bdf8;'>${mm_ask:.2f}</div>
            </div>
            <div>
                <div style='font-size:.65rem;color:#7a90a8;text-transform:uppercase;letter-spacing:.1em;margin-bottom:.2rem;'>SPREAD</div>
                <div style='font-family:Space Mono,monospace;font-size:1.4rem;font-weight:700;color:#fbbf24;'>${mm_ask-mm_bid:.2f}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not is_admin:
        left,right=st.columns([1,1],gap="large")
        with left:
            if is_mm:
                st.markdown("""<div style='background:rgba(192,132,252,.08);
                    border:1px solid rgba(192,132,252,.25);border-radius:14px;
                    padding:1.5rem;text-align:center;'>
                    <div style='font-size:2.5rem;margin-bottom:.75rem;'>🏦</div>
                    <div style='font-weight:800;font-size:1.2rem;color:#c084fc;'>You are the Market Maker</div>
                    <div style='color:#7a90a8;font-size:.88rem;margin-top:.6rem;line-height:1.6;'>
                        You must fill every trade placed against you.<br>
                        You can go negative. Positions settle at true price.
                    </div>
                </div>""", unsafe_allow_html=True)
            else:
                # Check if already traded
                already_traded = has_traded_this_round(my_team, round_num)
                my_cash = teams[my_team]["cash"]

                st.markdown(f"""<h3 style='font-weight:800;font-size:1.3rem;margin-bottom:1rem;
                    color:#f1f5f9;'>Your Trade Decision</h3>""", unsafe_allow_html=True)

                if already_traded:
                    st.warning("✅ You've already placed your trade this round. Wait for the reveal.")
                else:
                    action=st.radio("Direction",["🟢 BUY shares (at ask)","🔴 SELL shares (at bid)"],horizontal=True)
                    is_buy="BUY" in action
                    price=mm_ask if is_buy else mm_bid
                    max_qty=int(my_cash//price) if is_buy else 999
                    qty=st.number_input("Number of shares",min_value=1,max_value=max(1,max_qty),value=1,step=1)
                    total_cost=price*qty
                    cash_after=my_cash-total_cost if is_buy else my_cash+total_cost

                    st.markdown(f"""
                    <div style='background:#0f1520;border:1px solid #253347;border-radius:12px;
                                padding:1.1rem 1.25rem;margin:1rem 0;font-family:Space Mono,monospace;'>
                        <div style='display:grid;grid-template-columns:1fr 1fr;gap:.6rem;'>
                            <div>
                                <div style='font-size:.65rem;color:#7a90a8;text-transform:uppercase;letter-spacing:.1em;'>Price per share</div>
                                <div style='font-size:1rem;color:#f1f5f9;font-weight:700;margin-top:.2rem;'>${price:.2f}</div>
                            </div>
                            <div>
                                <div style='font-size:.65rem;color:#7a90a8;text-transform:uppercase;letter-spacing:.1em;'>Shares</div>
                                <div style='font-size:1rem;color:#f1f5f9;font-weight:700;margin-top:.2rem;'>{qty:,}</div>
                            </div>
                            <div>
                                <div style='font-size:.65rem;color:#7a90a8;text-transform:uppercase;letter-spacing:.1em;'>Total {"cost" if is_buy else "proceeds"}</div>
                                <div style='font-size:1.1rem;color:{"#f87171" if is_buy else "#4ade80"};font-weight:700;margin-top:.2rem;'>${total_cost:,.0f}</div>
                            </div>
                            <div>
                                <div style='font-size:.65rem;color:#7a90a8;text-transform:uppercase;letter-spacing:.1em;'>Cash after trade</div>
                                <div style='font-size:1.1rem;color:{"#4ade80" if cash_after>=0 else "#f87171"};font-weight:700;margin-top:.2rem;'>${cash_after:,.0f}</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if is_buy and my_cash < total_cost:
                        st.error(f"Insufficient funds. You have ${my_cash:,.0f}")
                    else:
                        btn_col1, btn_col2 = st.columns([3,1])
                        with btn_col1:
                            if st.button(
                                f"{'🟢 BUY' if is_buy else '🔴 SELL'} {qty} shares @ ${price:.2f} = ${total_cost:,.0f}",
                                type="primary", use_container_width=True
                            ):
                                if is_buy:
                                    execute_trade(my_team,market_maker,stock,price,qty,round_num)
                                    st.success(f"Bought {qty} shares @ ${price:.2f} | Total: ${total_cost:,.0f}")
                                else:
                                    execute_trade(market_maker,my_team,stock,price,qty,round_num)
                                    st.success(f"Sold {qty} shares @ ${price:.2f} | Proceeds: ${total_cost:,.0f}")
                                st.rerun()

        with right:
            round_trades=get_trade_log(round_num)
            st.markdown(f"""<h3 style='font-weight:800;font-size:1.1rem;margin-bottom:1rem;color:#f1f5f9;'>
                Trades This Round
                <span style='font-family:Space Mono,monospace;font-size:.8rem;color:#7a90a8;
                             font-weight:400;margin-left:.5rem;'>({len(round_trades)})</span>
            </h3>""", unsafe_allow_html=True)
            if round_trades:
                df_t=pd.DataFrame(round_trades)[["buyer","seller","price","qty","executed_at"]]
                df_t.columns=["Buyer","Seller","Price","Qty","Time"]
                df_t["Price"]=df_t["Price"].apply(lambda v:f"${v:.2f}")
                df_t["Time"]=df_t["Time"].apply(lambda v:str(v)[-15:-7] if v else "")
                st.dataframe(df_t,use_container_width=True,hide_index=True)
            else:
                st.markdown("<p style='color:#7a90a8;font-size:.9rem;'>No trades yet this round.</p>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# REVEAL PHASE
# ══════════════════════════════════════════════════════════════════════════════
elif phase == "reveal":
    true_price=true_prices.get(stock)
    st.markdown(f"""<h2 style='font-size:1.9rem;font-weight:800;margin-bottom:1.5rem;color:#f1f5f9;'>
        🎯 Round {round_num} Results — {stock.upper()}</h2>""", unsafe_allow_html=True)
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
st.markdown("""<div style='display:flex;align-items:center;gap:.9rem;margin-bottom:1.1rem;'>
    <span style='font-size:1.5rem;font-weight:800;color:#f1f5f9;'>🏆 Live Leaderboard</span>
    <span style='display:inline-flex;align-items:center;gap:.4rem;background:#0f1520;
                 border:1px solid #253347;border-radius:20px;padding:.2rem .65rem;
                 font-family:Space Mono,monospace;font-size:.65rem;color:#7a90a8;'>
        <span style='width:6px;height:6px;border-radius:50%;background:#00ffaa;
                     display:inline-block;box-shadow:0 0 8px #00ffaa;'></span>LIVE
    </span>
</div>""", unsafe_allow_html=True)

if teams:
    rows=[]
    for name in teams:
        # After settle, all P&L is in cash
        cash=teams[name]["cash"]
        pnl=cash-STARTING_BUDGET
        rows.append({
            "":          "🏦" if name==market_maker else "",
            "Team":      name,
            "Cash":      f"${cash:,.0f}",
            "P&L":       f"${pnl:+,.0f}",
            "You":       "👈" if name==my_team else "",
        })
    lb=sorted(rows,key=lambda r:float(r["Cash"].replace("$","").replace(",","")),reverse=True)
    lb_df=pd.DataFrame(lb).reset_index(drop=True); lb_df.index+=1
    st.dataframe(lb_df,use_container_width=True)

    history=get_round_history()
    if history:
        with st.expander("📋 Round History"):
            st.dataframe(pd.DataFrame(history),use_container_width=True,hide_index=True)
    all_trades=get_trade_log()
    if all_trades:
        with st.expander("📜 Full Trade Log"):
            df_all=pd.DataFrame(all_trades)[["round","stock","buyer","seller","price","qty","executed_at"]]
            df_all.columns=["Round","Stock","Buyer","Seller","Price","Qty","Time"]
            df_all["Price"]=df_all["Price"].apply(lambda v:f"${v:.2f}")
            st.dataframe(df_all,use_container_width=True,hide_index=True)
else:
    st.info("No teams registered yet.")

if phase in ("submit","trade") and not game_over:
    st.caption("⟳ Auto-refreshing every 6s")
    import time; time.sleep(6); st.rerun()