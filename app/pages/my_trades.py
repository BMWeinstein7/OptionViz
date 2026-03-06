import streamlit as st
import json
import numpy as np
from datetime import datetime
from app.database import get_user_trades, close_trade, update_trade_current
from app.data import get_stock_quote, format_number
from app.pricing import black_scholes_price
import plotly.graph_objects as go


def render_my_trades_page():
    st.markdown("### My Trades")

    user = st.session_state.get("user")
    if not user or user.get("guest"):
        st.info("Sign in to save strategies and track trades.")
        return

    tab_open, tab_closed, tab_summary = st.tabs(["Open Trades", "Closed Trades", "Performance Summary"])

    with tab_open:
        _render_open_trades(user)

    with tab_closed:
        _render_closed_trades(user)

    with tab_summary:
        _render_performance_summary(user)


def _render_open_trades(user):
    trades = get_user_trades(user["id"], status="open")

    if not trades:
        st.info("No open trades. Save a strategy and open a trade from 'My Strategies'.")
        return

    if st.button("Refresh Prices", key="refresh_trades"):
        st.cache_data.clear()
        st.session_state["_refresh_trades"] = True

    for trade in trades:
        legs = trade["legs"] if isinstance(trade["legs"], list) else json.loads(trade["legs"])

        current_quote = None
        if trade.get("ticker"):
            current_quote = get_stock_quote(trade["ticker"])

        current_price = current_quote["price"] if current_quote else float(trade["entry_spot_price"])
        entry_price = float(trade["entry_spot_price"])
        entry_cost = float(trade["entry_cost"])

        current_pnl = _estimate_current_pnl(legs, entry_price, current_price, entry_cost)

        if st.session_state.get("_refresh_trades"):
            try:
                update_trade_current(trade["id"], current_price, entry_cost + current_pnl)
            except Exception:
                pass

        pnl_class = "trade-profit" if current_pnl >= 0 else "trade-loss"
        pnl_color = "#22c55e" if current_pnl >= 0 else "#ef4444"

        entry_date = trade["entry_date"]
        if isinstance(entry_date, str):
            entry_date = datetime.fromisoformat(entry_date)
        days_held = (datetime.now() - entry_date).days

        st.markdown(f"""<div class="strategy-card {pnl_class}">
            <h4>{trade['strategy_name']} — {trade.get('ticker', 'N/A')}</h4>
            <div class="meta">
                {trade.get('strategy_type', 'Custom')} | Opened: {entry_date.strftime('%b %d, %Y')} | Days held: {days_held}
            </div>
            <div class="trade-stats-row">
                <div>
                    <span style="color:#888; font-size:0.75rem;">ENTRY</span><br>
                    <span style="color:#ccc;">${entry_price:.2f}</span>
                </div>
                <div>
                    <span style="color:#888; font-size:0.75rem;">CURRENT</span><br>
                    <span style="color:#ccc;">${current_price:.2f}</span>
                </div>
                <div>
                    <span style="color:#888; font-size:0.75rem;">ENTRY COST</span><br>
                    <span style="color:#ccc;">${entry_cost:,.2f}</span>
                </div>
                <div>
                    <span style="color:#888; font-size:0.75rem;">EST. P&L</span><br>
                    <span style="color:{pnl_color}; font-weight:700;">${current_pnl:+,.2f}</span>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Close Trade", key=f"close_{trade['id']}"):
                st.session_state[f"show_close_{trade['id']}"] = True

        if st.session_state.get(f"show_close_{trade['id']}"):
            with st.form(f"close_form_{trade['id']}"):
                st.markdown("##### Close Trade")
                c1, c2 = st.columns(2)
                with c1:
                    exit_price = st.number_input("Exit Stock Price", min_value=0.01, value=current_price, key=f"exit_p_{trade['id']}")
                with c2:
                    realized = st.number_input("Realized P&L", value=round(current_pnl, 2), key=f"real_pnl_{trade['id']}")
                if st.form_submit_button("Confirm Close"):
                    close_trade(trade["id"], user["id"], exit_price, realized)
                    del st.session_state[f"show_close_{trade['id']}"]
                    st.success("Trade closed!")
                    st.rerun()

        if trade.get("notes"):
            st.caption(f"Notes: {trade['notes']}")

        st.markdown("---")


def _render_closed_trades(user):
    trades = get_user_trades(user["id"], status="closed")

    if not trades:
        st.info("No closed trades yet.")
        return

    for trade in trades:
        realized = float(trade.get("realized_pnl") or 0)
        pnl_class = "trade-profit" if realized >= 0 else "trade-loss"
        pnl_color = "#22c55e" if realized >= 0 else "#ef4444"

        entry_date = trade["entry_date"]
        exit_date = trade.get("exit_date")
        if isinstance(entry_date, str):
            entry_date = datetime.fromisoformat(entry_date)
        if isinstance(exit_date, str):
            exit_date = datetime.fromisoformat(exit_date)
        days_held = (exit_date - entry_date).days if exit_date else 0

        entry_cost = float(trade.get("entry_cost") or 0)
        pct_return = (realized / abs(entry_cost) * 100) if entry_cost != 0 else 0

        st.markdown(f"""<div class="strategy-card {pnl_class}">
            <h4>{trade['strategy_name']} — {trade.get('ticker', 'N/A')}</h4>
            <div class="meta">
                {trade.get('strategy_type', 'Custom')} | {entry_date.strftime('%b %d')} - {exit_date.strftime('%b %d, %Y') if exit_date else 'N/A'} | {days_held} days
            </div>
            <div class="trade-stats-row">
                <div>
                    <span style="color:#888; font-size:0.75rem;">ENTRY</span><br>
                    <span style="color:#ccc;">${float(trade['entry_spot_price']):.2f}</span>
                </div>
                <div>
                    <span style="color:#888; font-size:0.75rem;">EXIT</span><br>
                    <span style="color:#ccc;">${float(trade.get('exit_spot_price') or 0):.2f}</span>
                </div>
                <div>
                    <span style="color:#888; font-size:0.75rem;">COST</span><br>
                    <span style="color:#ccc;">${entry_cost:,.2f}</span>
                </div>
                <div>
                    <span style="color:#888; font-size:0.75rem;">P&L</span><br>
                    <span style="color:{pnl_color}; font-weight:700;">${realized:+,.2f} ({pct_return:+.1f}%)</span>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")


def _render_performance_summary(user):
    all_trades = get_user_trades(user["id"])
    closed = [t for t in all_trades if t["status"] == "closed"]
    open_trades = [t for t in all_trades if t["status"] == "open"]

    if not all_trades:
        st.info("No trades to analyze. Open some trades to see performance metrics.")
        return

    total_realized = sum(float(t.get("realized_pnl") or 0) for t in closed)
    winners = [t for t in closed if float(t.get("realized_pnl") or 0) > 0]
    losers = [t for t in closed if float(t.get("realized_pnl") or 0) < 0]
    win_rate = (len(winners) / len(closed) * 100) if closed else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="metric-card">
            <h4>Total Trades</h4>
            <p class="neutral">{len(all_trades)}</p>
        </div>""", unsafe_allow_html=True)
    with c2:
        pnl_class = "profit" if total_realized >= 0 else "loss"
        st.markdown(f"""<div class="metric-card">
            <h4>Total P&L</h4>
            <p class="{pnl_class}">${total_realized:+,.2f}</p>
        </div>""", unsafe_allow_html=True)
    with c3:
        wr_class = "profit" if win_rate >= 50 else "loss"
        st.markdown(f"""<div class="metric-card">
            <h4>Win Rate</h4>
            <p class="{wr_class}">{win_rate:.1f}%</p>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="metric-card">
            <h4>Open / Closed</h4>
            <p class="neutral">{len(open_trades)} / {len(closed)}</p>
        </div>""", unsafe_allow_html=True)

    if closed:
        avg_win = np.mean([float(t.get("realized_pnl") or 0) for t in winners]) if winners else 0
        avg_loss = np.mean([float(t.get("realized_pnl") or 0) for t in losers]) if losers else 0
        largest_win = max([float(t.get("realized_pnl") or 0) for t in closed]) if closed else 0
        largest_loss = min([float(t.get("realized_pnl") or 0) for t in closed]) if closed else 0

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""<div class="metric-card">
                <h4>Avg Win</h4>
                <p class="profit">${avg_win:+,.2f}</p>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="metric-card">
                <h4>Avg Loss</h4>
                <p class="loss">${avg_loss:+,.2f}</p>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class="metric-card">
                <h4>Best Trade</h4>
                <p class="profit">${largest_win:+,.2f}</p>
            </div>""", unsafe_allow_html=True)
        with c4:
            st.markdown(f"""<div class="metric-card">
                <h4>Worst Trade</h4>
                <p class="loss">${largest_loss:+,.2f}</p>
            </div>""", unsafe_allow_html=True)

        pnl_values = [float(t.get("realized_pnl") or 0) for t in closed]
        cumulative = np.cumsum(pnl_values)

        chart_bg = "rgba(6, 11, 24, 0.95)"
        chart_grid = "rgba(99, 179, 237, 0.06)"

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            y=cumulative, mode="lines+markers",
            line=dict(color="#3b82f6", width=2),
            marker=dict(size=6, color="#3b82f6"),
            name="Cumulative P&L",
        ))
        fig.add_hline(y=0, line_dash="dot", line_color="rgba(136, 146, 164, 0.3)", line_width=1)
        fig.update_layout(
            template="plotly_dark",
            plot_bgcolor=chart_bg,
            paper_bgcolor=chart_bg,
            font=dict(family="DM Sans, sans-serif", color="#8892a4"),
            yaxis_title="Cumulative P&L ($)",
            xaxis_title="Trade #",
            height=300,
            margin=dict(l=40, r=15, t=30, b=40),
            autosize=True,
            xaxis=dict(gridcolor=chart_grid, tickfont=dict(family="JetBrains Mono", size=10)),
            yaxis=dict(gridcolor=chart_grid, tickfont=dict(family="JetBrains Mono", size=10), tickprefix="$"),
        )
        st.plotly_chart(fig, use_container_width=True)


def _estimate_current_pnl(legs, entry_spot, current_spot, entry_cost):
    pnl = 0
    for leg in legs:
        if leg.get("type") == "stock":
            qty = leg["qty"]
            per_share = current_spot - entry_spot
            if leg["action"] == "sell":
                per_share = -per_share
            pnl += per_share * qty
        else:
            strike = leg["strike"]
            qty = leg["qty"]
            if leg["type"] == "call":
                intrinsic = max(current_spot - strike, 0)
            else:
                intrinsic = max(strike - current_spot, 0)

            contract_value = intrinsic * qty * 100
            premium_paid = leg["premium"] * qty * 100

            if leg["action"] == "buy":
                pnl += contract_value - premium_paid
            else:
                pnl += premium_paid - contract_value

    return pnl
