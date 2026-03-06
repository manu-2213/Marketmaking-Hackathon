import streamlit as st
import pandas as pd
import uuid
from supabase import create_client, Client

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Stock Prediction Market", layout="wide", page_icon="📈")

# ── Session identity — each browser tab gets a unique persistent ID ────────────
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())
SESSION_ID = st.session_state["session_id"]

if "claimed_team" not in st.session_state:
    st.session_state["claimed_team"] = None

# ── Constants ──────────────────────────────────────────────────────────────────
STARTING_BUDGET = 100_000
STOCKS          = [f"stock_{i}" for i in range(1, 10)]
TOTAL_ROUNDS    = 9
ADMIN_PASSWORD  = "admin123"   # ← change before running!

# ── Supabase client ────────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

sb = get_supabase()

# ── DB helpers ─────────────────────────────────────────────────────────────────
def get_game_state():
    r = sb.table("game_state").select("*").eq("id", 1).single().execute()
    return r.data

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
    """Try to claim a team. Returns True if successful, False if already taken."""
    existing = sb.table("team_sessions").select("*").eq("team", team).execute()
    if existing.data:
        # Already claimed — only allow if same session
        return existing.data[0]["session_id"] == session_id
    sb.table("team_sessions").insert({
        "team": team, "session_id": session_id
    }).execute()
    return True

def release_team(team):
    sb.table("team_sessions").delete().eq("team", team).execute()

def get_positions(team=None):
    q = sb.table("positions").select("*")
    if team:
        q = q.eq("team", team)
    return q.execute().data

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
            "team": team, "stock": stock,
            "qty": qty_delta, "cost_basis": cost_delta,
        }).execute()

def update_cash(team, delta):
    teams = get_teams()
    new_cash = teams[team]["cash"] + delta
    sb.table("teams").update({"cash": new_cash}).eq("name", team).execute()

def get_spreads(round_num):
    r = sb.table("spreads").select("*").eq("round", round_num).execute()
    return {row["team"]: row for row in r.data}

def upsert_spread(round_num, team, bid, ask):
    sb.table("spreads").upsert({
        "round": round_num, "team": team, "bid": bid, "ask": ask
    }, on_conflict="round,team").execute()

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
        "buyer": buyer, "seller": seller,
        "price": price, "qty": qty,
    }).execute()

def get_round_history():
    return sb.table("round_history").select("*").order("round").execute().data

def log_round(round_num, stock, market_maker, true_price):
    sb.table("round_history").upsert({
        "round": round_num, "stock": stock,
        "market_maker": market_maker, "true_price": true_price,
    }).execute()

def reset_game():
    sb.table("trade_log").delete().neq("id", 0).execute()
    sb.table("round_history").delete().neq("round", 0).execute()
    sb.table("spreads").delete().neq("id", 0).execute()
    sb.table("true_prices").delete().neq("stock", "").execute()
    sb.table("positions").delete().neq("id", 0).execute()
    sb.table("team_sessions").delete().neq("team", "").execute()
    sb.table("teams").delete().neq("name", "").execute()
    sb.table("game_state").update({
        "round": 1, "phase": "submit",
        "market_maker": None, "game_over": False,
    }).eq("id", 1).execute()

# ── Business logic ─────────────────────────────────────────────────────────────
def find_market_maker(spreads):
    if not spreads:
        return None
    return min(spreads, key=lambda t: (spreads[t]["ask"] - spreads[t]["bid"], t))

def execute_trade(buyer, seller, stock, price, round_num, qty=1):
    cost = price * qty
    update_cash(buyer,  -cost)
    update_cash(seller, +cost)
    upsert_position(buyer,  stock, +qty, +cost)
    upsert_position(seller, stock, -qty, -cost)
    log_trade(round_num, stock, buyer, seller, price, qty)

def portfolio_value(team_name, teams, positions, true_prices):
    cash = teams[team_name]["cash"]
    pnl  = sum(p["qty"] * true_prices[p["stock"]]
               for p in positions
               if p["team"] == team_name and p["stock"] in true_prices)
    return cash + pnl

def unrealised_pnl(team_name, positions, true_prices):
    return sum(p["qty"] * true_prices[p["stock"]] - p["cost_basis"]
               for p in positions
               if p["team"] == team_name and p["stock"] in true_prices and p["qty"] != 0)

# ── Load shared state ──────────────────────────────────────────────────────────
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

# ── Resolve which team this browser owns ──────────────────────────────────────
# Check if this session already owns a team in DB
my_team = st.session_state["claimed_team"]
if my_team is None:
    for team, sid in sessions.items():
        if sid == SESSION_ID:
            my_team = team
            st.session_state["claimed_team"] = team
            break

# ── Team login gate ────────────────────────────────────────────────────────────
if my_team is None:
    st.title("📈 Stock Prediction Market")
    st.header("Select your team to join")

    claimed_teams = set(sessions.keys())
    available     = [t for t in sorted(teams.keys()) if t not in claimed_teams]

    if not teams:
        st.warning("No teams registered yet. Ask the organiser to add teams.")
        st.stop()

    if not available:
        st.warning("All teams are currently claimed. Ask the organiser if there's an issue.")
        st.stop()

    chosen = st.selectbox("Choose your team", available)
    if st.button("Join as this team", type="primary"):
        success = claim_team(chosen, SESSION_ID)
        if success:
            st.session_state["claimed_team"] = chosen
            st.rerun()
        else:
            st.error("That team was just claimed by someone else. Please choose another.")
    st.stop()

