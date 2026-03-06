import streamlit as st
import json
from datetime import datetime
from app.database import (
    get_user_strategies, get_strategy_by_id, delete_strategy,
    save_strategy, create_trade, get_user_trades
)
from app.data import get_stock_quote, format_number


def render_my_strategies_page():
    st.markdown("### My Saved Strategies")

    user = st.session_state.get("user")
    if not user or user.get("guest"):
        st.info("Sign in to save strategies and track trades.")
        return

    strategies = get_user_strategies(user["id"])

    if not strategies:
        st.info("You haven't saved any strategies yet. Build one in the Strategy Builder and click 'Save Strategy'.")
        return

    for strat in strategies:
        legs = strat["legs"] if isinstance(strat["legs"], list) else json.loads(strat["legs"])
        leg_summary = []
        for leg in legs:
            if leg.get("type") == "stock":
                leg_summary.append(f"{'Long' if leg['action'] == 'buy' else 'Short'} {leg['qty']} Shares")
            else:
                leg_summary.append(f"{'Buy' if leg['action'] == 'buy' else 'Sell'} {leg['qty']}x {leg['type'].upper()} ${leg['strike']:.0f}")

        created = strat["created_at"]
        if isinstance(created, str):
            created = datetime.fromisoformat(created)
        date_str = created.strftime("%b %d, %Y %I:%M %p")

        ticker_str = f" ({strat['ticker']})" if strat.get("ticker") else ""
        type_str = strat.get("strategy_type") or "Custom"

        st.markdown(f"""<div class="strategy-card">
            <h4>{strat['name']}{ticker_str}</h4>
            <div class="meta">
                {type_str} | Spot: ${float(strat['spot_price']):.2f} | DTE: {strat['days_to_expiry']} | {date_str}
            </div>
            <div style="margin-top:0.5rem; color:#ccc; font-size:0.85rem;">
                {' | '.join(leg_summary)}
            </div>
        </div>""", unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("Load", key=f"load_{strat['id']}"):
                st.session_state.loaded_strategy = strat
                st.session_state.loaded_legs = legs
                st.info("Strategy loaded! Switch to Strategy Builder to view it.")
        with col2:
            if st.button("Open Trade", key=f"trade_{strat['id']}"):
                st.session_state[f"show_trade_form_{strat['id']}"] = True
        with col3:
            if st.button("Delete", key=f"del_{strat['id']}"):
                try:
                    delete_strategy(strat["id"], user["id"])
                    st.rerun()
                except Exception:
                    st.error("Could not delete strategy.")

        if st.session_state.get(f"show_trade_form_{strat['id']}"):
            _render_open_trade_form(strat, legs, user)

        st.markdown("---")


def _render_open_trade_form(strat, legs, user):
    with st.form(f"trade_form_{strat['id']}"):
        st.markdown("##### Open a Trade")
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            ticker = st.text_input("Ticker", value=strat.get("ticker") or "", key=f"t_ticker_{strat['id']}")
        with t_col2:
            entry_spot = st.number_input("Entry Stock Price", min_value=0.01, value=float(strat["spot_price"]), key=f"t_spot_{strat['id']}")

        total_cost = 0.0
        for leg in legs:
            if leg.get("type") == "stock":
                cost = leg.get("entry_price", leg["strike"]) * leg["qty"]
                total_cost += cost if leg["action"] == "buy" else -cost
            else:
                cost = leg["premium"] * leg["qty"] * 100
                total_cost += cost if leg["action"] == "buy" else -cost

        st.caption(f"Estimated entry cost: ${total_cost:,.2f}")
        notes = st.text_input("Notes (optional)", key=f"t_notes_{strat['id']}")

        if st.form_submit_button("Open Trade"):
            try:
                trade = create_trade(strat["id"], user["id"], ticker.upper(), entry_spot, total_cost, notes or None)
                if trade:
                    st.success("Trade opened!")
                    del st.session_state[f"show_trade_form_{strat['id']}"]
                    st.rerun()
                else:
                    st.error("Could not open trade.")
            except Exception:
                st.error("Could not open trade. Please try again.")


def render_save_strategy_form(selected_strategy, legs, spot_price, risk_free_rate, implied_vol, days_to_expiry, ticker=None):
    user = st.session_state.get("user")
    if not user:
        return

    if user.get("guest"):
        st.markdown("---")
        st.info("Sign in to save strategies and track trades.")
        return

    st.markdown("---")
    with st.expander("Save This Strategy"):
        with st.form("save_strategy_form"):
            default_name = selected_strategy if selected_strategy != "Custom" else "My Strategy"
            name = st.text_input("Strategy Name", value=default_name)
            notes = st.text_area("Notes (optional)", height=80)
            save_ticker = st.text_input("Ticker (optional)", value=ticker or "")

            if st.form_submit_button("Save Strategy"):
                if not name.strip():
                    st.error("Please enter a name.")
                else:
                    legs_data = []
                    for leg in legs:
                        legs_data.append({k: v for k, v in leg.items()})

                    try:
                        strat = save_strategy(
                            user_id=user["id"],
                            name=name.strip(),
                            strategy_type=selected_strategy,
                            legs=legs_data,
                            spot_price=spot_price,
                            risk_free_rate=risk_free_rate,
                            implied_vol=implied_vol,
                            days_to_expiry=days_to_expiry,
                            ticker=save_ticker.upper() if save_ticker.strip() else None,
                            notes=notes if notes.strip() else None,
                        )
                        if strat:
                            st.success(f"Strategy '{name}' saved!")
                        else:
                            st.error("Could not save strategy.")
                    except Exception:
                        st.error("Could not save strategy. Please try again.")
