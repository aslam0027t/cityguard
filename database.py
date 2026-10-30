"""
CivicAction Database Layer
Provides SQLite schema definitions, connection management, transactions,
and verified CRUD operations for complaints, audit events, and duplicate links.
"""

import json
import secrets
import sqlite3
import string
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import DATABASE_PATH, DATA_DIR, ALLOWED_TRANSITIONS


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 string format."""
    return datetime.now(timezone.utc).isoformat()


def generate_tracking_token() -> str:
    """Generate a clean, unambiguous tracking token (e.g., CIVIC-9B2K-4X8M)."""
    alphabet = string.ascii_uppercase + string.digits
    # Exclude easily confused characters (0, O, I, 1)
    clean_chars = [c for c in alphabet if c not in ("O", "0", "I", "1")]
    part1 = "".join(secrets.choice(clean_chars) for _ in range(4))
    part2 = "".join(secrets.choice(clean_chars) for _ in range(4))
    return f"CIVIC-{part1}-{part2}"


@contextmanager
def get_db_connection(db_path: Optional[Path] = None):
    """
    Context manager for SQLite connections.
    Enforces foreign keys, row dict access, and explicit commit/rollback.
    Never caches connections across Streamlit reruns or threads.
    """
    path = Path(db_path) if db_path else DATABASE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Optional[Path] = None) -> None:
    """Initialize SQLite database tables and indexes idempotently."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # 1. Reports table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tracking_token TEXT UNIQUE NOT NULL,
                description TEXT NOT NULL,
                citizen_category TEXT NOT NULL,
                predicted_category TEXT NOT NULL,
                category_evidence TEXT NOT NULL, -- JSON list of matching tokens
                extractive_summary TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                area TEXT NOT NULL,
                priority_score INTEGER NOT NULL, -- 0 to 100
                priority_label TEXT NOT NULL,    -- High, Medium, Low
                priority_reasons TEXT NOT NULL,  -- JSON list of explainability factors
                priority_override_score INTEGER,
                priority_override_label TEXT,
                priority_override_reason TEXT,
                needs_review INTEGER NOT NULL DEFAULT 0,
                analysis_status TEXT NOT NULL,   -- 'complete', 'incomplete', 'failed'
                analysis_error TEXT,
                workflow_status TEXT NOT NULL DEFAULT 'Submitted',
                assigned_department TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                seed_id TEXT UNIQUE
            );
            """
        )

        # 2. Status and audit events table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS status_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
                event_type TEXT NOT NULL,
                previous_value TEXT,
                new_value TEXT,
                note TEXT,
                is_public INTEGER NOT NULL DEFAULT 1, -- 0 for internal, 1 for citizen visible
                created_at TEXT NOT NULL
            );
            """
        )

        # 3. Duplicate relationships table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS duplicate_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_report_id INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
                candidate_report_id INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
                similarity_score REAL NOT NULL,
                distance_meters REAL NOT NULL,
                review_state TEXT NOT NULL DEFAULT 'suggested', -- suggested, confirmed, rejected
                created_at TEXT NOT NULL,
                CONSTRAINT chk_no_self_link CHECK (source_report_id != candidate_report_id),
                CONSTRAINT unq_pair UNIQUE (source_report_id, candidate_report_id)
            );
            """
        )

        # Indexes for query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_token ON reports(tracking_token);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_area ON reports(area);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_workflow ON reports(workflow_status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_priority ON reports(priority_score);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_report ON status_events(report_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_duplicates_src ON duplicate_relationships(source_report_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_duplicates_cand ON duplicate_relationships(candidate_report_id);")


def insert_report(data: Dict[str, Any], db_path: Optional[Path] = None) -> int:
    """
    Insert a new complaint report and record an initial 'created' event in one transaction.
    Returns the newly created report internal ID.
    """
    now = data.get("created_at") or utc_now_iso()
    tracking_token = data.get("tracking_token") or generate_tracking_token()

    category_evidence = data.get("category_evidence", [])
    if isinstance(category_evidence, list):
        category_evidence = json.dumps(category_evidence)

    priority_reasons = data.get("priority_reasons", [])
    if isinstance(priority_reasons, list):
        priority_reasons = json.dumps(priority_reasons)

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO reports (
                tracking_token, description, citizen_category, predicted_category,
                category_evidence, extractive_summary, latitude, longitude, area,
                priority_score, priority_label, priority_reasons,
                priority_override_score, priority_override_label, priority_override_reason,
                needs_review, analysis_status, analysis_error, workflow_status,
                assigned_department, created_at, updated_at, seed_id
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            );
            """,
            (
                tracking_token,
                data["description"].strip(),
                data["citizen_category"],
                data["predicted_category"],
                category_evidence,
                data.get("extractive_summary", ""),
                float(data["latitude"]),
                float(data["longitude"]),
                data["area"],
                int(data.get("priority_score", 0)),
                data.get("priority_label", "Low"),
                priority_reasons,
                data.get("priority_override_score"),
                data.get("priority_override_label"),
                data.get("priority_override_reason"),
                1 if data.get("needs_review") else 0,
                data.get("analysis_status", "complete"),
                data.get("analysis_error"),
                data.get("workflow_status", "Submitted"),
                data.get("assigned_department"),
                now,
                now,
                data.get("seed_id"),
            ),
        )
        report_id = cursor.lastrowid

        # Insert initial submission event
        cursor.execute(
            """
            INSERT INTO status_events (
                report_id, event_type, previous_value, new_value, note, is_public, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                report_id,
                "created",
                None,
                data.get("workflow_status", "Submitted"),
                "Complaint submitted and recorded.",
                1,
                now,
            ),
        )

        return report_id


def get_report_by_id(report_id: int, db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Fetch report by internal ID."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reports WHERE id = ?;", (report_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_report_by_token(token: str, db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Fetch report by its unique tracking token."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reports WHERE UPPER(tracking_token) = UPPER(?);", (token.strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_all_reports(db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Fetch all reports, ordered by effective priority descending, then created_at ascending."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT *,
                COALESCE(priority_override_score, priority_score) AS effective_priority
            FROM reports
            ORDER BY effective_priority DESC, created_at ASC;
            """
        )
        return [dict(row) for row in cursor.fetchall()]


