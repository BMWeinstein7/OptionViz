import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime


TOP_TICKERS = [
    "SPY", "QQQ", "AAPL", "TSLA", "NVDA", "AMZN", "META", "MSFT", "AMD", "GOOGL",
    "IWM", "NFLX", "SOFI", "BAC", "PLTR", "XLF", "INTC", "DIS", "NIO", "F",
    "EEM", "GLD", "SLV", "XLE", "COIN", "MARA", "RIOT", "BABA", "PYPL", "UBER",
    "JPM", "WFC", "C", "GS", "V", "MA", "CRM", "ORCL", "AVGO", "MU",
    "SMCI", "ARM", "MSTR", "SNOW", "SQ", "SHOP", "ROKU", "SNAP", "PINS", "RBLX",
    "GME", "AMC", "RIVN", "LCID", "PLUG", "CHPT", "DKNG", "PENN", "WYNN", "LVS",
    "XOM", "CVX", "OXY", "DVN", "HAL", "USO", "KO", "PEP", "MCD", "SBUX",
    "WMT", "TGT", "COST", "HD", "LOW", "LMT", "BA", "RTX", "GE", "CAT",
    "JNJ", "PFE", "MRNA", "ABBV", "UNH", "LLY", "BMY", "MRK", "GILD", "BIIB",
    "TLT", "HYG", "EWZ", "FXI", "KWEB", "VIX", "SOXL", "TQQQ", "SQQQ", "ARKK",
]


@st.cache_data(ttl=60)
def get_stock_quote(ticker):
    try:
        tk = yf.Ticker(ticker)
        info = tk.fast_info
        hist = tk.history(period="2d")

        if hist.empty:
            return None

        current_price = float(info.last_price) if hasattr(info, 'last_price') else float(hist['Close'].iloc[-1])

        prev_close = float(info.previous_close) if hasattr(info, 'previous_close') else (
            float(hist['Close'].iloc[-2]) if len(hist) >= 2 else current_price
        )

        change = current_price - prev_close
        change_pct = (change / prev_close * 100) if prev_close != 0 else 0

        market_cap = None
        if hasattr(info, 'market_cap'):
            market_cap = info.market_cap

        return {
            "ticker": ticker,
            "price": round(current_price, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "prev_close": round(prev_close, 2),
            "market_cap": market_cap,
            "day_high": float(hist['High'].iloc[-1]) if not hist.empty else None,
            "day_low": float(hist['Low'].iloc[-1]) if not hist.empty else None,
            "volume": int(hist['Volume'].iloc[-1]) if not hist.empty else None,
        }
    except Exception:
        return None


@st.cache_data(ttl=60)
def get_options_expirations(ticker):
    try:
        tk = yf.Ticker(ticker)
        return list(tk.options)
    except Exception:
        return []


@st.cache_data(ttl=30)
def get_options_chain(ticker, expiration):
    try:
        tk = yf.Ticker(ticker)
        chain = tk.option_chain(expiration)

        calls = chain.calls.copy()
        puts = chain.puts.copy()

        for df in [calls, puts]:
            df['bid'] = df['bid'].round(2)
            df['ask'] = df['ask'].round(2)
            df['lastPrice'] = df['lastPrice'].round(2)
            df['impliedVolatility'] = (df['impliedVolatility'] * 100).round(1)
            if 'change' in df.columns:
                df['change'] = df['change'].round(2)
            if 'percentChange' in df.columns:
                df['percentChange'] = df['percentChange'].round(2)

        return calls, puts
    except Exception:
        return pd.DataFrame(), pd.DataFrame()


@st.cache_data(ttl=120)
def get_options_flow(ticker):
    try:
        tk = yf.Ticker(ticker)
        expirations = list(tk.options)

        if not expirations:
            return pd.DataFrame()

        flow_data = []
        exps_to_check = expirations[:4]

        for exp in exps_to_check:
            try:
                chain = tk.option_chain(exp)

                for opt_type, opt_df in [("CALL", chain.calls), ("PUT", chain.puts)]:
                    for _, row in opt_df.iterrows():
                        vol = row.get('volume', 0) or 0
                        oi = row.get('openInterest', 0) or 0
                        if vol > 0 and oi > 0:
                            flow_data.append({
                                "Ticker": ticker,
                                "Exp": exp,
                                "Strike": row.get('strike', 0),
                                "Type": opt_type,
                                "Bid": round(row.get('bid', 0) or 0, 2),
                                "Ask": round(row.get('ask', 0) or 0, 2),
                                "Last": round(row.get('lastPrice', 0) or 0, 2),
                                "Volume": int(vol),
                                "OI": int(oi),
                                "Vol/OI": round(vol / oi, 2) if oi > 0 else 0,
                                "IV": round((row.get('impliedVolatility', 0) or 0) * 100, 1),
                                "ITM": row.get('inTheMoney', False),
                            })
            except Exception:
                continue

        if not flow_data:
            return pd.DataFrame()

        df = pd.DataFrame(flow_data)
        df = df.sort_values("Volume", ascending=False)
        return df

    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=120)
def get_put_call_ratio(ticker):
    try:
        tk = yf.Ticker(ticker)
        expirations = list(tk.options)
        if not expirations:
            return None

        total_call_vol = 0
        total_put_vol = 0
        total_call_oi = 0
        total_put_oi = 0

        for exp in expirations[:3]:
            try:
                chain = tk.option_chain(exp)
                total_call_vol += chain.calls['volume'].sum()
                total_put_vol += chain.puts['volume'].sum()
                total_call_oi += chain.calls['openInterest'].sum()
                total_put_oi += chain.puts['openInterest'].sum()
            except Exception:
                continue

        vol_ratio = total_put_vol / total_call_vol if total_call_vol > 0 else 0
        oi_ratio = total_put_oi / total_call_oi if total_call_oi > 0 else 0

        return {
            "vol_ratio": round(vol_ratio, 3),
            "oi_ratio": round(oi_ratio, 3),
            "total_call_vol": int(total_call_vol),
            "total_put_vol": int(total_put_vol),
            "total_call_oi": int(total_call_oi),
            "total_put_oi": int(total_put_oi),
        }
    except Exception:
        return None


def format_number(num):
    if num is None:
        return "N/A"
    if abs(num) >= 1e12:
        return f"${num/1e12:.2f}T"
    elif abs(num) >= 1e9:
        return f"${num/1e9:.2f}B"
    elif abs(num) >= 1e6:
        return f"${num/1e6:.2f}M"
    elif abs(num) >= 1e3:
        return f"{num/1e3:.1f}K"
    return str(num)
