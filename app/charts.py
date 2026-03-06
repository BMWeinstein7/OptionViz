import numpy as np
import plotly.graph_objects as go
from app.pricing import black_scholes_price


def calculate_leg_pnl(S_range, leg, r, sigma, T_remaining=0):
    strike = leg["strike"]
    qty = leg["qty"]
    premium = leg.get("premium", 0)
    action = leg["action"]
    option_type = leg["type"]
    multiplier = 100

    if option_type == "stock":
        entry_price = leg.get("entry_price", strike)
        if action == "buy":
            pnl = (S_range - entry_price) * qty
        else:
            pnl = (entry_price - S_range) * qty
        return pnl

    if T_remaining <= 0:
        if option_type == "call":
            intrinsic = np.maximum(S_range - strike, 0)
        else:
            intrinsic = np.maximum(strike - S_range, 0)
        value = intrinsic
    else:
        value = np.array([
            black_scholes_price(s, strike, T_remaining, r, sigma, option_type)
            for s in S_range
        ])

    if action == "buy":
        pnl = (value - premium) * qty * multiplier
    else:
        pnl = (premium - value) * qty * multiplier

    return pnl


def build_pnl_chart(legs, spot_price, r, sigma, days_to_expiry, title="P&L Diagram"):
    price_range = spot_price * 0.3
    S_range = np.linspace(
        max(spot_price - price_range, 1),
        spot_price + price_range,
        500
    )

    fig = go.Figure()

    T_expiry = 0
    total_pnl_expiry = np.zeros_like(S_range)
    for leg in legs:
        pnl = calculate_leg_pnl(S_range, leg, r, sigma, T_remaining=T_expiry)
        total_pnl_expiry += pnl

    fig.add_trace(go.Scatter(
        x=S_range, y=total_pnl_expiry,
        name="At Expiry",
        line=dict(color="#FF6B6B", width=3),
        hovertemplate="Price: $%{x:.2f}<br>P&L: $%{y:.2f}<extra></extra>"
    ))

    time_intervals = [0.75, 0.5, 0.25]
    colors = ["rgba(100, 200, 255, 0.6)", "rgba(100, 255, 150, 0.6)", "rgba(255, 200, 100, 0.6)"]

    for frac, color in zip(time_intervals, colors):
        T_remaining = (days_to_expiry * frac) / 365
        if T_remaining <= 0:
            continue
        total_pnl = np.zeros_like(S_range)
        for leg in legs:
            if leg["type"] == "stock":
                pnl = calculate_leg_pnl(S_range, leg, r, sigma, T_remaining=0)
            else:
                dte_mult = leg.get("dte_multiplier", 1.0)
                pnl = calculate_leg_pnl(S_range, leg, r, sigma, T_remaining=T_remaining * dte_mult)
            total_pnl += pnl

        days_label = int(days_to_expiry * frac)
        fig.add_trace(go.Scatter(
            x=S_range, y=total_pnl,
            name=f"{days_label} DTE",
            line=dict(color=color, width=2, dash="dash"),
            hovertemplate="Price: $%{x:.2f}<br>P&L: $%{y:.2f}<extra></extra>"
        ))

    fig.add_hline(y=0, line_dash="dot", line_color="gray", opacity=0.5)
    fig.add_vline(x=spot_price, line_dash="dot", line_color="white", opacity=0.3,
                  annotation_text=f"Current: ${spot_price:.2f}",
                  annotation_position="top")

    for leg in legs:
        if leg["type"] != "stock":
            fig.add_vline(x=leg["strike"], line_dash="dot", line_color="rgba(255,255,255,0.15)",
                          annotation_text=f"${leg['strike']}", annotation_position="bottom")

    breakevens = []
    for i in range(len(S_range) - 1):
        if total_pnl_expiry[i] * total_pnl_expiry[i + 1] < 0:
            x_be = S_range[i] - total_pnl_expiry[i] * (S_range[i + 1] - S_range[i]) / (total_pnl_expiry[i + 1] - total_pnl_expiry[i])
            breakevens.append(x_be)

    for be in breakevens:
        fig.add_vline(x=be, line_dash="dashdot", line_color="#FFD700", opacity=0.7,
                      annotation_text=f"BE: ${be:.2f}", annotation_position="top right",
                      annotation_font_color="#FFD700")

    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color="white")),
        xaxis_title="Stock Price ($)",
        yaxis_title="Profit / Loss ($)",
        template="plotly_dark",
        plot_bgcolor="rgba(17,17,17,0.9)",
        paper_bgcolor="rgba(17,17,17,0.9)",
        hovermode="x unified",
        legend=dict(
            yanchor="top", y=0.99,
            xanchor="left", x=0.01,
            bgcolor="rgba(0,0,0,0.5)",
            font=dict(color="white", size=10)
        ),
        margin=dict(l=40, r=15, t=50, b=40),
        height=400,
        autosize=True,
    )

    return fig, breakevens, total_pnl_expiry


def build_greek_chart(legs, spot_price, r, sigma, days_to_expiry, greek_name="delta"):
    from app.pricing import calculate_greeks

    price_range = spot_price * 0.3
    S_range = np.linspace(max(spot_price - price_range, 1), spot_price + price_range, 200)
    T = days_to_expiry / 365

    total_greek = np.zeros_like(S_range)

    for leg in legs:
        if leg["type"] == "stock":
            if greek_name == "delta":
                qty = leg["qty"]
                if leg["action"] == "buy":
                    total_greek += np.ones_like(S_range) * qty / 100
                else:
                    total_greek -= np.ones_like(S_range) * qty / 100
            continue

        strike = leg["strike"]
        qty = leg["qty"]
        action = leg["action"]
        option_type = leg["type"]
        dte_mult = leg.get("dte_multiplier", 1.0)
        T_leg = T * dte_mult

        for i, s in enumerate(S_range):
            greeks = calculate_greeks(s, strike, T_leg, r, sigma, option_type)
            val = greeks.get(greek_name, 0)
            if action == "buy":
                total_greek[i] += val * qty
            else:
                total_greek[i] -= val * qty

    color_map = {
        "delta": "#4ECDC4",
        "gamma": "#FF6B6B",
        "theta": "#FFE66D",
        "vega": "#A06CD5",
        "rho": "#95E1D3",
    }

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=S_range, y=total_greek,
        name=greek_name.capitalize(),
        line=dict(color=color_map.get(greek_name, "#4ECDC4"), width=2),
        fill="tozeroy",
        fillcolor=f"rgba{tuple(list(int(color_map.get(greek_name, '#4ECDC4').lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + [0.15])}",
        hovertemplate="Price: $%{x:.2f}<br>" + greek_name.capitalize() + ": %{y:.4f}<extra></extra>"
    ))

    fig.add_vline(x=spot_price, line_dash="dot", line_color="white", opacity=0.3)
    fig.add_hline(y=0, line_dash="dot", line_color="gray", opacity=0.5)

    fig.update_layout(
        title=dict(text=f"{greek_name.capitalize()} vs Stock Price", font=dict(size=14, color="white")),
        xaxis_title="Stock Price ($)",
        yaxis_title=greek_name.capitalize(),
        template="plotly_dark",
        plot_bgcolor="rgba(17,17,17,0.9)",
        paper_bgcolor="rgba(17,17,17,0.9)",
        height=300,
        margin=dict(l=40, r=15, t=40, b=40),
        autosize=True,
    )

    return fig
