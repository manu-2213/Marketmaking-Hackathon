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
    rows = sb().table("team_sessions").select("team,session_id").execute().data
    sessions = {}

    # Deterministic collapse in case legacy duplicate rows exist.
    for r in sorted(rows, key=lambda x: (x["team"], x["session_id"])):
        team = r["team"]
        sid = r["session_id"]
        if team not in sessions:
            sessions[team] = sid
            continue
        if sessions[team] != sid:
            sb().table("team_sessions").delete().eq("team", team).eq("session_id", sid).execute()

    return sessions


def get_team_for_session(sid):
    rows = sb().table("team_sessions").select("team").eq("session_id", sid).execute().data
    if not rows:
        return None

    teams = sorted({r["team"] for r in rows})
    if len(teams) == 1:
        return teams[0]

    # Ambiguous mapping should not auto-assign the wrong team.
    # Clear all claims for this sid and force explicit re-join.
    sb().table("team_sessions").delete().eq("session_id", sid).execute()
    return None


def claim_team(team, sid):
    # Idempotent success if this exact claim already exists.
    ex = sb().table("team_sessions").select("team").eq("team", team).eq("session_id", sid).execute().data
    if ex:
        sb().table("team_sessions").delete().eq("session_id", sid).neq("team", team).execute()
        return True

    # Insert-first strategy: first writer should win; second concurrent writer should fail
    # under a unique constraint on `team` and then be resolved by readback below.
    try:
        sb().table("team_sessions").insert({"team": team, "session_id": sid}).execute()
    except Exception:
        pass

    # Resolve concurrent duplicates (if constraints are missing) by selecting one
    # deterministic winner and deleting the rest.
    owners = sb().table("team_sessions").select("session_id").eq("team", team).execute().data
    if not owners:
        return False

    owner_ids = sorted({r["session_id"] for r in owners})
    winner_sid = owner_ids[0]
    for losing_sid in owner_ids[1:]:
        sb().table("team_sessions").delete().eq("team", team).eq("session_id", losing_sid).execute()

    if winner_sid != sid:
        return False

    # Keep one-team-per-session invariant (best effort) after successful claim.
    sb().table("team_sessions").delete().eq("session_id", sid).neq("team", team).execute()
    return True


def release_team(team):
    sb().table("team_sessions").delete().eq("team", team).execute()


# ── Positions ──────────────────────────────────────────────────────────────────

def get_positions():
    return sb().table("positions").select("*").execute().data


def upsert_position(team, stk, dq, dc):
    max_retries = 10
    for _ in range(max_retries):
        rows = sb().table("positions").select("*").eq("team", team).eq("stock", stk).execute().data

        # Defensive repair: collapse duplicate rows for same (team, stock).
        if len(rows) > 1:
            rows = sorted(rows, key=lambda r: r["id"])
            keeper = rows[0]
            total_qty = sum(r.get("qty", 0) for r in rows)
            total_cb = sum(r.get("cost_basis", 0) for r in rows)
            sb().table("positions").update(
                {"qty": total_qty, "cost_basis": total_cb}
            ).eq("id", keeper["id"]).execute()
            for extra in rows[1:]:
                sb().table("positions").delete().eq("id", extra["id"]).execute()
            continue

        if len(rows) == 1:
            row = rows[0]
            new_qty = row["qty"] + dq
            new_cb = row["cost_basis"] + dc
            res = sb().table("positions").update(
                {"qty": new_qty, "cost_basis": new_cb}
            ).eq("id", row["id"]).eq("qty", row["qty"]).eq("cost_basis", row["cost_basis"]).select("id").execute()
            if res.data:
                return
            continue

        try:
            sb().table("positions").insert(
                {"team": team, "stock": stk, "qty": dq, "cost_basis": dc}
            ).execute()
            return
        except Exception:
            # Another concurrent insert may have won; retry with read path.
            continue

    raise RuntimeError(f"Could not update position for team={team}, stock={stk} after retries")


def update_cash(team, delta):
    max_retries = 10
    for _ in range(max_retries):
        current = sb().table("teams").select("cash").eq("name", team).single().execute().data
        current_cash = current["cash"]
        new_cash = current_cash + delta

        # Compare-and-swap update to avoid lost writes under concurrent trades.
        res = sb().table("teams").update(
            {"cash": new_cash}
        ).eq("name", team).eq("cash", current_cash).select("cash").execute()
        if res.data:
            return

    raise RuntimeError(f"Could not update cash for team={team} after retries")


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
