import streamlit as st
import pandas as pd


def render_reveal(my_team, market_maker, round_num, stock, spreads, true_prices):
    true_price = true_prices.get(stock)

    st.markdown(f"""<div class='animate-in' style='margin-bottom:1.5rem;'>
        <h2 style='font-size:1.8rem;font-weight:800;color:#f1f5f9;letter-spacing:-.03em;margin-bottom:.3rem;'>
            🎯 Round {round_num} Results</h2>
        <p style='color:#64748b;font-size:.85rem;'>{stock.upper()} — all positions settled at true price</p>
    </div>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("True Price", f"${true_price:.2f}" if true_price else "?")
    c2.metric("Market Maker", market_maker or "—")
    if true_price and market_maker and market_maker in spreads:
        sp = spreads[market_maker]
        c3.metric("MM Edge / Share", f"${((sp['ask']-true_price)+(true_price-sp['bid']))/2:.2f}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.info("✅ All positions have been settled to cash at the true price.")

    rows = []
    for t, s in spreads.items():
        inside = (s["bid"] <= true_price <= s["ask"]) if true_price else None
        rows.append({
            "Team": t,
            "Bid": f"${s['bid']:.2f}",
            "Ask": f"${s['ask']:.2f}",
            "Spread": f"${s['ask']-s['bid']:.2f}",
            "Hit?": "✅ Yes" if inside else ("❌ No" if inside is False else "?"),
            "MM": "🏦" if t == market_maker else "",
            "You": "👈" if t == my_team else "",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
