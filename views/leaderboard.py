import streamlit as st
import pandas as pd

from config import STARTING_BUDGET
from db import get_trade_log, get_round_history, reset_game
from utils import dataframe_height, format_gbp


def render_game_over(teams, is_admin):
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

    rows = []
    for n in teams:
        t = teams[n]["cash"]
        rows.append({
            "Rank": "",
            "Team": n,
            "Final Cash": format_gbp(t),
            "P&L": format_gbp(t - STARTING_BUDGET, signed=True),
            "_sort_cash": t,
        })
    df = pd.DataFrame(rows).sort_values("_sort_cash", ascending=False).drop(columns=["_sort_cash"]).reset_index(drop=True)
    df["Rank"] = ["🥇", "🥈", "🥉"] + [""] * (max(0, len(df) - 3))
    st.dataframe(df, use_container_width=True, hide_index=True, height=dataframe_height(len(df), max_height=560))

    if is_admin and st.button("🔄 Reset Game", use_container_width=True):
        reset_game()
        st.rerun()


def render_leaderboard(my_team, market_maker, teams, round_num, phase, game_over, is_admin):
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

    if not teams:
        st.info("No teams registered yet.")
        return

    rows = []
    for name in teams:
        cash = teams[name]["cash"]
        pnl = cash - STARTING_BUDGET
        rows.append({
            "": "🏦" if name == market_maker else "",
            "Team": name,
            "Cash": format_gbp(cash),
            "P&L": format_gbp(pnl, signed=True),
            "You": "👈" if name == my_team else "",
            "_sort_cash": cash,
        })
    lb = sorted(rows, key=lambda r: r["_sort_cash"], reverse=True)
    lb_df = pd.DataFrame(lb).drop(columns=["_sort_cash"]).reset_index(drop=True)
    lb_df.index += 1
    st.dataframe(lb_df, use_container_width=True, height=dataframe_height(len(lb_df), max_height=560))

    # History + chart
    history = get_round_history()
    if history:
        hist_df = pd.DataFrame(history)
        if "round" in hist_df.columns and len(hist_df) > 0:
            chart_data = {"Round": [0], **{n: [0] for n in teams}}
            all_trades_data = get_trade_log()
            cumulative = {n: 0.0 for n in teams}
            for h in history:
                rnd_num = h["round"]
                rnd_tp = h.get("true_price", 0) or 0
                for t in all_trades_data:
                    if t["round"] == rnd_num and t["qty"] > 0:
                        cost = t["price"] * t["qty"]
                        cumulative[t["buyer"]] -= cost
                        cumulative[t["seller"]] += cost
                        cumulative[t["buyer"]] += t["qty"] * rnd_tp
                        cumulative[t["seller"]] -= t["qty"] * rnd_tp
                chart_data["Round"].append(rnd_num)
                for n in teams:
                    chart_data[n].append(round(cumulative[n], 2))
            chart_df = pd.DataFrame(chart_data).set_index("Round")
            with st.expander("📈 P&L Over Rounds", expanded=True):
                st.line_chart(chart_df, use_container_width=True)

        with st.expander("📋 Round History"):
            st.dataframe(hist_df, use_container_width=True, hide_index=True, height=dataframe_height(len(hist_df), max_height=420))

    all_trades = get_trade_log()
    if all_trades:
        with st.expander("📜 Full Trade Log"):
            df_all = pd.DataFrame(all_trades)[["round", "stock", "buyer", "seller", "price", "qty", "executed_at"]]
            df_all.columns = ["Round", "Stock", "Buyer", "Seller", "Price", "Qty", "Time"]
            df_all["Price"] = df_all["Price"].apply(lambda v: format_gbp(v, decimals=2))
            st.dataframe(df_all, use_container_width=True, hide_index=True, height=dataframe_height(len(df_all), max_height=460))
