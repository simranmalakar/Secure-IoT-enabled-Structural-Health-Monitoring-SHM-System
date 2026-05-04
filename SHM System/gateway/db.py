"""
SQLite Database Layer — Secure IoT SHM Gateway
=================================================
Manages all database operations for sensor readings,
anomaly alerts, and security log events.
"""

import sqlite3
import os
from datetime import datetime, timezone

# Database path (project root)
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "shm.db"
)


def get_connection():
    """Get a thread-local SQLite connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # Better concurrent read performance
    return conn


def init_database():
    """Initialize the database schema (idempotent)."""
    conn = get_connection()
    cursor = conn.cursor()

    # --- Sensor Readings ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id   TEXT NOT NULL,
            timestamp   TEXT NOT NULL,
            vibration   REAL NOT NULL,
            tilt        REAL NOT NULL,
            strain      REAL NOT NULL,
            hash        TEXT NOT NULL,
            anomaly_score REAL DEFAULT 0,
            anomaly_class TEXT DEFAULT 'NORMAL',
            prediction  REAL DEFAULT 0,
            explanation TEXT DEFAULT '',
            received_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # --- Anomaly Alerts ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id   TEXT NOT NULL,
            alert_type  TEXT NOT NULL,
            severity    TEXT NOT NULL CHECK(severity IN ('LOW','MEDIUM','HIGH','CRITICAL')),
            message     TEXT NOT NULL,
            value       REAL,
            threshold   REAL,
            features    TEXT DEFAULT '{}',
            timestamp   TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # --- Security Logs ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS security_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type  TEXT NOT NULL,
            source      TEXT,
            details     TEXT,
            severity    TEXT NOT NULL CHECK(severity IN ('LOW','MEDIUM','HIGH','CRITICAL')),
            timestamp   TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # --- Indexes for performance ---
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_readings_sensor ON sensor_readings(sensor_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_readings_time ON sensor_readings(received_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_sensor ON alerts(sensor_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_time ON alerts(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_security_time ON security_logs(timestamp)")

    conn.commit()
    conn.close()
    print("[OK] Database initialized at:", DB_PATH)


def insert_reading(sensor_id: str, timestamp: str, vibration: float,
                   tilt: float, strain: float, hash_value: str,
                   anomaly_score: float = 0.0, anomaly_class: str = 'NORMAL',
                   prediction: float = 0.0, explanation: str = ''):
    """Insert a validated sensor reading with anomaly metrics."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO sensor_readings (sensor_id, timestamp, vibration, tilt, strain, hash, anomaly_score, anomaly_class, prediction, explanation)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (sensor_id, timestamp, vibration, tilt, strain, hash_value, anomaly_score, anomaly_class, prediction, explanation),
    )
    conn.commit()
    conn.close()


def insert_alert(sensor_id: str, alert_type: str, severity: str,
                 message: str, value: float = None, threshold: float = None,
                 features: str = "{}"):
    """Insert an anomaly alert with explainability features."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO alerts (sensor_id, alert_type, severity, message, value, threshold, features)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (sensor_id, alert_type, severity, message, value, threshold, features),
    )
    conn.commit()
    conn.close()


def insert_security_log(event_type: str, source: str, details: str, severity: str):
    """Insert a security event log."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO security_logs (event_type, source, details, severity)
           VALUES (?, ?, ?, ?)""",
        (event_type, source, details, severity),
    )
    conn.commit()
    conn.close()


def get_recent_readings(limit: int = 100):
    """Fetch the most recent sensor readings."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM sensor_readings ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_alerts(limit: int = 50):
    """Fetch the most recent alerts."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_security_logs(limit: int = 50):
    """Fetch the most recent security logs."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM security_logs ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def clear_all_data():
    """Clear all tables to reset the system (used on Start System)."""
    conn = get_connection()
    conn.execute("DELETE FROM sensor_readings")
    conn.execute("DELETE FROM alerts")
    conn.execute("DELETE FROM security_logs")
    # Reset autoincrement
    conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('sensor_readings', 'alerts', 'security_logs')")
    conn.commit()
    conn.close()
    print("[OK] Database cleared for new session.")


def get_stats():
    """Get aggregate statistics for the health endpoint."""
    conn = get_connection()
    stats = {
        "total_readings": conn.execute("SELECT COUNT(*) FROM sensor_readings").fetchone()[0],
        "total_alerts": conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0],
        "total_security_events": conn.execute("SELECT COUNT(*) FROM security_logs").fetchone()[0],
        "critical_alerts": conn.execute(
            "SELECT COUNT(*) FROM alerts WHERE severity = 'CRITICAL'"
        ).fetchone()[0],
        "active_sensors": conn.execute(
            "SELECT COUNT(DISTINCT sensor_id) FROM sensor_readings"
        ).fetchone()[0],
    }
    conn.close()
    return stats


# Auto-initialize on import
init_database()

