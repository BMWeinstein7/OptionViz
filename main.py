import streamlit as st
import streamlit.components.v1 as stc
import numpy as np
import pandas as pd
from app.page_config import setup_page
from app.pricing import black_scholes_price, calculate_greeks
from app.strategies import STRATEGY_TEMPLATES, get_strategy_legs
from app.charts import build_pnl_chart, build_greek_chart
from app.data import (
    TOP_TICKERS, get_stock_quote, get_options_expirations,
    get_options_chain, get_options_flow, get_put_call_ratio, format_number,
)
from app.pages.auth_page import render_auth_page, render_user_sidebar, _is_guest
from app.pages.my_strategies import render_my_strategies_page, render_save_strategy_form
from app.pages.my_trades import render_my_trades_page
import plotly.graph_objects as go

setup_page()

if "user" not in st.session_state:
    render_auth_page()
    st.stop()

render_user_sidebar()

user = st.session_state.user

st.markdown('<p class="strategy-header">OptionViz</p>', unsafe_allow_html=True)
st.caption("Options Strategy Builder & Visualizer with Live Market Data")

if _is_guest():
    nav_options = ["Strategy Builder", "Market Data", "Options Chain", "Options Flow"]
else:
    nav_options = ["Strategy Builder", "Market Data", "Options Chain", "Options Flow", "My Strategies", "My Trades"]

page = st.sidebar.radio(
    "Navigation",
    nav_options,
    label_visibility="collapsed",
)

stc.html("""
<script>
(function() {
    var doc = window.parent.document;
    if (doc._optionviz_sidebar_bound) return;
    doc._optionviz_sidebar_bound = true;

    function collapseSidebar() {
        var sidebar = doc.querySelector('[data-testid="stSidebar"]');
        if (!sidebar) return;
        var selectors = [
            '[data-testid="stSidebar"] button[kind="headerNoPadding"]',
            'button[data-testid="baseButton-headerNoPadding"]',
            '[data-testid="stSidebar"] [data-testid="collapsedControl"]'
        ];
        for (var i = 0; i < selectors.length; i++) {
            var btn = doc.querySelector(selectors[i]);
            if (btn) { btn.click(); return; }
        }
        sidebar.setAttribute('aria-expanded', 'false');
    }

    var sidebar = doc.querySelector('[data-testid="stSidebar"]');
    if (!sidebar) return;
    sidebar.addEventListener('click', function(e) {
        var radio = e.target.closest('label');
        if (!radio) return;
        var input = radio.querySelector('input[type="radio"]');
        if (!input) return;
        setTimeout(collapseSidebar, 200);
    });
})();
</script>
""", height=0)


if page == "My Strategies":
    render_my_strategies_page()

elif page == "My Trades":
    render_my_trades_page()

