# OptionViz

  **Options Strategy Builder & Visualizer**

  OptionViz is a web application for building, analyzing, and visualizing options trading strategies. It uses Black-Scholes pricing to model option values and Greeks, pulls live market data via yfinance, and renders interactive P&L diagrams with Plotly. Designed for traders and students who want to understand how multi-leg options strategies behave across different price scenarios.

  ## Features

  ### Strategy Builder
  - **12 Pre-Built Templates** — Long Call, Long Put, Bull Call Spread, Bear Put Spread, Straddle, Strangle, Iron Condor, Iron Butterfly, Butterfly Spread, Calendar Spread, Covered Call, and Protective Put
  - **Custom Multi-Leg Builder** — Build strategies with up to 8 legs, each with configurable action (buy/sell), type (call/put), quantity, strike price, and premium
  - **Strategy Legs Summary** — HTML table showing each leg's details with color-coded BUY/SELL tags

  ### Analysis & Visualization
  - **P&L Charts** — Interactive Plotly charts with green profit zone and red loss zone gradient fills, at-expiry curve and intermediate DTE curves
  - **Greeks Calculation** — Full Greeks suite: Delta, Gamma, Theta, Vega, Rho computed via Black-Scholes
  - **Greeks Charts** — Visual sensitivity charts showing how each Greek changes across stock prices
  - **Break-Even Analysis** — Automatic detection and display of break-even points
  - **Risk Metrics** — Max profit, max loss, net cost/credit, and risk/reward ratio

  ### Market Data
  - **Live Stock Quotes** — Real-time quotes for the top 100 most actively traded tickers with search and filtering
  - **Options Chain Viewer** — Full options chain with calls and puts, open interest charts, and implied volatility smile
  - **Options Flow Scanner** — Volume scanner with put/call ratios and unusual activity detection
  - **Live Ticker Integration** — Strategy builder pulls the current stock price and available expiration dates for any ticker

  ### User Features
  - **Authentication** — Email/password signup and login with bcrypt password hashing
  - **Guest Mode** — Browse all features (Strategy Builder, Market Data, Options Chain, Options Flow) without an account; saving and trade tracking require login
  - **Save Strategies** — Save strategy configurations with all parameters for later review or modification
  - **Trade Tracking** — Open trades on saved strategies, track current value vs. entry cost, close trades with realized P&L, and view performance summaries with cumulative P&L charts

  ## Tech Stack

  | Component | Technology |
  |-----------|-----------|
  | Framework | Streamlit |
  | Database | PostgreSQL with connection pooling (psycopg2) |
  | Pricing Model | Black-Scholes (SciPy) |
  | Market Data | yfinance |
  | Charts | Plotly |
  | Auth | bcrypt |
  | Python | 3.10 |

  ## Design

  - **Typography**: DM Sans for UI, JetBrains Mono for numerical data
  - **Theme**: Dark navy backgrounds with glassmorphism metric cards
  - **Color Palette**: Green (#22c55e) for profit/bullish, Red (#ef4444) for loss/bearish, Blue (#3b82f6) for neutral/accent
  - **Responsive**: Mobile-first CSS with breakpoints at 768px and 480px, touch-friendly 44px tap targets

  ## Project Structure

  ```
  main.py                    # Streamlit entry point, navigation, strategy builder page
  app/
    auth.py                  # Authentication logic (signup, login, password hashing)
    database.py              # PostgreSQL operations with ThreadedConnectionPool
    pricing.py               # Black-Scholes pricing and Greeks calculations
    strategies.py            # Strategy templates and leg generation
    charts.py                # Plotly chart builders (P&L, Greeks)
    page_config.py           # Page setup, CSS design system, meta tags
    data.py                  # Live market data via yfinance
    pages/
      auth_page.py           # Login/signup/guest UI
      my_strategies.py       # Saved strategies management
      my_trades.py           # Trade tracking and performance
  ```

  ## Running

  ```bash
  streamlit run main.py --server.headless true --server.port 5000
  ```

  Requires a `DATABASE_URL` environment variable pointing to a PostgreSQL instance. The app automatically creates the required tables and indexes on first run.
  