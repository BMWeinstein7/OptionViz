import streamlit as st


def setup_page():
    st.set_page_config(
        page_title="OptionViz - Options Strategy Visualizer",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    st.markdown("""
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        .stApp {
            background-color: #0e1117;
        }

        .block-container {
            max-width: 100%;
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .metric-card {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 0.8rem 1rem;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.1);
            text-align: center;
            margin-bottom: 0.5rem;
        }
        .metric-card h4 {
            color: #888;
            font-size: 0.75rem;
            margin: 0;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .metric-card p {
            font-size: clamp(1rem, 2.5vw, 1.4rem);
            font-weight: 700;
            margin: 0.3rem 0 0 0;
            word-break: break-word;
        }
        .profit { color: #00E676; }
        .loss { color: #FF5252; }
        .neutral { color: #B0BEC5; }
        .leg-card {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 8px;
            padding: 0.8rem;
            margin-bottom: 0.5rem;
        }
        .strategy-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: clamp(1.5rem, 4vw, 2rem);
            font-weight: 800;
        }
        .sentiment-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .bullish { background: rgba(0,230,118,0.2); color: #00E676; }
        .bearish { background: rgba(255,82,82,0.2); color: #FF5252; }
        .neutral-badge { background: rgba(176,190,197,0.2); color: #B0BEC5; }
        .volatile { background: rgba(255,215,0,0.2); color: #FFD700; }
        div[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0a0a1a 0%, #111133 100%);
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            flex-wrap: wrap;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 8px 16px;
            border-radius: 8px;
        }
        .user-badge {
            display: inline-block;
            background: rgba(102,126,234,0.2);
            color: #667eea;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            word-break: break-all;
        }
        .strategy-card {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 1.2rem;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 0.8rem;
        }
        .strategy-card h4 {
            margin: 0 0 0.5rem 0;
            color: #e0e0e0;
        }
        .strategy-card .meta {
            color: #888;
            font-size: 0.8rem;
        }
        .trade-open { border-left: 3px solid #00E676; }
        .trade-closed { border-left: 3px solid #888; }
        .trade-profit { border-left: 3px solid #00E676; }
        .trade-loss { border-left: 3px solid #FF5252; }

        .auth-title {
            text-align: center;
            font-size: clamp(1.6rem, 4vw, 2.2rem);
            font-weight: 800;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.25rem;
        }
        .auth-subtitle {
            text-align: center;
            color: #888;
            font-size: 0.85rem;
            margin-bottom: 1.5rem;
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
        }
        input, select, textarea,
        .stTextInput input,
        .stNumberInput input,
        .stSelectbox > div > div {
            min-height: 44px;
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
                font-size: 0.65rem;
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
                font-size: 0.85rem;
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
