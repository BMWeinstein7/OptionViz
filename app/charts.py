import numpy as np
import plotly.graph_objects as go
from app.pricing import black_scholes_price

CHART_BG = "rgba(6, 11, 24, 0.95)"
CHART_GRID = "rgba(99, 179, 237, 0.06)"
CHART_FONT = dict(family="DM Sans, -apple-system, sans-serif", color="#8892a4")
GREEN = "#22c55e"
RED = "#ef4444"
BLUE = "#3b82f6"
AMBER = "#f59e0b"


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

    profit_y = np.where(total_pnl_expiry >= 0, total_pnl_expiry, 0)
    loss_y = np.where(total_pnl_expiry <= 0, total_pnl_expiry, 0)

    fig.add_trace(go.Scatter(
        x=S_range, y=profit_y,
        name="Profit Zone",
        line=dict(width=0),
        fill="tozeroy",
        fillcolor="rgba(34, 197, 94, 0.12)",
        hoverinfo="skip",
        showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=S_range, y=loss_y,
        name="Loss Zone",
        line=dict(width=0),
        fill="tozeroy",
        fillcolor="rgba(239, 68, 68, 0.12)",
        hoverinfo="skip",
        showlegend=False,
    ))

    fig.add_trace(go.Scatter(
        x=S_range, y=total_pnl_expiry,
        name="At Expiry",
        line=dict(color="#e8edf5", width=2.5),
        hovertemplate="Price: $%{x:.2f}<br>P&L: $%{y:.2f}<extra></extra>"
    ))

    time_intervals = [0.75, 0.5, 0.25]
    time_colors = [
        "rgba(59, 130, 246, 0.5)",
        "rgba(139, 92, 246, 0.5)",
        "rgba(245, 158, 11, 0.5)",
    ]

    for frac, color in zip(time_intervals, time_colors):
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
            line=dict(color=color, width=1.5, dash="dash"),
            hovertemplate="Price: $%{x:.2f}<br>P&L: $%{y:.2f}<extra></extra>"
        ))

    fig.add_hline(y=0, line_dash="dot", line_color="rgba(136, 146, 164, 0.3)", line_width=1)
    fig.add_vline(x=spot_price, line_dash="dot", line_color="rgba(255, 255, 255, 0.2)", line_width=1,
                  annotation_text=f"Current: ${spot_price:.2f}",
                  annotation_position="top",
                  annotation_font=dict(color="#8892a4", size=11, family="DM Sans"))

    for leg in legs:
        if leg["type"] != "stock":
            fig.add_vline(x=leg["strike"], line_dash="dot", line_color="rgba(255,255,255,0.08)",
                          annotation_text=f"${leg['strike']}", annotation_position="bottom",
                          annotation_font=dict(color="#5a6478", size=10, family="JetBrains Mono"))

    breakevens = []
    for i in range(len(S_range) - 1):
        if total_pnl_expiry[i] * total_pnl_expiry[i + 1] < 0:
            x_be = S_range[i] - total_pnl_expiry[i] * (S_range[i + 1] - S_range[i]) / (total_pnl_expiry[i + 1] - total_pnl_expiry[i])
            breakevens.append(x_be)

    for be in breakevens:
        fig.add_vline(x=be, line_dash="dashdot", line_color=AMBER, opacity=0.6, line_width=1,
                      annotation_text=f"BE: ${be:.2f}", annotation_position="top right",
                      annotation_font=dict(color=AMBER, size=11, family="JetBrains Mono"))

    fig.update_layout(
        title=dict(text=title, font=dict(size=15, color="#e8edf5", family="DM Sans")),
        xaxis_title="Stock Price ($)",
        yaxis_title="Profit / Loss ($)",
        template="plotly_dark",
        plot_bgcolor=CHART_BG,
        paper_bgcolor=CHART_BG,
        font=CHART_FONT,
        hovermode="x unified",
        legend=dict(
            yanchor="top", y=0.99,
            xanchor="left", x=0.01,
            bgcolor="rgba(6, 11, 24, 0.8)",
            bordercolor="rgba(99, 179, 237, 0.1)",
            borderwidth=1,
            font=dict(color="#8892a4", size=11, family="DM Sans")
        ),
        margin=dict(l=50, r=15, t=50, b=45),
        height=420,
        autosize=True,
        xaxis=dict(
            gridcolor=CHART_GRID,
            zerolinecolor="rgba(99, 179, 237, 0.1)",
            tickfont=dict(family="JetBrains Mono", size=10),
        ),
        yaxis=dict(
            gridcolor=CHART_GRID,
            zerolinecolor="rgba(99, 179, 237, 0.1)",
            tickfont=dict(family="JetBrains Mono", size=10),
            tickprefix="$",
        ),
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
        "delta": BLUE,
        "gamma": RED,
        "theta": AMBER,
        "vega": "#8b5cf6",
        "rho": "#06b6d4",
    }

    line_color = color_map.get(greek_name, BLUE)
    r_val = int(line_color.lstrip('#')[0:2], 16)
    g_val = int(line_color.lstrip('#')[2:4], 16)
    b_val = int(line_color.lstrip('#')[4:6], 16)
    fill_color = f"rgba({r_val}, {g_val}, {b_val}, 0.1)"

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=S_range, y=total_greek,
        name=greek_name.capitalize(),
        line=dict(color=line_color, width=2),
        fill="tozeroy",
        fillcolor=fill_color,
        hovertemplate="Price: $%{x:.2f}<br>" + greek_name.capitalize() + ": %{y:.4f}<extra></extra>"
    ))

    fig.add_vline(x=spot_price, line_dash="dot", line_color="rgba(255,255,255,0.15)", line_width=1)
    fig.add_hline(y=0, line_dash="dot", line_color="rgba(136, 146, 164, 0.2)", line_width=1)

    fig.update_layout(
        title=dict(text=f"{greek_name.capitalize()} vs Stock Price", font=dict(size=14, color="#e8edf5", family="DM Sans")),
        xaxis_title="Stock Price ($)",
        yaxis_title=greek_name.capitalize(),
        template="plotly_dark",
        plot_bgcolor=CHART_BG,
        paper_bgcolor=CHART_BG,
        font=CHART_FONT,
        height=320,
        margin=dict(l=50, r=15, t=45, b=45),
        autosize=True,
        xaxis=dict(
            gridcolor=CHART_GRID,
            zerolinecolor="rgba(99, 179, 237, 0.1)",
            tickfont=dict(family="JetBrains Mono", size=10),
        ),
        yaxis=dict(
            gridcolor=CHART_GRID,
            zerolinecolor="rgba(99, 179, 237, 0.1)",
            tickfont=dict(family="JetBrains Mono", size=10),
        ),
    )

    return fig