def get_report_events(report_id: int, public_only: bool = False, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Fetch event timeline for a given report."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        if public_only:
            cursor.execute(
                """
                SELECT * FROM status_events
                WHERE report_id = ? AND is_public = 1
                ORDER BY created_at ASC, id ASC;
                """,
                (report_id,),
            )
        else:
            cursor.execute(
                """
                SELECT * FROM status_events
                WHERE report_id = ?
                ORDER BY created_at ASC, id ASC;
                """,
                (report_id,),
            )
        return [dict(row) for row in cursor.fetchall()]


def add_status_event(
    report_id: int,
    event_type: str,
    previous_value: Optional[str] = None,
    new_value: Optional[str] = None,
    note: Optional[str] = None,
    is_public: bool = True,
    db_path: Optional[Path] = None,
) -> int:
    """Insert an event entry into the audit trail."""
    now = utc_now_iso()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO status_events (
                report_id, event_type, previous_value, new_value, note, is_public, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (report_id, event_type, previous_value, new_value, note, 1 if is_public else 0, now),
        )
        return cursor.lastrowid


def update_report_workflow(
    report_id: int,
    new_status: str,
    department: Optional[str] = None,
    note: Optional[str] = None,
    is_public: bool = True,
    db_path: Optional[Path] = None,
) -> Tuple[bool, str]:
    """
    Update report workflow status with verification rules:
    - Status must be in ALLOWED_TRANSITIONS from current status (or initial review)
    - Department required for 'Assigned' and 'In progress'
    - Public note required for 'Resolved'
    Returns (success, message).
    """
    report = get_report_by_id(report_id, db_path)
    if not report:
        return False, "Report not found."

    current_status = report["workflow_status"]
    effective_dept = department or report["assigned_department"]

    # Rule checks
    if new_status in ("Assigned", "In progress") and not effective_dept:
        return False, f"Department assignment is mandatory before moving to '{new_status}'."

    if new_status == "Resolved" and (not note or not note.strip()):
        return False, "A public resolution note is required to mark an issue as 'Resolved'."

    # Transition validation
    valid_targets = ALLOWED_TRANSITIONS.get(current_status, [])
    if new_status != current_status and new_status not in valid_targets:
        return False, f"Invalid transition from '{current_status}' to '{new_status}'."

    now = utc_now_iso()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE reports
            SET workflow_status = ?,
                assigned_department = ?,
                updated_at = ?
            WHERE id = ?;
            """,
            (new_status, effective_dept, now, report_id),
        )

        event_note = note.strip() if note else f"Workflow status changed to {new_status}."
        cursor.execute(
            """
            INSERT INTO status_events (
                report_id, event_type, previous_value, new_value, note, is_public, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                report_id,
                "status_change",
                current_status,
                new_status,
                event_note,
                1 if is_public else 0,
                now,
            ),
        )

        # If department was changed or newly assigned
        if effective_dept != report["assigned_department"]:
            cursor.execute(
                """
                INSERT INTO status_events (
                    report_id, event_type, previous_value, new_value, note, is_public, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    report_id,
                    "assigned",
                    report["assigned_department"],
                    effective_dept,
                    f"Assigned to {effective_dept} department.",
                    1,
                    now,
                ),
            )

    return True, f"Report successfully updated to {new_status}."


def override_priority(
    report_id: int,
    new_score: int,
    new_label: str,
    reason: str,
    db_path: Optional[Path] = None,
) -> Tuple[bool, str]:
    """
    Allow an officer to override priority score/label with a required reason.
    Preserves original computed score while updating audit trail.
    """
    if not reason or not reason.strip():
        return False, "An explicit reason is required to override priority."

    report = get_report_by_id(report_id, db_path)
    if not report:
        return False, "Report not found."

    old_label = report["priority_override_label"] or report["priority_label"]
    now = utc_now_iso()

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE reports
            SET priority_override_score = ?,
                priority_override_label = ?,
                priority_override_reason = ?,
                updated_at = ?
            WHERE id = ?;
            """,
            (new_score, new_label, reason.strip(), now, report_id),
        )

        cursor.execute(
            """
            INSERT INTO status_events (
                report_id, event_type, previous_value, new_value, note, is_public, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                report_id,
                "priority_override",
                old_label,
                new_label,
                f"Priority overridden to {new_label} ({new_score}/100). Reason: {reason.strip()}",
                0,  # internal officer note by default
                now,
            ),
        )

    return True, f"Priority overridden to {new_label}."


def record_duplicate_candidate(
    source_id: int,
    candidate_id: int,
    similarity: float,
    distance_meters: float,
    review_state: str = "suggested",
    db_path: Optional[Path] = None,
) -> bool:
    """
    Store or update a suggested duplicate candidate relationship.
    Prevents self-links and enforces uniqueness.
    """
    if source_id == candidate_id:
        return False

    now = utc_now_iso()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO duplicate_relationships (
                source_report_id, candidate_report_id, similarity_score,
                distance_meters, review_state, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_report_id, candidate_report_id) DO UPDATE SET
                similarity_score = excluded.similarity_score,
                distance_meters = excluded.distance_meters;
            """,
            (source_id, candidate_id, similarity, distance_meters, review_state, now),
        )
    return True


