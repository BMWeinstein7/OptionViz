import os
import json
import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from datetime import datetime

_pool = None


def _get_pool():
    global _pool
    if _pool is None or _pool.closed:
        _pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            dsn=os.environ["DATABASE_URL"],
        )
    return _pool


@contextmanager
def get_db():
    pool = _get_pool()
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def init_db():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_verified BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS saved_strategies (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR(255) NOT NULL,
                    strategy_type VARCHAR(100),
                    legs JSONB NOT NULL,
                    spot_price NUMERIC(12,4),
                    risk_free_rate NUMERIC(8,6),
                    implied_vol NUMERIC(8,6),
                    days_to_expiry INTEGER,
                    ticker VARCHAR(20),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS trade_tracking (
                    id SERIAL PRIMARY KEY,
                    strategy_id INTEGER REFERENCES saved_strategies(id) ON DELETE SET NULL,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    ticker VARCHAR(20),
                    entry_date TIMESTAMP DEFAULT NOW(),
                    exit_date TIMESTAMP,
                    entry_spot_price NUMERIC(12,4),
                    current_spot_price NUMERIC(12,4),
                    exit_spot_price NUMERIC(12,4),
                    entry_cost NUMERIC(14,2),
                    current_value NUMERIC(14,2),
                    realized_pnl NUMERIC(14,2),
                    status VARCHAR(20) DEFAULT 'open',
                    notes TEXT
                )
            """)

            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_saved_strategies_user_id ON saved_strategies (user_id)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_trade_tracking_user_id ON trade_tracking (user_id)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_trade_tracking_strategy_id ON trade_tracking (strategy_id)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_trade_tracking_status ON trade_tracking (status)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_trade_tracking_user_status ON trade_tracking (user_id, status)
            """)


def create_user(email, password_hash):
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO users (email, password_hash, is_verified)
                   VALUES (%s, %s, TRUE)
                   RETURNING id, email, is_verified, created_at""",
                (email, password_hash),
            )
            return dict(cur.fetchone())


def get_user_by_email(email):
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
            return dict(row) if row else None


def get_user_by_id(user_id):
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, email, is_verified, created_at FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None


def save_strategy(user_id, name, strategy_type, legs, spot_price, risk_free_rate, implied_vol, days_to_expiry, ticker=None, notes=None):
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO saved_strategies
                   (user_id, name, strategy_type, legs, spot_price, risk_free_rate, implied_vol, days_to_expiry, ticker, notes)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING *""",
                (user_id, name, strategy_type, json.dumps(legs), spot_price, risk_free_rate, implied_vol, days_to_expiry, ticker, notes),
            )
            return dict(cur.fetchone())


def get_user_strategies(user_id):
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM saved_strategies WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,),
            )
            return [dict(row) for row in cur.fetchall()]


def get_strategy_by_id(strategy_id, user_id):
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM saved_strategies WHERE id = %s AND user_id = %s",
                (strategy_id, user_id),
            )
            row = cur.fetchone()
            return dict(row) if row else None


def delete_strategy(strategy_id, user_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM saved_strategies WHERE id = %s AND user_id = %s",
                (strategy_id, user_id),
            )
            return cur.rowcount > 0


def create_trade(strategy_id, user_id, ticker, entry_spot_price, entry_cost, notes=None):
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO trade_tracking
                   (strategy_id, user_id, ticker, entry_spot_price, entry_cost, current_spot_price, current_value, status, notes)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, 'open', %s)
                   RETURNING *""",
                (strategy_id, user_id, ticker, entry_spot_price, entry_cost, entry_spot_price, entry_cost, notes),
            )
            return dict(cur.fetchone())


def get_user_trades(user_id, status=None):
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if status:
                cur.execute(
                    """SELECT t.*, s.name as strategy_name, s.strategy_type, s.legs
                       FROM trade_tracking t
                       JOIN saved_strategies s ON t.strategy_id = s.id
                       WHERE t.user_id = %s AND t.status = %s
                       ORDER BY t.entry_date DESC""",
                    (user_id, status),
                )
            else:
                cur.execute(
                    """SELECT t.*, s.name as strategy_name, s.strategy_type, s.legs
                       FROM trade_tracking t
                       JOIN saved_strategies s ON t.strategy_id = s.id
                       WHERE t.user_id = %s
                       ORDER BY t.entry_date DESC""",
                    (user_id,),
                )
            return [dict(row) for row in cur.fetchall()]


def close_trade(trade_id, user_id, exit_spot_price, realized_pnl):
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """UPDATE trade_tracking
                   SET status = 'closed', exit_date = NOW(), exit_spot_price = %s, realized_pnl = %s
                   WHERE id = %s AND user_id = %s
                   RETURNING *""",
                (exit_spot_price, realized_pnl, trade_id, user_id),
            )
            row = cur.fetchone()
            return dict(row) if row else None


def update_trade_current(trade_id, current_spot_price, current_value):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE trade_tracking SET current_spot_price = %s, current_value = %s WHERE id = %s",
                (current_spot_price, current_value, trade_id),
            )
