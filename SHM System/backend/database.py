"""
Database Connection — FastAPI Backend
=======================================
Provides database access for the API layer,
reusing the gateway's SQLite database.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gateway.db import (
    get_connection,
    get_recent_readings,
    get_alerts,
    get_security_logs,
    get_stats,
    init_database,
    insert_security_log,
    clear_all_data,
)

# Re-export for use by routers
__all__ = [
    "get_connection",
    "get_recent_readings",
    "get_alerts",
    "get_security_logs",
    "get_stats",
    "init_database",
    "insert_security_log",
    "clear_all_data",
]