elif page == "Market Data":
    st.markdown("### Live Market Data — Top Tickers")

    search = st.text_input("Search ticker", placeholder="Type to filter (e.g. AAPL, TSLA)...")
    filtered = [t for t in TOP_TICKERS if search.upper() in t] if search else TOP_TICKERS

    batch_size = st.selectbox("Show", [10, 25, 50, 100], index=0)
    tickers_to_show = filtered[:batch_size]

    if st.button("Refresh Prices"):
        st.cache_data.clear()

    if not tickers_to_show:
        st.warning("No tickers match your search.")
        st.stop()

    with st.spinner("Fetching live quotes..."):
        quotes = []
        for t in tickers_to_show:
            q = get_stock_quote(t)
            if q:
                quotes.append(q)

    if not quotes:
        st.error("Could not fetch any quotes. Please try again.")
        st.stop()

    df = pd.DataFrame(quotes)
    df = df.rename(columns={
        "ticker": "Ticker",
        "price": "Price",
        "change": "Chg",
        "change_pct": "Chg%",
        "volume": "Volume",
        "day_high": "High",
        "day_low": "Low",
    })

    display_cols = ["Ticker", "Price", "Chg", "Chg%", "Volume", "High", "Low"]
    display_df = df[display_cols].copy()

    def color_change(val):
        if isinstance(val, (int, float)):
            if val > 0:
                return "color: #00E676"
            elif val < 0:
                return "color: #FF5252"
        return ""

    styled = display_df.style.map(color_change, subset=["Chg", "Chg%"])
    styled = styled.format({
        "Price": "${:.2f}",
        "Chg": "{:+.2f}",
        "Chg%": "{:+.2f}%",
        "Volume": "{:,.0f}",
        "High": "${:.2f}",
        "Low": "${:.2f}",
    })

    st.dataframe(styled, use_container_width=True, height=min(len(display_df) * 38 + 40, 600))

    st.markdown("---")
    st.markdown("##### Quick Quote")
    quick_ticker = st.selectbox("Select ticker for details", TOP_TICKERS, key="quick_quote")
    if quick_ticker:
        q = get_stock_quote(quick_ticker)
        if q:
            c1, c2, c3, c4 = st.columns(4)
            chg_class = "profit" if q["change"] >= 0 else "loss"
            with c1:
                st.markdown(f"""<div class="metric-card">
                    <h4>{q['ticker']}</h4>
                    <p class="{chg_class}">${q['price']:.2f}</p>
                </div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""<div class="metric-card">
                    <h4>Change</h4>
                    <p class="{chg_class}">{q['change']:+.2f} ({q['change_pct']:+.2f}%)</p>
                </div>""", unsafe_allow_html=True)
            with c3:
                st.markdown(f"""<div class="metric-card">
                    <h4>Day Range</h4>
                    <p class="neutral">${q['day_low']:.2f} - ${q['day_high']:.2f}</p>
                </div>""", unsafe_allow_html=True)
            with c4:
                vol_str = format_number(q['volume']) if q['volume'] else "N/A"
                st.markdown(f"""<div class="metric-card">
                    <h4>Volume</h4>
                    <p class="neutral">{vol_str}</p>
                </div>""", unsafe_allow_html=True)