# ── Past this point the user has a claimed team ────────────────────────────────

# ── Sidebar — admin ────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🔐 Admin Panel")
    pwd      = st.text_input("Password", type="password")
    is_admin = pwd == ADMIN_PASSWORD
    if pwd and not is_admin:
        st.error("Wrong password")

    if is_admin:
        st.success("Admin access granted")
        st.divider()

        st.subheader("Register Teams")
        new_team = st.text_input("Team name")
        if st.button("Add team") and new_team.strip():
            if new_team.strip() not in teams:
                add_team(new_team.strip())
                st.success(f"Added {new_team.strip()}")
                st.rerun()
            else:
                st.warning("Already exists")

        if teams:
            st.write("**Registered:**", ", ".join(sorted(teams.keys())))
            # Show claim status
            for t in sorted(teams.keys()):
                status = "🔒 claimed" if t in sessions else "⬜ unclaimed"
                st.caption(f"{t}: {status}")
            if st.button("🗑 Remove all teams", type="secondary"):
                delete_all_teams()
                st.rerun()
            # Admin can release a specific team if needed
            st.divider()
            st.subheader("Release a team slot")
            if sessions:
                to_release = st.selectbox("Team to release", sorted(sessions.keys()))
                if st.button("Release"):
                    release_team(to_release)
                    st.success(f"Released {to_release}")
                    st.rerun()

        st.divider()
        st.subheader(f"Round {round_num} — {stock.upper()}")
        st.write(f"Phase: **{phase.upper()}**")

        if phase == "submit":
            if st.button("⏩ Close submissions → Trading", type="primary"):
                mm = find_market_maker(spreads)
                if mm:
                    set_game_state(market_maker=mm, phase="trade")
                    st.rerun()
                else:
                    st.warning("No spreads submitted yet")

        elif phase == "trade":
            st.subheader("Reveal true price")
            true_p = st.number_input("True price ($)", min_value=0.0, value=100.0, step=0.01)
            if st.button("✅ Reveal & settle", type="primary"):
                set_true_price(stock, true_p)
                set_game_state(phase="reveal")
                st.rerun()

        elif phase == "reveal":
            if round_num < TOTAL_ROUNDS:
                if st.button("▶ Next round", type="primary"):
                    log_round(round_num, stock, market_maker, true_prices.get(stock))
                    set_game_state(round=round_num + 1, phase="submit", market_maker=None)
                    st.rerun()
            else:
                if st.button("🏁 End game", type="primary"):
                    log_round(round_num, stock, market_maker, true_prices.get(stock))
                    set_game_state(game_over=True)
                    st.rerun()

        st.divider()
        if st.button("🔄 Reset entire game", type="secondary"):
            reset_game()
            st.rerun()

# ── Main ───────────────────────────────────────────────────────────────────────
st.title("📈 Stock Prediction Market")
st.caption(f"Logged in as: **{my_team}**")

if game_over:
    st.balloons()
    st.header("🏁 Final Results")
    rows = [{"Team": n,
             "Final Portfolio": f"${portfolio_value(n, teams, positions, true_prices):,.0f}",
             "Cash": f"${teams[n]['cash']:,.0f}",
             "Total P&L": f"${portfolio_value(n, teams, positions, true_prices) - STARTING_BUDGET:+,.0f}"}
            for n in teams]
    df = pd.DataFrame(rows).sort_values("Final Portfolio", ascending=False).reset_index(drop=True)
    df.index += 1
    st.dataframe(df, use_container_width=True)
    st.stop()

st.progress((round_num - 1) / TOTAL_ROUNDS,
            text=f"Round {round_num} of {TOTAL_ROUNDS}  •  {stock.upper()}  •  Phase: {phase.upper()}")
st.divider()

# ── SUBMIT ─────────────────────────────────────────────────────────────────────
if phase == "submit":
    st.header(f"📋 Submit Spread — {stock.upper()}")
    st.info("Enter your **bid** (buy price) and **ask** (sell price). Tightest spread becomes the market maker.")

    col_form, col_submitted = st.columns([1, 1])
    with col_form:
        existing = spreads.get(my_team, {})
        bid_val  = st.number_input("Bid ($)", min_value=0.0,
                                   value=float(existing.get("bid", 95.0)), step=0.01)
        ask_val  = st.number_input("Ask ($)", min_value=0.0,
                                   value=float(existing.get("ask", 105.0)), step=0.01)
        if bid_val >= ask_val:
            st.error("Ask must be greater than bid")
        elif st.button("Submit spread", type="primary"):
            upsert_spread(round_num, my_team, bid_val, ask_val)
            st.success("Spread submitted!")
            st.rerun()

    with col_submitted:
        st.subheader("Submitted so far")
        if spreads:
            rows = [{"Team": t, "Bid": f"${s['bid']:.2f}",
                     "Ask": f"${s['ask']:.2f}",
                     "Spread": f"${s['ask']-s['bid']:.2f}",
                     "You": "👈" if t == my_team else ""}
                    for t, s in spreads.items()]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.caption(f"{len(spreads)} / {len(teams)} teams submitted")
        else:
            st.write("Waiting for submissions…")

