"""
CivicAction Supabase Integration Module
Handles authentication, connection testing, and data synchronization between
local SQLite storage and a cloud Supabase PostgreSQL database.
"""

from typing import Any, Dict, List, Optional, Tuple
import json

import os
import config
import database as local_db

SUPABASE_KEY = getattr(config, "SUPABASE_KEY", os.getenv("SUPABASE_KEY", ""))
SUPABASE_URL = getattr(config, "SUPABASE_URL", os.getenv("SUPABASE_URL", ""))
DB_BACKEND = getattr(config, "DB_BACKEND", os.getenv("DB_BACKEND", "sqlite"))

try:
    from supabase import Client, create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = Any  # type: ignore


def is_supabase_configured() -> bool:
    """Check if valid Supabase credentials have been configured."""
    return bool(
        SUPABASE_AVAILABLE
        and SUPABASE_URL
        and SUPABASE_KEY
        and not SUPABASE_URL.startswith("https://your-project")
        and not SUPABASE_KEY.startswith("your-")
    )


def get_supabase_client() -> Optional[Client]:
    """Initialize and return the Supabase client, or None if not configured."""
    if not is_supabase_configured():
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Error initializing Supabase client: {e}")
        return None


def test_supabase_connection() -> Tuple[bool, str]:
    """
    Test connectivity to Supabase by checking the 'reports' table.
    Returns (success: bool, message: str).
    """
    if not SUPABASE_AVAILABLE:
        return False, "The 'supabase' Python package is not installed."

    if not is_supabase_configured():
        return False, (
            "Supabase credentials are not configured or still have placeholder values. "
            "Please update SUPABASE_URL and SUPABASE_KEY in your .env file."
        )

    client = get_supabase_client()
    if not client:
        return False, "Could not initialize Supabase client."

    try:
        # Perform a lightweight query to test connectivity
        response = client.table("reports").select("id").limit(1).execute()
        return True, "Successfully connected to Supabase 'reports' table."
    except Exception as e:
        err_msg = str(e)
        if "relation \"public.reports\" does not exist" in err_msg or "PGRST204" in err_msg or "PGRST200" in err_msg:
            return False, (
                "Connected to Supabase, but the 'reports' table does not exist yet. "
                "Please run the SQL script in 'supabase_schema.sql' inside your Supabase SQL Editor."
            )
        return False, f"Supabase connection error: {err_msg}"


def sync_sqlite_to_supabase() -> Tuple[bool, str, int]:
    """
    Upload all local SQLite reports, status events, and duplicate relationships
    into the Supabase database.
    Returns (success, message, records_synced).
    """
    client = get_supabase_client()
    if not client:
        return False, "Supabase client is not configured.", 0

    reports = local_db.get_all_reports()
    if not reports:
        return True, "No local SQLite reports to synchronize.", 0

    synced_reports = 0
    try:
        for r in reports:
            # Prepare report payload
            payload = {
                "tracking_token": r["tracking_token"],
                "seed_id": r.get("seed_id"),
                "description": r["description"],
                "citizen_category": r.get("citizen_category"),
                "predicted_category": r.get("predicted_category"),
                "category_evidence": r.get("category_evidence"),
                "extractive_summary": r.get("extractive_summary"),
                "latitude": float(r["latitude"]),
                "longitude": float(r["longitude"]),
                "area": r["area"],
                "priority_score": int(r["priority_score"]),
                "priority_label": r["priority_label"],
                "priority_reasons": r.get("priority_reasons"),
                "priority_override_score": r.get("priority_override_score"),
                "priority_override_label": r.get("priority_override_label"),
                "priority_override_reason": r.get("priority_override_reason"),
                "needs_review": 1 if r.get("needs_review") else 0,
                "analysis_status": r.get("analysis_status", "complete"),
                "analysis_error": r.get("analysis_error"),
                "workflow_status": r.get("workflow_status", "Submitted"),
                "assigned_department": r.get("assigned_department"),
                "created_at": r["created_at"],
                "updated_at": r.get("updated_at", r["created_at"]),
            }

            # Upsert by tracking_token
            res = client.table("reports").upsert(payload, on_conflict="tracking_token").execute()
            if res.data:
                synced_reports += 1

        return True, f"Successfully synchronized {synced_reports} reports to Supabase.", synced_reports
    except Exception as e:
        return False, f"Sync error: {str(e)}", synced_reports


if __name__ == "__main__":
    print(f"Supabase configured: {is_supabase_configured()}")
    success, msg = test_supabase_connection()
    print(f"Connection test: {msg}")