elif page == "Options Chain":
    st.markdown("### Options Chain")

    col1, col2 = st.columns([1, 2])
    with col1:
        chain_ticker = st.selectbox("Ticker", TOP_TICKERS, key="chain_ticker")
    with col2:
        if chain_ticker:
            quote = get_stock_quote(chain_ticker)
            if quote:
                chg_class = "profit" if quote["change"] >= 0 else "loss"
                st.markdown(f"""<div class="metric-card" style="margin-top:0.5rem">
                    <h4>{chain_ticker}</h4>
                    <p class="{chg_class}">${quote['price']:.2f} &nbsp; {quote['change']:+.2f} ({quote['change_pct']:+.2f}%)</p>
                </div>""", unsafe_allow_html=True)

    expirations = get_options_expirations(chain_ticker)

    if not expirations:
        st.warning(f"No options available for {chain_ticker}.")
        st.stop()

    selected_exp = st.selectbox("Expiration Date", expirations)

    if selected_exp:
        with st.spinner("Loading options chain..."):
            calls, puts = get_options_chain(chain_ticker, selected_exp)

        if calls.empty and puts.empty:
            st.warning("No options data available for this expiration.")
            st.stop()

        from datetime import datetime
        exp_date = datetime.strptime(selected_exp, "%Y-%m-%d")
        dte = (exp_date - datetime.now()).days
        st.caption(f"Days to expiry: **{dte}**")

        chain_cols = ["strike", "lastPrice", "bid", "ask", "volume", "openInterest", "impliedVolatility", "inTheMoney"]
        col_rename = {
            "strike": "Strike",
            "lastPrice": "Last",
            "bid": "Bid",
            "ask": "Ask",
            "volume": "Vol",
            "openInterest": "OI",
            "impliedVolatility": "IV%",
            "inTheMoney": "ITM",
        }

        tab_calls, tab_puts, tab_combined = st.tabs(["Calls", "Puts", "Combined View"])

        with tab_calls:
            if not calls.empty:
                available = [c for c in chain_cols if c in calls.columns]
                display = calls[available].rename(columns=col_rename)
                st.dataframe(display, use_container_width=True, height=400)
                st.caption(f"{len(calls)} call contracts")
            else:
                st.info("No call data available.")

        with tab_puts:
            if not puts.empty:
                available = [c for c in chain_cols if c in puts.columns]
                display = puts[available].rename(columns=col_rename)
                st.dataframe(display, use_container_width=True, height=400)
                st.caption(f"{len(puts)} put contracts")
            else:
                st.info("No put data available.")

        with tab_combined:
            if not calls.empty and not puts.empty:
                spot = quote["price"] if quote else 0

                call_display = calls[["strike", "lastPrice", "bid", "ask", "volume", "openInterest", "impliedVolatility"]].copy()
                call_display.columns = ["Strike", "C.Last", "C.Bid", "C.Ask", "C.Vol", "C.OI", "C.IV%"]

                put_display = puts[["strike", "lastPrice", "bid", "ask", "volume", "openInterest", "impliedVolatility"]].copy()
                put_display.columns = ["Strike", "P.Last", "P.Bid", "P.Ask", "P.Vol", "P.OI", "P.IV%"]

                combined = pd.merge(call_display, put_display, on="Strike", how="outer").sort_values("Strike")
                st.dataframe(combined, use_container_width=True, height=500)

                st.markdown("##### Open Interest by Strike")
                oi_fig = go.Figure()
                if not calls.empty:
                    oi_fig.add_trace(go.Bar(
                        x=calls["strike"], y=calls["openInterest"],
                        name="Call OI", marker_color="#00E676", opacity=0.7,
                    ))
                if not puts.empty:
                    oi_fig.add_trace(go.Bar(
                        x=puts["strike"], y=puts["openInterest"],
                        name="Put OI", marker_color="#FF5252", opacity=0.7,
                    ))
                if spot:
                    oi_fig.add_vline(x=spot, line_dash="dot", line_color="white", opacity=0.5,
                                     annotation_text=f"${spot:.2f}")
                oi_fig.update_layout(
                    template="plotly_dark",
                    plot_bgcolor="rgba(17,17,17,0.9)",
                    paper_bgcolor="rgba(17,17,17,0.9)",
                    barmode="group", height=300,
                    margin=dict(l=40, r=15, t=30, b=40),
                    autosize=True,
                )
                st.plotly_chart(oi_fig, use_container_width=True)

                st.markdown("##### IV Smile")
                iv_fig = go.Figure()
                if not calls.empty:
                    iv_fig.add_trace(go.Scatter(
                        x=calls["strike"], y=calls["impliedVolatility"],
                        name="Call IV", line=dict(color="#4ECDC4", width=2),
                    ))
                if not puts.empty:
                    iv_fig.add_trace(go.Scatter(
                        x=puts["strike"], y=puts["impliedVolatility"],
                        name="Put IV", line=dict(color="#FF6B6B", width=2),
                    ))
                if spot:
                    iv_fig.add_vline(x=spot, line_dash="dot", line_color="white", opacity=0.5)
                iv_fig.update_layout(
                    template="plotly_dark",
                    plot_bgcolor="rgba(17,17,17,0.9)",
                    paper_bgcolor="rgba(17,17,17,0.9)",
                    yaxis_title="IV (%)", xaxis_title="Strike ($)",
                    height=300,
                    margin=dict(l=40, r=15, t=30, b=40),
                    autosize=True,
                )
                st.plotly_chart(iv_fig, use_container_width=True)

