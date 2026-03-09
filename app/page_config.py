import streamlit as st


def setup_page():
    st.set_page_config(
        page_title="OptionViz - Options Strategy Visualizer",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    import streamlit.components.v1 as components
    components.html("""
    <script>
    (function() {
        var head = window.parent.document.head;
        var metas = [
            {name: "viewport", content: "width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"},
            {name: "description", content: "OptionViz - Options Strategy Builder & Visualizer. Build, analyze, and visualize options strategies with real-time market data, Black-Scholes pricing, and interactive P&L charts."},
            {name: "theme-color", content: "#060b18"},
            {name: "robots", content: "index, follow"}
        ];
        var ogMetas = [
            {property: "og:title", content: "OptionViz - Options Strategy Visualizer"},
            {property: "og:description", content: "Build and visualize options strategies with live market data, P&L diagrams, Greeks analysis, and trade tracking."},
            {property: "og:type", content: "website"}
        ];
        metas.forEach(function(m) {
            if (!head.querySelector('meta[name="' + m.name + '"]')) {
                var el = document.createElement('meta');
                el.name = m.name;
                el.content = m.content;
                head.appendChild(el);
            }
        });
        ogMetas.forEach(function(m) {
            if (!head.querySelector('meta[property="' + m.property + '"]')) {
                var el = document.createElement('meta');
                el.setAttribute('property', m.property);
                el.content = m.content;
                head.appendChild(el);
            }
        });
        if (!head.querySelector('link[href*="fonts.googleapis.com/css2"]')) {
            var pc1 = document.createElement('link');
            pc1.rel = 'preconnect';
            pc1.href = 'https://fonts.googleapis.com';
            head.appendChild(pc1);
            var pc2 = document.createElement('link');
            pc2.rel = 'preconnect';
            pc2.href = 'https://fonts.gstatic.com';
            pc2.crossOrigin = '';
            head.appendChild(pc2);
            var fonts = document.createElement('link');
            fonts.rel = 'stylesheet';
            fonts.href = 'https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=JetBrains+Mono:wght@400;500;600;700&display=swap';
            head.appendChild(fonts);
        }
    })();
    </script>
    """, height=0)

    st.markdown("""
    <style>
        :root {
            --bg-primary: #060b18;
            --bg-secondary: #0c1425;
            --bg-card: #111b2e;
            --bg-card-hover: #152038;
            --border-subtle: rgba(99, 179, 237, 0.08);
            --border-hover: rgba(99, 179, 237, 0.18);
            --text-primary: #e8edf5;
            --text-secondary: #8892a4;
            --text-muted: #5a6478;
            --accent-green: #22c55e;
            --accent-green-dim: rgba(34, 197, 94, 0.15);
            --accent-red: #ef4444;
            --accent-red-dim: rgba(239, 68, 68, 0.15);
            --accent-blue: #3b82f6;
            --accent-blue-dim: rgba(59, 130, 246, 0.12);
            --accent-amber: #f59e0b;
            --accent-purple: #8b5cf6;
            --font-ui: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            --font-mono: 'JetBrains Mono', 'SF Mono', 'Fira Code', monospace;
            --radius-sm: 6px;
            --radius-md: 10px;
            --radius-lg: 14px;
            --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
            --transition-normal: 250ms cubic-bezier(0.4, 0, 0.2, 1);
        }

        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                animation-duration: 0.01ms !important;
                transition-duration: 0.01ms !important;
            }
        }

        .stApp {
            background-color: var(--bg-primary);
            font-family: var(--font-ui);
        }

        .block-container {
            max-width: 100%;
            padding-left: 1rem;
            padding-right: 1rem;
        }

        h1, h2, h3, h4, h5, h6, p, span, div, label, .stMarkdown {
            font-family: var(--font-ui) !important;
        }

        .metric-card {
            background: linear-gradient(135deg, var(--bg-card) 0%, rgba(17, 27, 46, 0.8) 100%);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            padding: 0.9rem 1.1rem;
            border-radius: var(--radius-md);
            border: 1px solid var(--border-subtle);
            text-align: center;
            margin-bottom: 0.5rem;
            transition: border-color var(--transition-normal), box-shadow var(--transition-normal);
        }
        .metric-card:hover {
            border-color: var(--border-hover);
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
        }
        .metric-card h4 {
            color: var(--text-muted);
            font-size: 0.7rem;
            font-weight: 500;
            margin: 0;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            font-family: var(--font-ui) !important;
        }
        .metric-card p {
            font-size: clamp(1rem, 2.5vw, 1.35rem);
            font-weight: 600;
            margin: 0.35rem 0 0 0;
            word-break: break-word;
            font-family: var(--font-mono) !important;
            letter-spacing: -0.02em;
        }

        .profit { color: var(--accent-green); }
        .loss { color: var(--accent-red); }
        .neutral { color: var(--text-secondary); }

        .leg-card {
            background: rgba(255,255,255,0.02);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-sm);
            padding: 0.8rem;
            margin-bottom: 0.5rem;
            transition: border-color var(--transition-fast);
        }
        .leg-card:hover {
            border-color: var(--border-hover);
        }

        .strategy-header {
            background: linear-gradient(135deg, var(--accent-blue) 0%, var(--accent-purple) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: clamp(1.5rem, 4vw, 2.2rem);
            font-weight: 700;
            letter-spacing: -0.03em;
            font-family: var(--font-ui) !important;
        }

        .sentiment-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.78rem;
            font-weight: 600;
            letter-spacing: 0.02em;
        }
        .bullish { background: var(--accent-green-dim); color: var(--accent-green); }
        .bearish { background: var(--accent-red-dim); color: var(--accent-red); }
        .neutral-badge { background: rgba(136, 146, 164, 0.15); color: var(--text-secondary); }
        .volatile { background: rgba(245, 158, 11, 0.15); color: var(--accent-amber); }

        div[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #070d1a 0%, #0c1425 50%, #0a1020 100%);
            border-right: 1px solid var(--border-subtle);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
            flex-wrap: wrap;
            background: var(--bg-secondary);
            border-radius: var(--radius-md);
            padding: 4px;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 8px 16px;
            border-radius: var(--radius-sm);
            font-family: var(--font-ui) !important;
            font-weight: 500;
            font-size: 0.85rem;
            transition: background var(--transition-fast), color var(--transition-fast);
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background: var(--accent-blue-dim);
        }

        .user-badge {
            display: inline-block;
            background: var(--accent-blue-dim);
            color: var(--accent-blue);
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            word-break: break-all;
            font-family: var(--font-mono) !important;
        }

        .strategy-card {
            background: linear-gradient(135deg, var(--bg-card) 0%, rgba(17, 27, 46, 0.7) 100%);
            backdrop-filter: blur(8px);
            padding: 1.2rem;
            border-radius: var(--radius-md);
            border: 1px solid var(--border-subtle);
            margin-bottom: 0.8rem;
            transition: border-color var(--transition-normal), transform var(--transition-normal);
        }
        .strategy-card:hover {
            border-color: var(--border-hover);
        }
        .strategy-card h4 {
            margin: 0 0 0.5rem 0;
            color: var(--text-primary);
            font-family: var(--font-ui) !important;
        }
        .strategy-card .meta {
            color: var(--text-muted);
            font-size: 0.8rem;
        }

        .trade-open { border-left: 3px solid var(--accent-green); }
        .trade-closed { border-left: 3px solid var(--text-muted); }
        .trade-profit { border-left: 3px solid var(--accent-green); }
        .trade-loss { border-left: 3px solid var(--accent-red); }

        .auth-title {
            text-align: center;
            font-size: clamp(1.8rem, 4vw, 2.6rem);
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-blue) 0%, var(--accent-purple) 60%, #c084fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.25rem;
            letter-spacing: -0.03em;
            font-family: var(--font-ui) !important;
        }
        .auth-subtitle {
            text-align: center;
            color: var(--text-muted);
            font-size: 0.88rem;
            margin-bottom: 1.5rem;
            font-weight: 400;
            letter-spacing: 0.01em;
        }

        .trade-stats-row {
            display: flex;
            gap: 2rem;
            flex-wrap: wrap;
            margin-top: 0.6rem;
        }
        .trade-stats-row > div {
            min-width: 0;
        }

        button, .stButton > button,
        [data-testid="stBaseButton-secondaryFormSubmit"],
        [data-testid="stBaseButton-secondary"],
        .stFormSubmitButton > button {
            min-height: 44px !important;
            font-family: var(--font-ui) !important;
            font-weight: 500;
            border-radius: var(--radius-sm) !important;
            transition: all var(--transition-fast) !important;
        }
        .stButton > button:hover,
        .stFormSubmitButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }

        button:focus-visible, a:focus-visible, input:focus-visible, select:focus-visible {
            outline: 2px solid var(--accent-blue) !important;
            outline-offset: 2px !important;
        }

        input, select, textarea,
        .stTextInput input,
        .stNumberInput input,
        .stSelectbox > div > div {
            min-height: 44px;
            font-family: var(--font-ui) !important;
        }

        .section-divider {
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--border-subtle) 20%, var(--border-subtle) 80%, transparent);
            margin: 1.5rem 0;
            border: none;
        }

        .summary-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            border-radius: var(--radius-md);
            overflow: hidden;
            font-family: var(--font-mono) !important;
            font-size: 0.82rem;
        }
        .summary-table th {
            background: var(--bg-secondary);
            color: var(--text-muted);
            font-weight: 500;
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            padding: 0.6rem 0.8rem;
            text-align: left;
            border-bottom: 1px solid var(--border-subtle);
        }
        .summary-table td {
            padding: 0.55rem 0.8rem;
            border-bottom: 1px solid rgba(99, 179, 237, 0.04);
            color: var(--text-primary);
        }
        .summary-table tr:last-child td {
            border-bottom: none;
        }
        .summary-table tr:hover td {
            background: rgba(59, 130, 246, 0.04);
        }
        .tag-buy {
            background: var(--accent-green-dim);
            color: var(--accent-green);
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 0.72rem;
        }
        .tag-sell {
            background: var(--accent-red-dim);
            color: var(--accent-red);
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 0.72rem;
        }

        .stDataFrame {
            border-radius: var(--radius-md) !important;
            overflow: hidden;
        }

        hr {
            border-color: var(--border-subtle) !important;
        }

        @media (max-width: 768px) {
            .block-container {
                padding-left: 0.5rem;
                padding-right: 0.5rem;
                padding-top: 1rem;
            }
            .metric-card {
                padding: 0.6rem 0.8rem;
            }
            .metric-card h4 {
                font-size: 0.6rem;
                letter-spacing: 0.5px;
            }
            .metric-card p {
                font-size: 1rem;
            }
            .strategy-card {
                padding: 0.8rem;
            }
            .strategy-card h4 {
                font-size: 0.95rem;
            }
            div[data-testid="stSidebar"] {
                min-width: 85vw !important;
                max-width: 85vw !important;
                z-index: 999;
            }
            div[data-testid="stHorizontalBlock"] {
                flex-wrap: wrap;
                gap: 0.25rem !important;
            }
            div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
                min-width: calc(50% - 0.25rem) !important;
                flex: 1 1 calc(50% - 0.25rem) !important;
            }
            .stTabs [data-baseweb="tab-list"] {
                gap: 4px;
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
                scrollbar-width: none;
                padding-bottom: 4px;
            }
            .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar {
                display: none;
            }
            .stTabs [data-baseweb="tab"] {
                padding: 8px 12px;
                font-size: 0.82rem;
                white-space: nowrap;
                flex-shrink: 0;
            }
            .trade-stats-row {
                gap: 0.8rem;
            }
            .trade-stats-row > div {
                flex: 1 1 40%;
                min-width: 40%;
            }
            .stDataFrame {
                overflow-x: auto !important;
                -webkit-overflow-scrolling: touch;
            }
            .strategy-header {
                font-size: 1.5rem;
            }
            .stPlotlyChart {
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
            }
            .summary-table {
                font-size: 0.75rem;
            }
            .summary-table th, .summary-table td {
                padding: 0.4rem 0.5rem;
            }
        }

        @media (max-width: 480px) {
            .block-container {
                padding-left: 0.3rem;
                padding-right: 0.3rem;
            }
            .metric-card p {
                font-size: 0.9rem;
            }
            div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
                min-width: 100% !important;
                flex: 1 1 100% !important;
            }
            .trade-stats-row > div {
                flex: 1 1 100%;
                min-width: 100%;
            }
            .stTabs [data-baseweb="tab"] {
                padding: 6px 10px;
                font-size: 0.8rem;
            }
            div[data-testid="stSidebar"] {
                min-width: 100vw !important;
                max-width: 100vw !important;
            }
        }

    </style>
    """, unsafe_allow_html=True)
