import streamlit as st
import pandas as pd
import html as _html

from config import MIN_SHARES
from db import has_traded_this_round, has_passed_this_round, log_pass, get_trade_log
from game import execute_trade


def _esc(s):
    return _html.escape(str(s)) if s else ""


def render_trade(is_admin, my_team, market_maker, round_num, stock, teams, spreads):
    mm_spread = spreads.get(market_maker, {})
    mm_bid = mm_spread.get("bid", 0)
    mm_ask = mm_spread.get("ask", 0)
    is_mm = (my_team == market_maker)

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

    if is_admin:
        return

    left, right = st.columns([1, 1], gap="large")

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
            _render_trade_form(my_team, market_maker, round_num, stock, teams, mm_bid, mm_ask)

    with right:
        _render_trade_log(round_num)


def _render_trade_form(my_team, market_maker, round_num, stock, teams, mm_bid, mm_ask):
    already_traded = has_traded_this_round(my_team, round_num)
    already_passed = has_passed_this_round(my_team, round_num)
    my_cash = teams[my_team]["cash"]

    st.markdown(f"""<h3 style='font-weight:800;font-size:1.25rem;margin-bottom:.25rem;
        color:#f1f5f9;letter-spacing:-.02em;'>Your Trade Decision</h3>
        <p style='color:#64748b;font-size:.78rem;margin-bottom:1rem;'>Min {MIN_SHARES} shares per trade</p>""",
        unsafe_allow_html=True)

    if already_traded or already_passed:
        if already_passed:
            st.info("⏭ You passed this round. Wait for the reveal.")
        else:
            st.warning("✅ You've already placed your trade this round. Wait for the reveal.")
        return

    action = st.radio("Direction",
                       ["🟢 BUY shares (at ask)", "🔴 SELL shares (at bid)", "⏭ PASS (no trade)"],
                       horizontal=True)
    is_pass = "PASS" in action
    is_buy = "BUY" in action

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
            st.info("Passed this round.")
        return

    price = mm_ask if is_buy else mm_bid
    if is_buy:
        max_qty = int(my_cash // price) if price > 0 else 1
    else:
        max_qty = int(my_cash // price) if price > 0 else 1
    max_qty = max(MIN_SHARES, max_qty)
    qty = st.number_input("Number of shares", min_value=MIN_SHARES, max_value=max_qty, value=MIN_SHARES, step=1)
    total_cost = price * qty
    cash_after = my_cash - total_cost if is_buy else my_cash + total_cost

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
        return

    # Two-step confirmation
    confirm_key = f"confirm_trade_{round_num}"
    if confirm_key not in st.session_state:
        st.session_state[confirm_key] = False

    if not st.session_state[confirm_key]:
        if st.button(
            f"{'🟢 BUY' if is_buy else '🔴 SELL'} {qty} shares @ ${price:.2f} = ${total_cost:,.0f}",
            type="primary", use_container_width=True,
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
                    execute_trade(my_team, market_maker, stock, pending["price"], pending["qty"], round_num)
                else:
                    execute_trade(market_maker, my_team, stock, pending["price"], pending["qty"], round_num)
                st.session_state[confirm_key] = False
                st.rerun()
        with col_no:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state[confirm_key] = False
                st.rerun()


def _render_trade_log(round_num):
    round_trades = get_trade_log(round_num)
    real_trades = [t for t in round_trades if t.get("qty", 0) > 0]

    st.markdown(f"""<div style='display:flex;align-items:center;gap:.75rem;margin-bottom:1rem;'>
        <h3 style='font-weight:800;font-size:1.05rem;color:#f1f5f9;margin:0;letter-spacing:-.02em;'>Trades This Round</h3>
        <span style='font-family:JetBrains Mono,monospace;font-size:.7rem;color:#64748b;
                     background:#111827;padding:.15rem .5rem;border-radius:6px;
                     border:1px solid #2a3a50;font-weight:600;'>{len(real_trades)}</span>
    </div>""", unsafe_allow_html=True)

    if real_trades:
        df_t = pd.DataFrame(real_trades)[["buyer", "seller", "price", "qty", "executed_at"]]
        df_t.columns = ["Buyer", "Seller", "Price", "Qty", "Time"]
        df_t["Price"] = df_t["Price"].apply(lambda v: f"${v:.2f}")
        df_t["Time"] = df_t["Time"].apply(lambda v: str(v)[-15:-7] if v else "")
        st.dataframe(df_t, use_container_width=True, hide_index=True)
    else:
        st.markdown("<p style='color:#64748b;font-size:.85rem;'>No trades yet this round.</p>", unsafe_allow_html=True)