elif page == "Options Flow":
    st.markdown("### Options Flow Scanner")

    flow_col1, flow_col2 = st.columns([1, 2])
    with flow_col1:
        flow_ticker = st.selectbox("Ticker", TOP_TICKERS, key="flow_ticker")
    with flow_col2:
        if flow_ticker:
            quote = get_stock_quote(flow_ticker)
            if quote:
                chg_class = "profit" if quote["change"] >= 0 else "loss"
                st.markdown(f"""<div class="metric-card" style="margin-top:0.5rem">
                    <h4>{flow_ticker}</h4>
                    <p class="{chg_class}">${quote['price']:.2f} &nbsp; {quote['change']:+.2f} ({quote['change_pct']:+.2f}%)</p>
                </div>""", unsafe_allow_html=True)

    if st.button("Refresh Flow Data"):
        st.cache_data.clear()

    pcr = get_put_call_ratio(flow_ticker)
    if pcr:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            pcr_class = "loss" if pcr["vol_ratio"] > 1 else "profit"
            st.markdown(f"""<div class="metric-card">
                <h4>P/C Vol Ratio</h4>
                <p class="{pcr_class}">{pcr['vol_ratio']:.3f}</p>
            </div>""", unsafe_allow_html=True)
        with c2:
            pcr_oi_class = "loss" if pcr["oi_ratio"] > 1 else "profit"
            st.markdown(f"""<div class="metric-card">
                <h4>P/C OI Ratio</h4>
                <p class="{pcr_oi_class}">{pcr['oi_ratio']:.3f}</p>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class="metric-card">
                <h4>Total Call Vol</h4>
                <p class="profit">{format_number(pcr['total_call_vol'])}</p>
            </div>""", unsafe_allow_html=True)
        with c4:
            st.markdown(f"""<div class="metric-card">
                <h4>Total Put Vol</h4>
                <p class="loss">{format_number(pcr['total_put_vol'])}</p>
            </div>""", unsafe_allow_html=True)

    with st.spinner("Scanning options flow..."):
        flow_df = get_options_flow(flow_ticker)

    if flow_df.empty:
        st.warning(f"No options flow data available for {flow_ticker}.")
        st.stop()

    st.markdown("##### Highest Volume Contracts")

    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        type_filter = st.selectbox("Type", ["All", "CALL", "PUT"], key="flow_type")
    with filter_col2:
        min_vol = st.number_input("Min Volume", 0, 100000, 100, key="flow_min_vol")
    with filter_col3:
        vol_oi_min = st.number_input("Min Vol/OI", 0.0, 100.0, 0.0, 0.1, key="flow_vol_oi")

    filtered = flow_df.copy()
    if type_filter != "All":
        filtered = filtered[filtered["Type"] == type_filter]
    filtered = filtered[filtered["Volume"] >= min_vol]
    if vol_oi_min > 0:
        filtered = filtered[filtered["Vol/OI"] >= vol_oi_min]

    def style_flow(row):
        color = "#00E676" if row["Type"] == "CALL" else "#FF5252"
        return [f"color: {color}"] * len(row)

    if not filtered.empty:
        st.dataframe(
            filtered.head(50).style.apply(style_flow, axis=1),
            use_container_width=True,
            height=min(len(filtered.head(50)) * 38 + 40, 500),
        )
        st.caption(f"Showing top {min(50, len(filtered))} of {len(filtered)} contracts")

        st.markdown("##### Volume by Strike")
        vol_fig = go.Figure()

        call_flow = filtered[filtered["Type"] == "CALL"]
        put_flow = filtered[filtered["Type"] == "PUT"]

        if not call_flow.empty:
            call_agg = call_flow.groupby("Strike")["Volume"].sum().reset_index()
            vol_fig.add_trace(go.Bar(
                x=call_agg["Strike"], y=call_agg["Volume"],
                name="Call Volume", marker_color="#00E676", opacity=0.8,
            ))
        if not put_flow.empty:
            put_agg = put_flow.groupby("Strike")["Volume"].sum().reset_index()
            vol_fig.add_trace(go.Bar(
                x=put_agg["Strike"], y=put_agg["Volume"],
                name="Put Volume", marker_color="#FF5252", opacity=0.8,
            ))

        if quote:
            vol_fig.add_vline(x=quote["price"], line_dash="dot", line_color="white", opacity=0.5,
                              annotation_text=f"${quote['price']:.2f}")

        vol_fig.update_layout(
            template="plotly_dark",
            plot_bgcolor="rgba(17,17,17,0.9)",
            paper_bgcolor="rgba(17,17,17,0.9)",
            barmode="group", height=300,
            margin=dict(l=40, r=15, t=30, b=40),
            autosize=True,
        )
        st.plotly_chart(vol_fig, use_container_width=True)

        st.markdown("##### Unusual Activity (High Vol/OI)")
        unusual = filtered[filtered["Vol/OI"] >= 2.0].sort_values("Vol/OI", ascending=False).head(20)
        if not unusual.empty:
            st.dataframe(unusual, use_container_width=True)
            st.caption("Contracts where today's volume is 2x or more the open interest — may indicate new positioning.")
        else:
            st.info("No unusual activity detected with Vol/OI >= 2.0")
    else:
        st.info("No contracts match your filters.")

