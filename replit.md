# OptionViz - Options Strategy Visualizer

## Overview
An options strategy builder and visualizer similar to OptionStrat. Built with Streamlit, using Black-Scholes pricing model for options valuation and yfinance for live market data. Includes user authentication, strategy saving, and trade performance tracking.

## Features
- **Strategy Templates**: 12 pre-built strategies (Long Call, Bull Call Spread, Iron Condor, Calendar Spread, etc.)
- **Custom Builder**: Build custom multi-leg strategies with up to 8 legs
- **P&L Charts**: Interactive Plotly charts showing P&L at expiry and intermediate dates
- **Greeks**: Full Greeks calculation (Delta, Gamma, Theta, Vega, Rho)
- **Greeks Charts**: Visual Greek sensitivity across stock prices
- **Break-even Analysis**: Automatic break-even point detection
- **Risk Metrics**: Max profit, max loss, net cost, risk/reward ratio
- **Live Market Data**: Real-time stock quotes for top 100 most actively traded tickers
- **Options Chain**: Full options chain with calls/puts, OI charts, IV smile
- **Options Flow**: Volume scanner, put/call ratios, unusual activity detection
- **Live Ticker Integration**: Strategy builder can pull live stock price and expiration dates
- **User Authentication**: Email/password signup with email verification
- **Save Strategies**: Verified users can save and load strategy configurations
- **Trade Tracking**: Open/close trades on saved strategies, track P&L and performance metrics

## Architecture
```
main.py                  # Streamlit entry point with auth gate and multi-page navigation
app/
  __init__.py
  auth.py                # Authentication (signup, login, verification, email sending)
  database.py            # PostgreSQL database operations (users, strategies, trades)
  pricing.py             # Black-Scholes pricing & Greeks calculations
  strategies.py          # Strategy templates and leg generation
  charts.py              # Plotly chart generation (P&L, Greeks)
  page_config.py         # Page setup and CSS styling
  data.py                # Live market data fetching (yfinance)
  pages/
    __init__.py
    auth_page.py         # Login/signup/verification UI
    my_strategies.py     # Saved strategies list and save form
    my_trades.py         # Trade tracking, open/close trades, performance summary
.streamlit/
  config.toml            # Streamlit server config (CORS, host binding)
```

## Database (PostgreSQL)
- **users**: id, email, password_hash, is_verified, created_at
- **saved_strategies**: id, user_id, name, strategy_type, legs (JSONB), spot_price, risk_free_rate, implied_vol, days_to_expiry, ticker, notes, created_at
- **trade_tracking**: id, strategy_id, user_id, ticker, entry/exit dates, entry/current/exit prices, entry_cost, current_value, realized_pnl, status, notes

## Pages
1. **Strategy Builder** - Build and visualize options strategies with P&L charts (+ save strategy)
2. **Market Data** - Live quotes for top 100 tickers with search/filter
3. **Options Chain** - Full chain viewer with OI charts and IV smile
4. **Options Flow** - Volume scanner with unusual activity detection
5. **My Strategies** - View/load/delete saved strategies, open trades
6. **My Trades** - Open/closed trades, performance summary with cumulative P&L chart

## Authentication
- Email/password signup and login (no email verification required)
- Users get full access immediately upon signup
- Passwords hashed with bcrypt
- Guest mode: users can bypass login to browse all features (Strategy Builder, Market Data, Options Chain, Options Flow) without saving capabilities
- Guest users see "Sign in to save strategies and track trades" instead of save/trade forms
- My Strategies and My Trades pages are hidden from guest navigation and guarded against direct access

## UI / Responsive Design
- Mobile-first responsive CSS with media queries at 768px and 480px breakpoints
- Sidebar starts collapsed by default for mobile-friendly initial experience
- Sidebar expands to 85vw on tablets, 100vw on phones for full-screen navigation
- Columns stack into 2-per-row at 768px, single-column at 480px via flex-wrap
- Tabs are horizontally scrollable on small screens (no wrapping overflow)
- Touch-friendly tap targets: all buttons and inputs have min-height of 44px
- Trade stat rows use responsive flex layout that wraps gracefully on mobile
- Charts use autosize with compact margins for better mobile rendering
- Login screen centered using Streamlit columns with gradient title
- Sidebar auto-collapses on navigation item selection via JS injection (components.html)
- Font sizes use clamp() for fluid scaling across screen sizes
- Viewport meta tag set for proper mobile rendering (no user zoom)

## Tech Stack
- **Framework**: Streamlit
- **Database**: PostgreSQL (psycopg2-binary)
- **Auth**: bcrypt for password hashing
- **Pricing Model**: Black-Scholes (scipy for normal distribution)
- **Market Data**: yfinance (no API key required)
- **Charts**: Plotly
- **Math**: NumPy 1.26.4, SciPy
- **Python**: 3.10

## Running
```
streamlit run main.py --server.headless true --server.port 5000
```
