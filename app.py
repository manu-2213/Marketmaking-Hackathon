import streamlit as st
import pandas as pd
import uuid
from supabase import create_client, Client

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Market Making Hackathon",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;700;800&display=swap');

:root {
    --bg:        #0a0e1a;
    --surface:   #111827;
    --surface2:  #1a2235;
    --border:    #1e2d45;
    --accent:    #00ff9d;
    --accent2:   #0ea5e9;
    --danger:    #ff4d6d;
    --warn:      #fbbf24;
    --text:      #e2e8f0;
    --muted:     #64748b;
    --mm:        #a78bfa;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Syne', sans-serif !important;
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(ellipse 80% 50% at 50% -20%, rgba(0,255,157,0.07) 0%, transparent 70%),
        radial-gradient(ellipse 60% 40% at 80% 80%, rgba(14,165,233,0.05) 0%, transparent 60%),
        var(--bg) !important;
}

[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}

/* Hide default streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

/* Typography */
h1, h2, h3 { font-family: 'Syne', sans-serif !important; letter-spacing: -0.02em; }
code, .mono { font-family: 'Space Mono', monospace !important; }

/* Metric cards */
[data-testid="stMetric"] {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 1rem 1.25rem !important;
}
[data-testid="stMetricLabel"] { color: var(--muted) !important; font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 0.1em; }
[data-testid="stMetricValue"] { color: var(--accent) !important; font-family: 'Space Mono', monospace !important; font-size: 1.4rem !important; }

/* Buttons */
[data-testid="stButton"] > button {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    transition: all 0.2s !important;
}
[data-testid="stButton"] > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    box-shadow: 0 0 16px rgba(0,255,157,0.15) !important;
}
[data-testid="stButton"][data-baseweb] > button[kind="primary"],
button[kind="primary"] {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
    color: #000 !important;
}

/* Inputs */
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] > div {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 8px !important;
    font-family: 'Space Mono', monospace !important;
}

/* DataFrames */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* Progress bar */
[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, var(--accent), var(--accent2)) !important;
}

/* Alerts */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    border-left: 3px solid var(--accent) !important;
    background: rgba(0,255,157,0.05) !important;
}

/* Divider */
hr { border-color: var(--border) !important; }

/* Expander */
[data-testid="stExpander"] {
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    background: var(--surface) !important;
}