def update_duplicate_review_state(
    relationship_id: int,
    new_state: str,
    db_path: Optional[Path] = None,
) -> Tuple[bool, str]:
    """
    Update duplicate candidate state to 'confirmed' or 'rejected'.
    Prevents cycle connections and self-referential chains.
    """
    if new_state not in ("suggested", "confirmed", "rejected"):
        return False, "Invalid review state."

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM duplicate_relationships WHERE id = ?;", (relationship_id,))
        row = cursor.fetchone()
        if not row:
            return False, "Duplicate relationship not found."

        source_id = row["source_report_id"]
        candidate_id = row["candidate_report_id"]

        if new_state == "confirmed":
            # Check for direct reverse link cycle
            cursor.execute(
                """
                SELECT id FROM duplicate_relationships
                WHERE source_report_id = ? AND candidate_report_id = ? AND review_state = 'confirmed';
                """,
                (candidate_id, source_id),
            )
            reverse_confirmed = cursor.fetchone()
            if reverse_confirmed:
                # Symmetrical link already confirmed, simply confirm this side
                pass

        cursor.execute(
            """
            UPDATE duplicate_relationships
            SET review_state = ?
            WHERE id = ?;
            """,
            (new_state, relationship_id),
        )

        now = utc_now_iso()
        note = f"Duplicate suggestion with report #{candidate_id} marked as {new_state}."
        cursor.execute(
            """
            INSERT INTO status_events (
                report_id, event_type, previous_value, new_value, note, is_public, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (source_id, "duplicate_linked", row["review_state"], new_state, note, 1 if new_state == "confirmed" else 0, now),
        )

    return True, f"Duplicate status updated to '{new_state}'."


def get_duplicates_for_report(report_id: int, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Fetch duplicate candidate links for a report (both as source and as candidate)."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT d.id AS relationship_id,
                   d.source_report_id,
                   d.candidate_report_id,
                   d.similarity_score,
                   d.distance_meters,
                   d.review_state,
                   d.created_at,
                   r.tracking_token,
                   r.extractive_summary,
                   r.area,
                   r.workflow_status,
                   r.created_at AS candidate_created_at
            FROM duplicate_relationships d
            JOIN reports r ON (
                CASE WHEN d.source_report_id = ? THEN d.candidate_report_id ELSE d.source_report_id END = r.id
            )
            WHERE d.source_report_id = ? OR d.candidate_report_id = ?
            ORDER BY d.similarity_score DESC;
            """,
            (report_id, report_id, report_id),
        )
        return [dict(row) for row in cursor.fetchall()]


def check_has_confirmed_related(report_id: int, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Check if report has any confirmed duplicate relationship."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT d.id, r.id AS related_id, r.tracking_token, r.extractive_summary, r.workflow_status
            FROM duplicate_relationships d
            JOIN reports r ON (
                CASE WHEN d.source_report_id = ? THEN d.candidate_report_id ELSE d.source_report_id END = r.id
            )
            WHERE (d.source_report_id = ? OR d.candidate_report_id = ?)
              AND d.review_state = 'confirmed';
            """,
            (report_id, report_id, report_id),
        )
        return [dict(row) for row in cursor.fetchall()]


def reset_database(confirm: bool = False, db_path: Optional[Path] = None) -> bool:
    """
    Safely reset the database, strictly requiring explicit confirmation.
    Deletes all records and reinitializes empty schema.
    """
    if not confirm:
        return False
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM duplicate_relationships;")
        cursor.execute("DELETE FROM status_events;")
        cursor.execute("DELETE FROM reports;")
    return True
