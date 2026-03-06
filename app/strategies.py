STRATEGY_TEMPLATES = {
    "Long Call": {
        "description": "Bullish bet with limited downside. Profits when the stock rises above the strike price.",
        "sentiment": "Bullish",
        "legs": [
            {"type": "call", "action": "buy", "strike_offset": 0, "qty": 1}
        ],
    },
    "Long Put": {
        "description": "Bearish bet with limited downside. Profits when the stock falls below the strike price.",
        "sentiment": "Bearish",
        "legs": [
            {"type": "put", "action": "buy", "strike_offset": 0, "qty": 1}
        ],
    },
    "Covered Call": {
        "description": "Own shares and sell a call for income. Caps upside but generates premium.",
        "sentiment": "Neutral/Mildly Bullish",
        "legs": [
            {"type": "stock", "action": "buy", "qty": 100},
            {"type": "call", "action": "sell", "strike_offset": 5, "qty": 1}
        ],
    },
    "Bull Call Spread": {
        "description": "Buy a lower strike call, sell a higher strike call. Limited risk and reward.",
        "sentiment": "Bullish",
        "legs": [
            {"type": "call", "action": "buy", "strike_offset": -5, "qty": 1},
            {"type": "call", "action": "sell", "strike_offset": 5, "qty": 1}
        ],
    },
    "Bear Put Spread": {
        "description": "Buy a higher strike put, sell a lower strike put. Limited risk and reward.",
        "sentiment": "Bearish",
        "legs": [
            {"type": "put", "action": "buy", "strike_offset": 5, "qty": 1},
            {"type": "put", "action": "sell", "strike_offset": -5, "qty": 1}
        ],
    },
    "Long Straddle": {
        "description": "Buy both a call and put at the same strike. Profits from large moves in either direction.",
        "sentiment": "Volatile",
        "legs": [
            {"type": "call", "action": "buy", "strike_offset": 0, "qty": 1},
            {"type": "put", "action": "buy", "strike_offset": 0, "qty": 1}
        ],
    },
    "Long Strangle": {
        "description": "Buy an OTM call and OTM put. Cheaper than a straddle, needs a bigger move.",
        "sentiment": "Volatile",
        "legs": [
            {"type": "call", "action": "buy", "strike_offset": 5, "qty": 1},
            {"type": "put", "action": "buy", "strike_offset": -5, "qty": 1}
        ],
    },
    "Iron Condor": {
        "description": "Sell an OTM call spread and OTM put spread. Profits from low volatility.",
        "sentiment": "Neutral",
        "legs": [
            {"type": "put", "action": "buy", "strike_offset": -10, "qty": 1},
            {"type": "put", "action": "sell", "strike_offset": -5, "qty": 1},
            {"type": "call", "action": "sell", "strike_offset": 5, "qty": 1},
            {"type": "call", "action": "buy", "strike_offset": 10, "qty": 1}
        ],
    },
    "Iron Butterfly": {
        "description": "Sell ATM call and put, buy OTM wings. Max profit if stock stays at the strike.",
        "sentiment": "Neutral",
        "legs": [
            {"type": "put", "action": "buy", "strike_offset": -10, "qty": 1},
            {"type": "put", "action": "sell", "strike_offset": 0, "qty": 1},
            {"type": "call", "action": "sell", "strike_offset": 0, "qty": 1},
            {"type": "call", "action": "buy", "strike_offset": 10, "qty": 1}
        ],
    },
    "Protective Put": {
        "description": "Own shares and buy a put for downside protection. Like insurance for your stock.",
        "sentiment": "Bullish (hedged)",
        "legs": [
            {"type": "stock", "action": "buy", "qty": 100},
            {"type": "put", "action": "buy", "strike_offset": -5, "qty": 1}
        ],
    },
    "Call Butterfly": {
        "description": "Buy 1 lower call, sell 2 ATM calls, buy 1 higher call. Profits if stock stays near center.",
        "sentiment": "Neutral",
        "legs": [
            {"type": "call", "action": "buy", "strike_offset": -10, "qty": 1},
            {"type": "call", "action": "sell", "strike_offset": 0, "qty": 2},
            {"type": "call", "action": "buy", "strike_offset": 10, "qty": 1}
        ],
    },
    "Calendar Spread": {
        "description": "Sell a near-term call, buy a longer-term call at the same strike. Profits from time decay.",
        "sentiment": "Neutral",
        "legs": [
            {"type": "call", "action": "sell", "strike_offset": 0, "qty": 1, "dte_multiplier": 0.5},
            {"type": "call", "action": "buy", "strike_offset": 0, "qty": 1, "dte_multiplier": 1.0}
        ],
    },
}


def get_strategy_legs(template_name, base_strike, base_premium=None):
    template = STRATEGY_TEMPLATES.get(template_name)
    if not template:
        return []

    legs = []
    for leg_def in template["legs"]:
        leg = {
            "type": leg_def["type"],
            "action": leg_def["action"],
            "qty": leg_def["qty"],
        }
        if leg_def["type"] == "stock":
            leg["strike"] = base_strike
        else:
            leg["strike"] = base_strike + leg_def.get("strike_offset", 0)
            leg["dte_multiplier"] = leg_def.get("dte_multiplier", 1.0)

        legs.append(leg)

    return legs
