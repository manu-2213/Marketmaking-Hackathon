import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Stock Prediction Market", layout="wide", page_icon="📈")

# ── Constants ──────────────────────────────────────────────────────────────────
STARTING_BUDGET   = 100_000
STOCKS            = [f"stock_{i}" for i in range(1, 10)]
TOTAL_ROUNDS      = 9
ADMIN_PASSWORD    = "admin123"   # change before running!

# ── Session state bootstrap ────────────────────────────────────────────────────
def init_state():
    defaults = {
        "teams":          {},          # {team_name: {cash, positions, trades}}
        "round":          1,           # current stock round (1-9)
        "phase":          "submit",    # submit | trade | reveal
        "spreads":        {},          # {team: {bid, ask}} for current round
        "market_maker":   None,
        "true_prices":    {},          # {stock: price} — filled by admin at reveal
        "trade_log":      [],          # list of trade dicts
        "round_history":  [],          # closed rounds summary
        "game_over":      False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()
S = st.session_state

# ── Helpers ────────────────────────────────────────────────────────────────────
def current_stock():
    return STOCKS[S["round"] - 1]

def find_market_maker():
    """Team with tightest (ask-bid) spread. Ties broken alphabetically."""
    spreads = S["spreads"]
    if not spreads:
        return None
    best_team = min(spreads, key=lambda t: (
        spreads[t]["ask"] - spreads[t]["bid"], t
    ))
    return best_team

def portfolio_value(team_name):
    team  = S["teams"][team_name]
    cash  = team["cash"]
    pnl   = 0.0
    for stock, qty in team["positions"].items():
        if stock in S["true_prices"] and qty != 0:
            pnl += qty * S["true_prices"][stock]
    return cash + pnl

def unrealised_pnl(team_name):
    team = S["teams"][team_name]
    pnl  = 0.0
    for stock, qty in team["positions"].items():
        if stock in S["true_prices"] and qty != 0:
            cost = team.get("cost_basis", {}).get(stock, 0)
            pnl += qty * S["true_prices"][stock] - cost
    return pnl

def execute_trade(buyer_team, seller_team, stock, price, qty=1):
    """Move stock & cash between two teams."""
    cost = price * qty
    # buyer pays cash, gets stock
    S["teams"][buyer_team]["cash"] -= cost
    S["teams"][buyer_team]["positions"][stock] = \
        S["teams"][buyer_team]["positions"].get(stock, 0) + qty
    S["teams"][buyer_team].setdefault("cost_basis", {})[stock] = \
        S["teams"][buyer_team]["cost_basis"].get(stock, 0) + cost

    # seller loses stock, gets cash
    S["teams"][seller_team]["cash"] += cost
    S["teams"][seller_team]["positions"][stock] = \
        S["teams"][seller_team]["positions"].get(stock, 0) - qty
    S["teams"][seller_team].setdefault("cost_basis", {})[stock] = \
        S["teams"][seller_team]["cost_basis"].get(stock, 0) - cost

    S["trade_log"].append({
        "round": S["round"], "stock": stock,
        "buyer": buyer_team, "seller": seller_team,
        "price": price, "qty": qty,
        "time": datetime.now().strftime("%H:%M:%S"),
    })

# ── Sidebar — admin panel ──────────────────────────────────────────────────────
with st.sidebar:
    st.title("🔐 Admin Panel")
    pwd = st.text_input("Password", type="password")
    is_admin = (pwd == ADMIN_PASSWORD)
    if pwd and not is_admin:
        st.error("Wrong password")

    if is_admin:
        st.success("Admin access granted")
        st.divider()

        # Register teams
        st.subheader("Register Teams")
        new_team = st.text_input("Team name")
        if st.button("Add team") and new_team:
            if new_team not in S["teams"]:
                S["teams"][new_team] = {
                    "cash": STARTING_BUDGET,
                    "positions": {},
                    "cost_basis": {},
                }
                st.success(f"Added {new_team}")
            else:
                st.warning("Already exists")

        if S["teams"]:
            st.write("**Registered:**", ", ".join(S["teams"].keys()))
            if st.button("🗑 Remove all teams", type="secondary"):
                S["teams"] = {}

        st.divider()

        # Phase controls
        st.subheader(f"Round {S['round']} — {current_stock()}")
        st.write(f"Phase: **{S['phase'].upper()}**")

        if S["phase"] == "submit":
            if st.button("⏩ Close submissions → Trading", type="primary"):
                mm = find_market_maker()
                if mm:
                    S["market_maker"] = mm
                    S["phase"] = "trade"
                    st.rerun()
                else:
                    st.warning("No spreads submitted yet")

        elif S["phase"] == "trade":
            st.subheader("Reveal true price")
            true_p = st.number_input("True price ($)", min_value=0.0, value=100.0, step=0.01)
            if st.button("✅ Reveal & settle", type="primary"):
                S["true_prices"][current_stock()] = true_p
                S["phase"] = "reveal"
                st.rerun()

        elif S["phase"] == "reveal":
            if S["round"] < TOTAL_ROUNDS:
                if st.button("▶ Next round", type="primary"):
                    S["round_history"].append({
                        "round":        S["round"],
                        "stock":        current_stock(),
                        "market_maker": S["market_maker"],
                        "true_price":   S["true_prices"].get(current_stock()),
                    })
                    S["round"]  += 1
                    S["phase"]   = "submit"
                    S["spreads"] = {}
                    S["market_maker"] = None
                    st.rerun()
            else:
                if st.button("🏁 End game", type="primary"):
                    S["game_over"] = True
                    st.rerun()

        st.divider()
        if st.button("🔄 Reset entire game", type="secondary"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

# ── Main area ──────────────────────────────────────────────────────────────────
st.title("📈 Stock Prediction Market")

if S["game_over"]:
    st.balloons()
    st.header("🏆 Final Results")
    rows = []
    for name in S["teams"]:
        rows.append({
            "Team":            name,
            "Final Portfolio": f"${portfolio_value(name):,.0f}",
            "Cash":            f"${S['teams'][name]['cash']:,.0f}",
            "Total P&L":       f"${portfolio_value(name) - STARTING_BUDGET:+,.0f}",
        })
    df = pd.DataFrame(rows).sort_values("Final Portfolio", ascending=False).reset_index(drop=True)
    df.index += 1
    st.dataframe(df, use_container_width=True)
    st.stop()

# Progress bar
progress = (S["round"] - 1) / TOTAL_ROUNDS
col_prog, col_info = st.columns([3, 1])
with col_prog:
    st.progress(progress, text=f"Round {S['round']} of {TOTAL_ROUNDS}  •  {current_stock().upper()}  •  Phase: {S['phase'].upper()}")
with col_info:
    st.metric("Teams registered", len(S["teams"]))

st.divider()

# ── SUBMIT PHASE ───────────────────────────────────────────────────────────────
if S["phase"] == "submit":
    st.header(f"📋 Submit Spread — {current_stock().upper()}")
    st.info("Each team: enter your predicted **bid** (buy price) and **ask** (sell price). Tightest spread becomes the market maker.")

    col_form, col_submitted = st.columns([1, 1])

    with col_form:
        if S["teams"]:
            team_sel = st.selectbox("Your team", sorted(S["teams"].keys()))
            bid_val  = st.number_input("Bid ($)", min_value=0.0, value=95.0, step=0.01, key="bid_input")
            ask_val  = st.number_input("Ask ($)", min_value=0.0, value=105.0, step=0.01, key="ask_input")

            if bid_val >= ask_val:
                st.error("Ask must be greater than bid")
            elif st.button("Submit spread", type="primary"):
                S["spreads"][team_sel] = {"bid": bid_val, "ask": ask_val}
                st.success(f"Spread submitted for {team_sel}!")
                st.rerun()
        else:
            st.warning("No teams registered yet — ask admin to add teams.")

    with col_submitted:
        st.subheader("Submitted so far")
        if S["spreads"]:
            rows = []
            for t, sp in S["spreads"].items():
                rows.append({"Team": t, "Bid": f"${sp['bid']:.2f}", "Ask": f"${sp['ask']:.2f}",
                             "Spread": f"${sp['ask']-sp['bid']:.2f}"})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.caption(f"{len(S['spreads'])} / {len(S['teams'])} teams submitted")
        else:
            st.write("Waiting for submissions…")

# ── TRADE PHASE ────────────────────────────────────────────────────────────────
elif S["phase"] == "trade":
    mm   = S["market_maker"]
    sp   = S["spreads"][mm]
    stock = current_stock()

    st.header(f"💹 Trading — {stock.upper()}")

    col_mm, col_sp = st.columns(2)
    with col_mm:
        st.metric("🏦 Market Maker", mm)
        st.caption("Market maker MUST fill every trade. They can go negative.")
    with col_sp:
        st.metric("Best Bid", f"${sp['bid']:.2f}")
        st.metric("Best Ask", f"${sp['ask']:.2f}")

    st.divider()
    st.subheader("All submitted spreads")
    rows = []
    for t, s in S["spreads"].items():
        rows.append({
            "Team": t,
            "Bid":  f"${s['bid']:.2f}",
            "Ask":  f"${s['ask']:.2f}",
            "Spread": f"${s['ask']-s['bid']:.2f}",
            "Market Maker": "✅" if t == mm else "",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Execute trade")
    st.caption("Non-market-maker teams choose to BUY (at ask) or SELL (at bid) from the market maker.")

    non_mm_teams = [t for t in S["teams"] if t != mm]
    if non_mm_teams:
        col_t, col_a = st.columns(2)
        with col_t:
            trading_team = st.selectbox("Team", sorted(non_mm_teams))
        with col_a:
            action = st.selectbox("Action", ["BUY (buy at ask price)", "SELL (sell at bid price)"])

        price = sp["ask"] if action.startswith("BUY") else sp["bid"]
        st.write(f"Trade price: **${price:.2f}**")

        if st.button("⚡ Execute trade", type="primary"):
            if action.startswith("BUY"):
                execute_trade(trading_team, mm, stock, price)
                st.success(f"{trading_team} bought 1 {stock} from {mm} @ ${price:.2f}")
            else:
                execute_trade(mm, trading_team, stock, price)
                st.success(f"{trading_team} sold 1 {stock} to {mm} @ ${price:.2f}")
            st.rerun()
    else:
        st.info("Only one team — no trades possible.")

    # Live trade log for this round
    round_trades = [t for t in S["trade_log"] if t["round"] == S["round"]]
    if round_trades:
        st.subheader(f"Trades this round ({len(round_trades)})")
        st.dataframe(pd.DataFrame(round_trades), use_container_width=True, hide_index=True)

# ── REVEAL PHASE ───────────────────────────────────────────────────────────────
elif S["phase"] == "reveal":
    stock      = current_stock()
    true_price = S["true_prices"].get(stock, "?")
    mm         = S["market_maker"]

    st.header(f"🎯 Reveal — {stock.upper()}")
    st.metric("True Price", f"${true_price:.2f}" if isinstance(true_price, float) else true_price)
    st.metric("Market Maker this round", mm)

    if isinstance(true_price, float):
        sp = S["spreads"].get(mm, {})
        mm_edge = ((sp.get("ask", true_price) - true_price) +
                   (true_price - sp.get("bid", true_price))) / 2
        st.caption(f"MM spread edge per trade: ${mm_edge:.2f}")

    st.divider()
    st.subheader("Spread accuracy — all teams")
    rows = []
    for t, s in S["spreads"].items():
        inside = (s["bid"] <= true_price <= s["ask"]) if isinstance(true_price, float) else "?"
        rows.append({
            "Team":    t,
            "Bid":     f"${s['bid']:.2f}",
            "Ask":     f"${s['ask']:.2f}",
            "Spread":  f"${s['ask']-s['bid']:.2f}",
            "Contains true price": "✅" if inside is True else ("❌" if inside is False else "?"),
            "Market Maker": "🏦" if t == mm else "",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ── LEADERBOARD (always visible) ───────────────────────────────────────────────
st.divider()
st.header("🏆 Live Leaderboard")

if S["teams"]:
    rows = []
    for name, team in S["teams"].items():
        unreal = unrealised_pnl(name)
        total  = portfolio_value(name)
        pnl    = total - STARTING_BUDGET
        rows.append({
            "Team":             name,
            "Cash":             team["cash"],
            "Unrealised P&L":   unreal,
            "Total Portfolio":  total,
            "vs Start":         pnl,
        })

    lb = pd.DataFrame(rows).sort_values("Total Portfolio", ascending=False).reset_index(drop=True)
    lb.index += 1

    # Format for display
    def fmt(v): return f"${v:,.0f}"
    def fmt_pnl(v): return f"+${v:,.0f}" if v >= 0 else f"-${abs(v):,.0f}"

    lb_display = lb.copy()
    lb_display["Cash"]            = lb["Cash"].apply(fmt)
    lb_display["Unrealised P&L"]  = lb["Unrealised P&L"].apply(fmt_pnl)
    lb_display["Total Portfolio"] = lb["Total Portfolio"].apply(fmt)
    lb_display["vs Start"]        = lb["vs Start"].apply(fmt_pnl)

    # Highlight market maker
    if S["market_maker"]:
        lb_display[""] = lb_display["Team"].apply(
            lambda t: "🏦" if t == S["market_maker"] else ""
        )

    st.dataframe(lb_display, use_container_width=True)

    # Market maker history
    if S["round_history"]:
        st.subheader("Market maker history")
        st.dataframe(pd.DataFrame(S["round_history"]), use_container_width=True, hide_index=True)

    # Full trade log
    if S["trade_log"]:
        with st.expander("📜 Full trade log"):
            st.dataframe(pd.DataFrame(S["trade_log"]), use_container_width=True, hide_index=True)
else:
    st.info("No teams registered yet. Admin must add teams in the sidebar.")

# Auto-refresh every 5 seconds during active phases
if S["phase"] in ("submit", "trade") and not S["game_over"]:
    st.caption("🔄 Auto-refreshing every 5s")
    import time
    time.sleep(5)
    st.rerun()