/* Caption */
[data-testid="stCaptionContainer"] { color: var(--muted) !important; font-family: 'Space Mono', monospace !important; font-size: 0.7rem !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

</style>
""", unsafe_allow_html=True)

# ── Session identity ───────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())
SESSION_ID = st.session_state["session_id"]

if "claimed_team" not in st.session_state:
    st.session_state["claimed_team"] = None
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False

# ── Constants ──────────────────────────────────────────────────────────────────
STARTING_BUDGET = 100_000
STOCKS          = [f"stock_{i}" for i in range(1, 10)]
TOTAL_ROUNDS    = 9
ADMIN_PASSWORD  = "admin123"

# ── Supabase ───────────────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

sb = get_supabase()

# ── DB helpers ─────────────────────────────────────────────────────────────────
def get_game_state():
    return sb.table("game_state").select("*").eq("id", 1).single().execute().data

def set_game_state(**kwargs):
    sb.table("game_state").update(kwargs).eq("id", 1).execute()

def get_teams():
    r = sb.table("teams").select("*").execute()
    return {row["name"]: row for row in r.data}

def add_team(name):
    sb.table("teams").insert({"name": name, "cash": STARTING_BUDGET}).execute()

def delete_all_teams():
    sb.table("team_sessions").delete().neq("team", "").execute()
    sb.table("teams").delete().neq("name", "").execute()

def get_sessions():
    r = sb.table("team_sessions").select("*").execute()
    return {row["team"]: row["session_id"] for row in r.data}

def claim_team(team, session_id):
    existing = sb.table("team_sessions").select("*").eq("team", team).execute()
    if existing.data:
        return existing.data[0]["session_id"] == session_id
    sb.table("team_sessions").insert({"team": team, "session_id": session_id}).execute()
    return True

def release_team(team):
    sb.table("team_sessions").delete().eq("team", team).execute()

def get_positions():
    return sb.table("positions").select("*").execute().data

def upsert_position(team, stock, qty_delta, cost_delta):
    r = sb.table("positions").select("*").eq("team", team).eq("stock", stock).execute()
    if r.data:
        row = r.data[0]
        sb.table("positions").update({
            "qty":        row["qty"] + qty_delta,
            "cost_basis": row["cost_basis"] + cost_delta,
        }).eq("id", row["id"]).execute()
    else:
        sb.table("positions").insert({
            "team": team, "stock": stock, "qty": qty_delta, "cost_basis": cost_delta,
        }).execute()

def update_cash(team, delta):
    teams = get_teams()
    sb.table("teams").update({"cash": teams[team]["cash"] + delta}).eq("name", team).execute()

def get_spreads(round_num):
    r = sb.table("spreads").select("*").eq("round", round_num).execute()
    return {row["team"]: row for row in r.data}

def upsert_spread(round_num, team, bid, ask):
    sb.table("spreads").upsert({"round": round_num, "team": team, "bid": bid, "ask": ask},
                               on_conflict="round,team").execute()

def get_true_prices():
    r = sb.table("true_prices").select("*").execute()
    return {row["stock"]: row["price"] for row in r.data}

def set_true_price(stock, price):
    sb.table("true_prices").upsert({"stock": stock, "price": price}).execute()

def get_trade_log(round_num=None):
    q = sb.table("trade_log").select("*").order("executed_at")
    if round_num:
        q = q.eq("round", round_num)
    return q.execute().data

def log_trade(round_num, stock, buyer, seller, price, qty=1):
    sb.table("trade_log").insert({
        "round": round_num, "stock": stock,
        "buyer": buyer, "seller": seller, "price": price, "qty": qty,
    }).execute()

def get_round_history():
    return sb.table("round_history").select("*").order("round").execute().data

def log_round(round_num, stock, mm, true_price):
    sb.table("round_history").upsert({
        "round": round_num, "stock": stock,
        "market_maker": mm, "true_price": true_price,
    }).execute()

def reset_game():
    for tbl, col in [("trade_log","id"), ("round_history","round"), ("spreads","id"),
                     ("true_prices","stock"), ("positions","id"), ("team_sessions","team"), ("teams","name")]:
        sb.table(tbl).delete().neq(col, "" if col in ("stock","team","name") else 0).execute()
    sb.table("game_state").update({
        "round": 1, "phase": "submit", "market_maker": None, "game_over": False,
    }).eq("id", 1).execute()

# ── Business logic ─────────────────────────────────────────────────────────────
def find_market_maker(spreads):
    if not spreads:
        return None
    return min(spreads, key=lambda t: (spreads[t]["ask"] - spreads[t]["bid"], t))

def execute_trade(buyer, seller, stock, price, round_num):
    update_cash(buyer,  -price)
    update_cash(seller, +price)
    upsert_position(buyer,  stock, +1, +price)
    upsert_position(seller, stock, -1, -price)
    log_trade(round_num, stock, buyer, seller, price)

def portfolio_value(name, teams, positions, true_prices):
    cash = teams[name]["cash"]
    return cash + sum(p["qty"] * true_prices[p["stock"]]
                      for p in positions
                      if p["team"] == name and p["stock"] in true_prices)

def unrealised_pnl(name, positions, true_prices):
    return sum(p["qty"] * true_prices[p["stock"]] - p["cost_basis"]
               for p in positions
               if p["team"] == name and p["stock"] in true_prices and p["qty"] != 0)

# ── Load state ─────────────────────────────────────────────────────────────────
gs           = get_game_state()
round_num    = gs["round"]
phase        = gs["phase"]
market_maker = gs["market_maker"]
game_over    = gs["game_over"]
stock        = STOCKS[round_num - 1]

teams       = get_teams()
sessions    = get_sessions()
spreads     = get_spreads(round_num)
true_prices = get_true_prices()
positions   = get_positions()

# ── Resolve identity ───────────────────────────────────────────────────────────
my_team  = st.session_state["claimed_team"]
is_admin = st.session_state["is_admin"]

# Re-hydrate from DB on new page load
if not is_admin and my_team is None:
    for team, sid in sessions.items():
        if sid == SESSION_ID:
            my_team = team
            st.session_state["claimed_team"] = team
            break

# ══════════════════════════════════════════════════════════════════════════════
# LOGIN GATE — shown when neither admin nor team claimed
# ══════════════════════════════════════════════════════════════════════════════
if not is_admin and my_team is None:

    st.markdown("""
    <div style='text-align:center; padding: 3rem 0 1rem'>
        <div style='font-family:Space Mono,monospace; font-size:0.75rem; letter-spacing:0.3em;
                    color:#00ff9d; text-transform:uppercase; margin-bottom:0.5rem;'>
            HACKATHON 2025
        </div>
        <h1 style='font-size:3.5rem; font-weight:800; letter-spacing:-0.03em; margin:0;
                   background: linear-gradient(135deg, #e2e8f0 0%, #94a3b8 100%);
                   -webkit-background-clip:text; -webkit-text-fill-color:transparent;'>
            Market Making<br>Challenge
        </h1>
        <p style='color:#64748b; margin-top:1rem; font-size:1rem;'>
            9 stocks · 9 rounds · tightest spread wins
        </p>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1, 2, 1])[1]
    with col:
        st.markdown("<br>", unsafe_allow_html=True)
        login_mode = st.radio("I am a", ["Team", "Organiser / Admin"],
                              horizontal=True, label_visibility="visible")

        if login_mode == "Organiser / Admin":
            pwd = st.text_input("Admin password", type="password", placeholder="Enter password…")
            if st.button("Enter as Admin", type="primary", use_container_width=True):
                if pwd == ADMIN_PASSWORD:
                    st.session_state["is_admin"] = True
                    st.rerun()
                else:
                    st.error("Incorrect password")
        else:
            claimed_teams = set(sessions.keys())
            available     = [t for t in sorted(teams.keys()) if t not in claimed_teams]

            if not teams:
                st.info("Waiting for the organiser to register teams.")
            elif not available:
                st.warning("All teams are claimed. Ask the organiser.")
            else:
                chosen = st.selectbox("Select your team", available,
                                      placeholder="Choose your team…")
                if st.button("Join Game", type="primary", use_container_width=True):
                    if claim_team(chosen, SESSION_ID):
                        st.session_state["claimed_team"] = chosen
                        st.rerun()
                    else:
                        st.error("That team was just claimed — choose another.")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    if is_admin:
        st.markdown(f"""
        <div style='padding:0.75rem 0; border-bottom:1px solid #1e2d45; margin-bottom:1rem;'>
            <div style='font-size:0.65rem; letter-spacing:0.2em; color:#00ff9d; text-transform:uppercase;'>
                Admin Console
            </div>
            <div style='font-size:1.1rem; font-weight:700; color:#e2e8f0; margin-top:0.2rem;'>
                Round {round_num} / {TOTAL_ROUNDS} — {phase.upper()}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Team registration
        with st.expander("👥 Manage Teams", expanded=not teams):
            new_team = st.text_input("Team name", placeholder="e.g. Alpha Squad")
            if st.button("➕ Add team", use_container_width=True) and new_team.strip():
                if new_team.strip() not in teams:
                    add_team(new_team.strip())
                    st.rerun()
                else:
                    st.warning("Already exists")

            if teams:
                for t in sorted(teams.keys()):
                    status = "🟢" if t in sessions else "⚪"
                    st.caption(f"{status} {t}")

            if sessions:
                st.markdown("---")
                to_release = st.selectbox("Release slot", sorted(sessions.keys()))
                if st.button("🔓 Release", use_container_width=True):
                    release_team(to_release)
                    st.rerun()

        st.markdown("---")

        # Phase controls
        st.markdown(f"**Current stock:** `{stock.upper()}`")

        if phase == "submit":
            submitted_count = len(spreads)
            total_teams     = len(teams)
            st.caption(f"{submitted_count}/{total_teams} teams submitted")
            if st.button("⏩ Close & Open Trading", type="primary", use_container_width=True):
                mm = find_market_maker(spreads)
                if mm:
                    set_game_state(market_maker=mm, phase="trade")
                    st.rerun()
                else:
                    st.warning("No spreads yet")

        elif phase == "trade":
            st.markdown(f"**Market Maker:** `{market_maker}`")
            true_p = st.number_input("True price ($)", min_value=0.0, value=100.0, step=0.01)
            if st.button("✅ Reveal True Price", type="primary", use_container_width=True):
                set_true_price(stock, true_p)
                set_game_state(phase="reveal")
                st.rerun()

        elif phase == "reveal":
            if round_num < TOTAL_ROUNDS:
                if st.button("▶ Next Round", type="primary", use_container_width=True):
                    log_round(round_num, stock, market_maker, true_prices.get(stock))
                    set_game_state(round=round_num + 1, phase="submit", market_maker=None)
                    st.rerun()
            else:
                if st.button("🏁 End Game", type="primary", use_container_width=True):
                    log_round(round_num, stock, market_maker, true_prices.get(stock))
                    set_game_state(game_over=True)
                    st.rerun()

        st.markdown("---")
        if st.button("🔄 Reset Game", use_container_width=True):
            reset_game()
            st.rerun()
        if st.button("🚪 Sign out", use_container_width=True):
            st.session_state["is_admin"] = False
            st.rerun()

    else:
        # Team sidebar — minimal
        st.markdown(f"""
        <div style='padding:0.75rem 0;'>
            <div style='font-size:0.65rem; letter-spacing:0.2em; color:#00ff9d; text-transform:uppercase;'>Logged in as</div>
            <div style='font-size:1.3rem; font-weight:800; color:#e2e8f0;'>{my_team}</div>
        </div>
        """, unsafe_allow_html=True)
        st.caption(f"Round {round_num} of {TOTAL_ROUNDS}")
        st.caption(f"Phase: {phase.upper()}")
        st.markdown("---")
        if st.button("🚪 Leave team", use_container_width=True):
            release_team(my_team)
            st.session_state["claimed_team"] = None
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ══════════════════════════════════════════════════════════════════════════════

# ── Header bar ─────────────────────────────────────────────────────────────────
identity_label = "🔧 Admin" if is_admin else f"🏷 {my_team}"
st.markdown(f"""
<div style='display:flex; justify-content:space-between; align-items:center;
            padding:0.6rem 1rem; background:rgba(17,24,39,0.8);
            border:1px solid #1e2d45; border-radius:12px; margin-bottom:1.5rem;
            backdrop-filter:blur(10px);'>
    <div style='display:flex; align-items:center; gap:1.5rem;'>
        <span style='font-family:Space Mono,monospace; font-size:0.8rem;
                     color:#00ff9d; letter-spacing:0.1em;'>
            📈 MARKET MAKING
        </span>
        <span style='color:#1e2d45;'>|</span>
        <span style='font-family:Space Mono,monospace; font-size:0.75rem; color:#64748b;'>
            {stock.upper()} &nbsp;·&nbsp; ROUND {round_num}/{TOTAL_ROUNDS}
        </span>
    </div>
    <span style='font-family:Space Mono,monospace; font-size:0.75rem; color:#94a3b8;'>
        {identity_label}
    </span>
</div>
""", unsafe_allow_html=True)

# ── Game over ──────────────────────────────────────────────────────────────────
if game_over:
    st.balloons()
    st.markdown("""
    <h1 style='text-align:center; font-size:3rem; font-weight:800;
               background:linear-gradient(135deg,#00ff9d,#0ea5e9);
               -webkit-background-clip:text;-webkit-text-fill-color:transparent;
               margin-bottom:2rem;'>
        🏁 Final Results
    </h1>
    """, unsafe_allow_html=True)
    rows = []
    for n in teams:
        total = portfolio_value(n, teams, positions, true_prices)
        rows.append({
            "Rank": "", "Team": n,
            "Final Portfolio": total,
            "Cash": teams[n]["cash"],
            "P&L": total - STARTING_BUDGET,
        })
    df = pd.DataFrame(rows).sort_values("Final Portfolio", ascending=False).reset_index(drop=True)
    df["Rank"] = ["🥇","🥈","🥉"] + [""] * max(0, len(df)-3)
    for col in ["Final Portfolio","Cash","P&L"]:
        df[col] = df[col].apply(lambda v: f"${v:+,.0f}" if col=="P&L" else f"${v:,.0f}")
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.stop()

# ── Progress ───────────────────────────────────────────────────────────────────
prog_pct = (round_num - 1) / TOTAL_ROUNDS
st.progress(prog_pct)
st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PHASE VIEWS
# ══════════════════════════════════════════════════════════════════════════════

# ── SUBMIT PHASE ───────────────────────────────────────────────────────────────
if phase == "submit":
    left, right = st.columns([1, 1], gap="large")

    with left:
        st.markdown(f"""
        <h2 style='font-size:1.8rem; font-weight:800; margin-bottom:0.25rem;'>
            Submit Your Spread
        </h2>
        <p style='color:#64748b; margin-bottom:1.5rem; font-size:0.9rem;'>
            Tightest spread = market maker. You must fill every trade if chosen.
        </p>
        """, unsafe_allow_html=True)

        existing = spreads.get(my_team if not is_admin else "", {})
        already  = my_team in spreads if not is_admin else False

        if is_admin:
            st.info("Waiting for all teams to submit their spreads. Close submissions when ready.")
        else:
            bid_val = st.number_input("📉 Bid — your buy price ($)",
                                      min_value=0.0, value=float(existing.get("bid", 95.0)), step=0.01)
            ask_val = st.number_input("📈 Ask — your sell price ($)",
                                      min_value=0.0, value=float(existing.get("ask", 105.0)), step=0.01)

            spread_width = ask_val - bid_val
            if bid_val >= ask_val:
                st.error("Ask must be strictly greater than bid.")
            else:
                st.markdown(f"""
                <div style='background:rgba(0,255,157,0.05); border:1px solid rgba(0,255,157,0.2);
                            border-radius:10px; padding:0.75rem 1rem; margin:0.5rem 0;
                            font-family:Space Mono,monospace; font-size:0.85rem;'>
                    Spread width: <span style='color:#00ff9d;'>${spread_width:.2f}</span>
                    {"&nbsp;&nbsp;✅ Already submitted — resubmit to update" if already else ""}
                </div>
                """, unsafe_allow_html=True)
                if st.button("Submit Spread", type="primary", use_container_width=True):
                    upsert_spread(round_num, my_team, bid_val, ask_val)
                    st.success("Spread locked in ✓")
                    st.rerun()

    with right:
        st.markdown(f"""
        <h3 style='font-size:1rem; font-weight:700; color:#64748b;
                   letter-spacing:0.1em; text-transform:uppercase; margin-bottom:1rem;'>
            Submissions — {len(spreads)}/{len(teams)} teams
        </h3>
        """, unsafe_allow_html=True)

        # Show only count + which teams have submitted (NOT the actual values)
        if teams:
            rows = []
            for t in sorted(teams.keys()):
                submitted = t in spreads
                is_me     = (t == my_team)
                rows.append({
                    "Team":      t,
                    "Status":    "✅ Submitted" if submitted else "⏳ Waiting…",
                    "":          "👈 You" if is_me else "",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.caption("No teams registered yet.")

# ── TRADE PHASE ────────────────────────────────────────────────────────────────
elif phase == "trade":
    mm_spread = spreads.get(market_maker, {})
    mm_bid    = mm_spread.get("bid", 0)
    mm_ask    = mm_spread.get("ask", 0)
    is_mm     = (my_team == market_maker)

    # Hero band
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,rgba(167,139,250,0.1),rgba(14,165,233,0.08));
                border:1px solid rgba(167,139,250,0.3); border-radius:14px;
                padding:1.25rem 1.5rem; margin-bottom:1.5rem;'>
        <div style='font-size:0.7rem; letter-spacing:0.2em; color:#a78bfa;
                    text-transform:uppercase; margin-bottom:0.5rem;'>
            Market Maker this Round
        </div>
        <div style='font-size:2rem; font-weight:800; color:#e2e8f0;'>{market_maker}</div>
        <div style='display:flex; gap:2rem; margin-top:0.75rem;'>
            <div>
                <div style='font-size:0.65rem; color:#64748b; text-transform:uppercase;'>Bid</div>
                <div style='font-family:Space Mono,monospace; font-size:1.2rem; color:#00ff9d;'>${mm_bid:.2f}</div>
            </div>
            <div>
                <div style='font-size:0.65rem; color:#64748b; text-transform:uppercase;'>Ask</div>
                <div style='font-family:Space Mono,monospace; font-size:1.2rem; color:#0ea5e9;'>${mm_ask:.2f}</div>
            </div>
            <div>
                <div style='font-size:0.65rem; color:#64748b; text-transform:uppercase;'>Spread</div>
                <div style='font-family:Space Mono,monospace; font-size:1.2rem; color:#fbbf24;'>${mm_ask-mm_bid:.2f}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    left, right = st.columns([1, 1], gap="large")

    with left:
        if is_mm or is_admin:
            st.markdown(f"""
            <div style='background:rgba(167,139,250,0.08); border:1px solid rgba(167,139,250,0.2);
                        border-radius:12px; padding:1.25rem; text-align:center;'>
                <div style='font-size:2rem; margin-bottom:0.5rem;'>🏦</div>
                <div style='font-weight:700; font-size:1.1rem; color:#a78bfa;'>
                    {"You are the Market Maker" if is_mm else f"{market_maker} is the Market Maker"}
                </div>
                <div style='color:#64748b; font-size:0.85rem; margin-top:0.5rem;'>
                    Must fill every trade. Can go negative.
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <h3 style='font-weight:700; margin-bottom:1rem;'>Your Trade Decision</h3>
            """, unsafe_allow_html=True)

            action = st.radio("Action", ["BUY at ask", "SELL at bid"],
                              horizontal=True, label_visibility="collapsed")
            price  = mm_ask if action == "BUY at ask" else mm_bid
            cash   = teams[my_team]["cash"]

            st.markdown(f"""
            <div style='background:var(--surface2); border:1px solid var(--border);
                        border-radius:10px; padding:1rem; margin:0.75rem 0;
                        font-family:Space Mono,monospace;'>
                <div style='display:flex; justify-content:space-between;'>
                    <span style='color:#64748b; font-size:0.8rem;'>Trade price</span>
                    <span style='color:#e2e8f0;'>${price:.2f}</span>
                </div>
                <div style='display:flex; justify-content:space-between; margin-top:0.4rem;'>
                    <span style='color:#64748b; font-size:0.8rem;'>Your cash</span>
                    <span style='color:#{"00ff9d" if cash > 0 else "ff4d6d"};'>${cash:,.0f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            btn_label = f"{'🟢 BUY' if action=='BUY at ask' else '🔴 SELL'} 1 unit @ ${price:.2f}"
            if action == "BUY at ask" and cash < price:
                st.error("Insufficient funds.")
            elif st.button(btn_label, type="primary", use_container_width=True):
                if action == "BUY at ask":
                    execute_trade(my_team, market_maker, stock, price, round_num)
                    st.success(f"Bought 1 {stock} @ ${price:.2f}")
                else:
                    execute_trade(market_maker, my_team, stock, price, round_num)
                    st.success(f"Sold 1 {stock} @ ${price:.2f}")
                st.rerun()

    with right:
        round_trades = get_trade_log(round_num)
        st.markdown(f"""
        <h3 style='font-weight:700; margin-bottom:1rem;'>
            Trades This Round
            <span style='font-family:Space Mono,monospace; font-size:0.8rem;
                         color:#64748b; font-weight:400; margin-left:0.5rem;'>
                ({len(round_trades)})
            </span>
        </h3>
        """, unsafe_allow_html=True)
        if round_trades:
            df_t = pd.DataFrame(round_trades)[["buyer","seller","price","executed_at"]]
            df_t.columns = ["Buyer","Seller","Price","Time"]
            df_t["Price"] = df_t["Price"].apply(lambda v: f"${v:.2f}")
            df_t["Time"]  = df_t["Time"].apply(lambda v: str(v)[-15:-7] if v else "")
            st.dataframe(df_t, use_container_width=True, hide_index=True)
        else:
            st.caption("No trades yet this round.")

# ── REVEAL PHASE ───────────────────────────────────────────────────────────────
elif phase == "reveal":
    true_price = true_prices.get(stock)

    st.markdown(f"""
    <h2 style='font-size:1.8rem; font-weight:800; margin-bottom:1.5rem;'>
        🎯 Round {round_num} Results — {stock.upper()}
    </h2>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("True Price", f"${true_price:.2f}" if true_price else "?")
    c2.metric("Market Maker", market_maker or "—")
    if true_price and market_maker and market_maker in spreads:
        sp = spreads[market_maker]
        edge = ((sp["ask"] - true_price) + (true_price - sp["bid"])) / 2
        c3.metric("MM Edge / Trade", f"${edge:.2f}")

    st.markdown("<br>", unsafe_allow_html=True)

    rows = []
    for t, s in spreads.items():
        inside = (s["bid"] <= true_price <= s["ask"]) if true_price else None
        rows.append({
            "Team":    t,
            "Bid":     f"${s['bid']:.2f}",
            "Ask":     f"${s['ask']:.2f}",
            "Spread":  f"${s['ask']-s['bid']:.2f}",
            "Hit?":    "✅" if inside else ("❌" if inside is False else "?"),
            "MM":      "🏦" if t == market_maker else "",
            "You":     "👈" if t == my_team else "",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# LEADERBOARD — always visible
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style='display:flex; align-items:center; gap:0.75rem; margin-bottom:1rem;'>
    <span style='font-size:1.4rem; font-weight:800;'>🏆 Leaderboard</span>
    <span style='font-family:Space Mono,monospace; font-size:0.7rem;
                 color:#64748b; letter-spacing:0.1em;'>LIVE</span>
    <span style='width:6px; height:6px; border-radius:50%; background:#00ff9d;
                 display:inline-block; animation:none; box-shadow:0 0 6px #00ff9d;'></span>
</div>
""", unsafe_allow_html=True)

if teams:
    rows = []
    for name in teams:
        total  = portfolio_value(name, teams, positions, true_prices)
        unreal = unrealised_pnl(name, positions, true_prices)
        pnl    = total - STARTING_BUDGET
        rows.append({
            "":               "🏦" if name == market_maker else "",
            "Team":           name,
            "Cash":           f"${teams[name]['cash']:,.0f}",
            "Unrealised P&L": f"${unreal:+,.0f}",
            "Portfolio":      f"${total:,.0f}",
            "vs $100k":       f"${pnl:+,.0f}",
            "You":            "👈" if name == my_team else "",
        })

    lb = sorted(rows, key=lambda r: float(r["Portfolio"].replace("$","").replace(",","")), reverse=True)
    lb_df = pd.DataFrame(lb).reset_index(drop=True)
    lb_df.index += 1
    st.dataframe(lb_df, use_container_width=True)

    history = get_round_history()
    if history:
        with st.expander("📋 Round History"):
            st.dataframe(pd.DataFrame(history), use_container_width=True, hide_index=True)

    all_trades = get_trade_log()
    if all_trades:
        with st.expander("📜 Full Trade Log"):
            df_all = pd.DataFrame(all_trades)[["round","stock","buyer","seller","price","executed_at"]]
            df_all.columns = ["Round","Stock","Buyer","Seller","Price","Time"]
            df_all["Price"] = df_all["Price"].apply(lambda v: f"${v:.2f}")
            st.dataframe(df_all, use_container_width=True, hide_index=True)
else:
    st.info("No teams registered yet.")

# Auto-refresh
if phase in ("submit", "trade") and not game_over:
    st.caption("⟳ Live — refreshing every 3s")
    import time; time.sleep(3); st.rerun()