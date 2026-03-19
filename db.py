import streamlit as st
from supabase import create_client, Client

from config import STARTING_BUDGET


@st.cache_resource
def _get_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


def sb():
    return _get_supabase()


# ── Game state ─────────────────────────────────────────────────────────────────

def get_game_state():
    return sb().table("game_state").select("*").eq("id", 1).single().execute().data


def set_game_state(**kw):
    sb().table("game_state").update(kw).eq("id", 1).execute()


# ── Teams ──────────────────────────────────────────────────────────────────────

def get_teams():
    return {r["name"]: r for r in sb().table("teams").select("*").execute().data}


def add_team(name):
    sb().table("teams").insert({"name": name, "cash": STARTING_BUDGET}).execute()


def delete_all_teams():
    sb().table("team_sessions").delete().neq("team", "").execute()
    sb().table("teams").delete().neq("name", "").execute()


# ── Sessions ───────────────────────────────────────────────────────────────────

def get_sessions():
    return {r["team"]: r["session_id"] for r in sb().table("team_sessions").select("*").execute().data}


def get_team_for_session(sid):
    rows = sb().table("team_sessions").select("team").eq("session_id", sid).execute().data
    if not rows:
        return None

    # Defensive normalization: if stale duplicate bindings exist for one session,
    # keep a deterministic team and clear the others.
    teams = sorted({r["team"] for r in rows})
    keeper = teams[0]
    for stale_team in teams[1:]:
        sb().table("team_sessions").delete().eq("team", stale_team).eq("session_id", sid).execute()
    return keeper


def claim_team(team, sid):
    ex = sb().table("team_sessions").select("*").eq("team", team).execute()
    if ex.data:
        if ex.data[0]["session_id"] == sid:
            # Keep one team binding per session id.
            sb().table("team_sessions").delete().eq("session_id", sid).neq("team", team).execute()
            return True
        return False

    # Prevent one browser/session from ending up linked to multiple teams.
    sb().table("team_sessions").delete().eq("session_id", sid).execute()
    sb().table("team_sessions").insert({"team": team, "session_id": sid}).execute()
    return True


def release_team(team):
    sb().table("team_sessions").delete().eq("team", team).execute()


# ── Positions ──────────────────────────────────────────────────────────────────

def get_positions():
    return sb().table("positions").select("*").execute().data


def upsert_position(team, stk, dq, dc):
    r = sb().table("positions").select("*").eq("team", team).eq("stock", stk).execute()
    if r.data:
        row = r.data[0]
        sb().table("positions").update(
            {"qty": row["qty"] + dq, "cost_basis": row["cost_basis"] + dc}
        ).eq("id", row["id"]).execute()
    else:
        sb().table("positions").insert(
            {"team": team, "stock": stk, "qty": dq, "cost_basis": dc}
        ).execute()


def update_cash(team, delta):
    current = sb().table("teams").select("cash").eq("name", team).single().execute().data
    sb().table("teams").update({"cash": current["cash"] + delta}).eq("name", team).execute()


# ── Spreads ────────────────────────────────────────────────────────────────────

def get_spreads(rnd):
    return {r["team"]: r for r in sb().table("spreads").select("*").eq("round", rnd).execute().data}


def upsert_spread(rnd, team, bid, ask):
    sb().table("spreads").upsert(
        {"round": rnd, "team": team, "bid": bid, "ask": ask}, on_conflict="round,team"
    ).execute()


# ── True prices ────────────────────────────────────────────────────────────────

def get_true_prices():
    return {r["stock"]: r["price"] for r in sb().table("true_prices").select("*").execute().data}


def set_true_price(stk, price):
    sb().table("true_prices").upsert({"stock": stk, "price": price}).execute()


# ── Trade log ──────────────────────────────────────────────────────────────────

def get_trade_log(rnd=None):
    q = sb().table("trade_log").select("*").order("executed_at")
    if rnd:
        q = q.eq("round", rnd)
    return q.execute().data


def log_trade(rnd, stk, buyer, seller, price, qty):
    sb().table("trade_log").insert(
        {"round": rnd, "stock": stk, "buyer": buyer, "seller": seller, "price": price, "qty": qty}
    ).execute()


def has_traded_this_round(team, rnd):
    r = sb().table("trade_log").select("*").eq("round", rnd).execute().data
    mm = get_game_state()["market_maker"]
    for t in r:
        if t["buyer"] == team or (t["seller"] == team and t["seller"] != mm):
            return True
    return False


def has_passed_this_round(team, rnd):
    r = sb().table("trade_log").select("*").eq("round", rnd).eq("buyer", team).eq("qty", 0).execute().data
    return len(r) > 0


def log_pass(team, rnd, stk):
    sb().table("trade_log").insert(
        {"round": rnd, "stock": stk, "buyer": team, "seller": "PASS", "price": 0, "qty": 0}
    ).execute()


# ── Round history ──────────────────────────────────────────────────────────────

def get_round_history():
    return sb().table("round_history").select("*").order("round").execute().data


def log_round(rnd, stk, mm, tp):
    sb().table("round_history").upsert(
        {"round": rnd, "stock": stk, "market_maker": mm, "true_price": tp}
    ).execute()


# ── Settlement ─────────────────────────────────────────────────────────────────

def settle_round(rnd, stk, true_price):
    pos = sb().table("positions").select("*").eq("stock", stk).execute().data
    for p in pos:
        if p["qty"] != 0:
            update_cash(p["team"], p["qty"] * true_price)
    sb().table("positions").update({"qty": 0, "cost_basis": 0}).eq("stock", stk).execute()


# ── Reset ──────────────────────────────────────────────────────────────────────

def reset_game():
    for tbl, col in [
        ("trade_log", "id"), ("round_history", "round"), ("spreads", "id"),
        ("true_prices", "stock"), ("positions", "id"), ("team_sessions", "team"), ("teams", "name"),
    ]:
        sb().table(tbl).delete().neq(col, "" if col in ("stock", "team", "name") else 0).execute()
    sb().table("game_state").update(
        {"round": 1, "phase": "submit", "market_maker": None, "game_over": False}
    ).eq("id", 1).execute()