# ── TRADE ──────────────────────────────────────────────────────────────────────
elif phase == "trade":
    mm_spread = spreads.get(market_maker, {})
    st.header(f"💹 Trading — {stock.upper()}")

    c1, c2, c3 = st.columns(3)
    c1.metric("🏦 Market Maker", market_maker)
    c2.metric("Best Bid", f"${mm_spread.get('bid', 0):.2f}")
    c3.metric("Best Ask", f"${mm_spread.get('ask', 0):.2f}")

    if my_team == market_maker:
        st.warning("🏦 You are the market maker this round. You must fill every trade.")
    else:
        st.divider()
        st.subheader("Your trade")
        action = st.selectbox("Action", ["BUY (at ask)", "SELL (at bid)"])
        price  = mm_spread.get("ask" if action.startswith("BUY") else "bid", 100)
        st.write(f"Trade price: **${price:.2f}**")
        cash_after = teams[my_team]["cash"] - (price if action.startswith("BUY") else 0)
        if action.startswith("BUY") and cash_after < 0:
            st.error(f"Insufficient funds. You have ${teams[my_team]['cash']:,.0f}")
        elif st.button("⚡ Submit trade decision", type="primary"):
            if action.startswith("BUY"):
                execute_trade(my_team, market_maker, stock, price, round_num)
                st.success(f"Bought 1 {stock} from {market_maker} @ ${price:.2f}")
            else:
                execute_trade(market_maker, my_team, stock, price, round_num)
                st.success(f"Sold 1 {stock} to {market_maker} @ ${price:.2f}")
            st.rerun()

    st.divider()
    st.subheader("All spreads this round")
    rows = [{"Team": t, "Bid": f"${s['bid']:.2f}", "Ask": f"${s['ask']:.2f}",
             "Spread": f"${s['ask']-s['bid']:.2f}",
             "Market Maker": "✅" if t == market_maker else "",
             "You": "👈" if t == my_team else ""}
            for t, s in spreads.items()]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    round_trades = get_trade_log(round_num)
    if round_trades:
        st.subheader(f"Trades this round ({len(round_trades)})")
        st.dataframe(pd.DataFrame(round_trades), use_container_width=True, hide_index=True)

# ── REVEAL ─────────────────────────────────────────────────────────────────────
elif phase == "reveal":
    true_price = true_prices.get(stock)
    st.header(f"🎯 Reveal — {stock.upper()}")

    c1, c2 = st.columns(2)
    c1.metric("True Price", f"${true_price:.2f}" if true_price else "?")
    c2.metric("Market Maker", market_maker or "—")

    st.divider()
    rows = []
    for t, s in spreads.items():
        inside = (s["bid"] <= true_price <= s["ask"]) if true_price else None
        rows.append({
            "Team":   t, "Bid": f"${s['bid']:.2f}",
            "Ask":    f"${s['ask']:.2f}", "Spread": f"${s['ask']-s['bid']:.2f}",
            "Contains true price": "✅" if inside else ("❌" if inside is False else "?"),
            "Market Maker": "🏦" if t == market_maker else "",
            "You": "👈" if t == my_team else "",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ── LEADERBOARD ────────────────────────────────────────────────────────────────
st.divider()
st.header("🏆 Live Leaderboard")

if teams:
    rows = []
    for name in teams:
        total  = portfolio_value(name, teams, positions, true_prices)
        unreal = unrealised_pnl(name, positions, true_prices)
        rows.append({
            "":                "🏦" if name == market_maker else "",
            "Team":            name,
            "Cash":            f"${teams[name]['cash']:,.0f}",
            "Unrealised P&L":  f"${unreal:+,.0f}",
            "Total Portfolio": f"${total:,.0f}",
            "vs Start":        f"${total - STARTING_BUDGET:+,.0f}",
            "You":             "👈" if name == my_team else "",
        })
    lb = sorted(rows, key=lambda r: float(r["Total Portfolio"].replace("$","").replace(",","")), reverse=True)
    lb_df = pd.DataFrame(lb).reset_index(drop=True)
    lb_df.index += 1
    st.dataframe(lb_df, use_container_width=True)

    history = get_round_history()
    if history:
        st.subheader("Round history")
        st.dataframe(pd.DataFrame(history), use_container_width=True, hide_index=True)

    all_trades = get_trade_log()
    if all_trades:
        with st.expander("📜 Full trade log"):
            st.dataframe(pd.DataFrame(all_trades), use_container_width=True, hide_index=True)

# Auto-refresh every 3s during active phases
if phase in ("submit", "trade") and not game_over:
    st.caption("🔄 Auto-refreshing every 3s")
    import time; time.sleep(3); st.rerun()