else:
    live_ticker_value = None

    with st.sidebar:
        st.markdown("---")
        st.markdown("### Market Parameters")

        use_live = st.checkbox("Use live ticker data", value=False)
        if use_live:
            live_ticker = st.selectbox("Ticker", TOP_TICKERS, key="strat_ticker")
            live_ticker_value = live_ticker
            live_quote = get_stock_quote(live_ticker)
            if live_quote:
                spot_price = live_quote["price"]
                st.markdown(f"""<div class="metric-card">
                    <h4>{live_ticker}</h4>
                    <p class="{'profit' if live_quote['change'] >= 0 else 'loss'}">${spot_price:.2f}</p>
                </div>""", unsafe_allow_html=True)

                live_exps = get_options_expirations(live_ticker)
                if live_exps:
                    live_exp = st.selectbox("Expiration", live_exps, key="strat_exp")
                    from datetime import datetime
                    exp_dt = datetime.strptime(live_exp, "%Y-%m-%d")
                    days_to_expiry = max((exp_dt - datetime.now()).days, 1)
                    st.caption(f"DTE: {days_to_expiry}")
                else:
                    days_to_expiry = st.slider("Days to Expiry", 1, 365, 30, 1)
            else:
                spot_price = st.number_input("Stock Price ($)", min_value=1.0, max_value=10000.0, value=100.0, step=1.0)
                days_to_expiry = st.slider("Days to Expiry", 1, 365, 30, 1)
        else:
            spot_price = st.number_input("Stock Price ($)", min_value=1.0, max_value=10000.0, value=100.0, step=1.0)
            days_to_expiry = st.slider("Days to Expiry", 1, 365, 30, 1)

        risk_free_rate = st.slider("Risk-Free Rate (%)", 0.0, 15.0, 5.0, 0.25) / 100
        implied_vol = st.slider("Implied Volatility (%)", 5.0, 150.0, 30.0, 1.0) / 100

        st.markdown("---")
        st.markdown("### Strategy")

        strategy_names = ["Custom"] + list(STRATEGY_TEMPLATES.keys())
        selected_strategy = st.selectbox("Strategy Template", strategy_names)

        if selected_strategy != "Custom":
            tmpl = STRATEGY_TEMPLATES[selected_strategy]
            sentiment = tmpl["sentiment"]

            if "bullish" in sentiment.lower():
                badge_class = "bullish"
            elif "bearish" in sentiment.lower():
                badge_class = "bearish"
            elif "volatile" in sentiment.lower():
                badge_class = "volatile"
            else:
                badge_class = "neutral-badge"

            st.markdown(f'<span class="sentiment-badge {badge_class}">{sentiment}</span>', unsafe_allow_html=True)
            st.caption(tmpl["description"])

    loaded = st.session_state.get("loaded_strategy")
    if loaded and "loaded_legs" in st.session_state:
        spot_price = float(loaded["spot_price"])
        days_to_expiry = loaded["days_to_expiry"]
        risk_free_rate = float(loaded["risk_free_rate"])
        implied_vol = float(loaded["implied_vol"])
        st.session_state.legs = st.session_state.loaded_legs
        selected_strategy = loaded.get("strategy_type") or "Custom"
        del st.session_state.loaded_strategy
        del st.session_state.loaded_legs

    if "legs" not in st.session_state:
        st.session_state.legs = []

    if selected_strategy != "Custom" and "loaded_strategy" not in st.session_state:
        template_legs = get_strategy_legs(selected_strategy, spot_price)
        processed_legs = []
        for leg in template_legs:
            if leg["type"] == "stock":
                processed_legs.append({
                    "type": "stock",
                    "action": leg["action"],
                    "qty": leg["qty"],
                    "strike": spot_price,
                    "entry_price": spot_price,
                })
            else:
                T = (days_to_expiry / 365) * leg.get("dte_multiplier", 1.0)
                premium = black_scholes_price(spot_price, leg["strike"], T, risk_free_rate, implied_vol, leg["type"])
                processed_legs.append({
                    "type": leg["type"],
                    "action": leg["action"],
                    "qty": leg["qty"],
                    "strike": leg["strike"],
                    "premium": round(premium, 2),
                    "dte_multiplier": leg.get("dte_multiplier", 1.0),
                })
        st.session_state.legs = processed_legs

    with st.sidebar:
        st.markdown("---")
        st.markdown("### Option Legs")

        if selected_strategy == "Custom":
            num_legs = st.number_input("Number of Legs", 1, 8, 1, key="num_legs")

            custom_legs = []
            for i in range(int(num_legs)):
                with st.expander(f"Leg {i + 1}", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        opt_type = st.selectbox("Type", ["call", "put"], key=f"type_{i}")
                    with col2:
                        action = st.selectbox("Action", ["buy", "sell"], key=f"action_{i}")

                    strike = st.number_input("Strike ($)", 1.0, 10000.0, spot_price, 1.0, key=f"strike_{i}")
                    qty = st.number_input("Quantity", 1, 100, 1, key=f"qty_{i}")

                    T = days_to_expiry / 365
                    auto_premium = black_scholes_price(spot_price, strike, T, risk_free_rate, implied_vol, opt_type)
                    premium = st.number_input("Premium ($)", 0.01, 10000.0, round(auto_premium, 2), 0.01, key=f"prem_{i}")

                    custom_legs.append({
                        "type": opt_type,
                        "action": action,
                        "qty": qty,
                        "strike": strike,
                        "premium": premium,
                        "dte_multiplier": 1.0,
                    })

            st.session_state.legs = custom_legs
        else:
            for i, leg in enumerate(st.session_state.legs):
                if leg["type"] == "stock":
                    st.markdown(f"""<div class="leg-card">
                        <strong>{'Long' if leg['action'] == 'buy' else 'Short'} {leg['qty']} Shares</strong><br>
                        <small>@ ${leg.get('entry_price', spot_price):.2f}</small>
                    </div>""", unsafe_allow_html=True)
                else:
                    color = "#00E676" if leg["action"] == "buy" else "#FF5252"
                    st.markdown(f"""<div class="leg-card">
                        <strong style="color:{color}">{'BUY' if leg['action'] == 'buy' else 'SELL'} {leg['qty']}x {leg['type'].upper()}</strong><br>
                        <small>Strike: ${leg['strike']:.2f} | Premium: ${leg['premium']:.2f}</small>
                    </div>""", unsafe_allow_html=True)

    legs = st.session_state.legs

    if not legs:
        st.info("Add option legs using the sidebar to get started.")
        st.stop()

    total_cost = 0
    for leg in legs:
        if leg["type"] == "stock":
            if leg["action"] == "buy":
                total_cost += leg.get("entry_price", leg["strike"]) * leg["qty"]
            else:
                total_cost -= leg.get("entry_price", leg["strike"]) * leg["qty"]
        else:
            if leg["action"] == "buy":
                total_cost += leg["premium"] * leg["qty"] * 100
            else:
                total_cost -= leg["premium"] * leg["qty"] * 100

    fig, breakevens, pnl_at_expiry = build_pnl_chart(
        legs, spot_price, risk_free_rate, implied_vol, days_to_expiry,
        title=f"{selected_strategy} P&L Diagram" if selected_strategy != "Custom" else "Custom Strategy P&L"
    )

    max_profit = np.max(pnl_at_expiry)
    max_loss = np.min(pnl_at_expiry)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        cost_class = "loss" if total_cost > 0 else "profit"
        st.markdown(f"""<div class="metric-card">
            <h4>Net Cost</h4>
            <p class="{cost_class}">${abs(total_cost):,.2f} {'Debit' if total_cost > 0 else 'Credit'}</p>
        </div>""", unsafe_allow_html=True)

    with col2:
        mp_class = "profit" if max_profit > 0 else "neutral"
        mp_display = "Unlimited" if max_profit > spot_price * 50 else f"${max_profit:,.2f}"
        st.markdown(f"""<div class="metric-card">
            <h4>Max Profit</h4>
            <p class="{mp_class}">{mp_display}</p>
        </div>""", unsafe_allow_html=True)

    with col3:
        ml_class = "loss" if max_loss < 0 else "neutral"
        ml_display = "Unlimited" if max_loss < -spot_price * 50 else f"${max_loss:,.2f}"
        st.markdown(f"""<div class="metric-card">
            <h4>Max Loss</h4>
            <p class="{ml_class}">{ml_display}</p>
        </div>""", unsafe_allow_html=True)

    with col4:
        be_text = " / ".join([f"${b:.2f}" for b in breakevens]) if breakevens else "N/A"
        st.markdown(f"""<div class="metric-card">
            <h4>Break Even</h4>
            <p class="neutral">{be_text}</p>
        </div>""", unsafe_allow_html=True)

    st.plotly_chart(fig, use_container_width=True)

    render_save_strategy_form(
        selected_strategy, legs, spot_price, risk_free_rate, implied_vol, days_to_expiry,
        ticker=live_ticker_value,
    )

    tab1, tab2, tab3 = st.tabs(["Greeks", "Greeks Charts", "Position Details"])

    with tab1:
        T = days_to_expiry / 365

        total_greeks = {"delta": 0, "gamma": 0, "theta": 0, "vega": 0, "rho": 0}

        for leg in legs:
            if leg["type"] == "stock":
                qty = leg["qty"]
                if leg["action"] == "buy":
                    total_greeks["delta"] += qty / 100
                else:
                    total_greeks["delta"] -= qty / 100
                continue

            T_leg = T * leg.get("dte_multiplier", 1.0)
            greeks = calculate_greeks(spot_price, leg["strike"], T_leg, risk_free_rate, implied_vol, leg["type"])

            multiplier = leg["qty"] if leg["action"] == "buy" else -leg["qty"]
            for g in total_greeks:
                total_greeks[g] += greeks[g] * multiplier

        gcols = st.columns(5)
        greek_info = [
            ("Delta", total_greeks["delta"], "Directional exposure"),
            ("Gamma", total_greeks["gamma"], "Rate of delta change"),
            ("Theta", total_greeks["theta"], "Daily time decay"),
            ("Vega", total_greeks["vega"], "Volatility sensitivity"),
            ("Rho", total_greeks["rho"], "Interest rate sensitivity"),
        ]

        for col, (name, value, desc) in zip(gcols, greek_info):
            with col:
                v_class = "profit" if value > 0 else "loss" if value < 0 else "neutral"
                st.markdown(f"""<div class="metric-card">
                    <h4>{name}</h4>
                    <p class="{v_class}">{value:+.4f}</p>
                    <small style="color:#666">{desc}</small>
                </div>""", unsafe_allow_html=True)

    with tab2:
        greek_select = st.selectbox("Select Greek", ["delta", "gamma", "theta", "vega", "rho"])
        greek_fig = build_greek_chart(legs, spot_price, risk_free_rate, implied_vol, days_to_expiry, greek_select)
        st.plotly_chart(greek_fig, use_container_width=True)

    with tab3:
        st.markdown("#### Position Summary")

        for i, leg in enumerate(legs):
            if leg["type"] == "stock":
                direction = "LONG" if leg["action"] == "buy" else "SHORT"
                cost = leg.get("entry_price", leg["strike"]) * leg["qty"]
                st.markdown(f"""
                **Leg {i+1}:** {direction} {leg['qty']} Shares @ ${leg.get('entry_price', leg['strike']):.2f}
                | Cost: ${cost:,.2f}
                """)
            else:
                direction = "LONG" if leg["action"] == "buy" else "SHORT"
                total = leg["premium"] * leg["qty"] * 100
                dte_label = int(days_to_expiry * leg.get("dte_multiplier", 1.0))
                st.markdown(f"""
                **Leg {i+1}:** {direction} {leg['qty']}x {leg['type'].upper()} @ Strike ${leg['strike']:.2f}
                | Premium: ${leg['premium']:.2f} | Total: ${total:,.2f} | DTE: {dte_label}
                """)

        st.markdown("---")

        if max_profit > spot_price * 50:
            st.success("This strategy has **unlimited profit potential** on the upside.")
        if max_loss < -spot_price * 50:
            st.error("This strategy has **unlimited loss potential**. Consider adding protection.")

        if total_cost > 0:
            if max_profit > 0:
                risk_reward = abs(max_profit / total_cost) if total_cost != 0 else float('inf')
                st.metric("Risk/Reward Ratio", f"{risk_reward:.2f}x")
        elif total_cost < 0:
            st.info(f"This is a **credit** strategy. You collect ${abs(total_cost):,.2f} upfront.")

