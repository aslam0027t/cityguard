"""
Tests for Database Schema, Transactions, and Integrity Constraints
"""

import os
import tempfile
from pathlib import Path
import pytest

import database as db
import config


@pytest.fixture
def temp_db():
    """Create an isolated temporary SQLite database for testing."""
    fd, path_str = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    path = Path(path_str)
    db.init_db(path)
    yield path
    if path.exists():
        try:
            os.remove(path)
        except Exception:
            pass


def test_schema_initialization(temp_db):
    """Verify that tables and indexes are created properly."""
    with db.get_db_connection(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row["name"] for row in cursor.fetchall()}
        assert "reports" in tables
        assert "status_events" in tables
        assert "duplicate_relationships" in tables


def test_persistence_after_reconnecting(temp_db):
    """Verify data persists when connections close and open anew."""
    report_data = {
        "description": "Deep pothole causing accidents near Central Gate.",
        "citizen_category": "Road damage",
        "predicted_category": "Road damage",
        "category_evidence": ["pothole", "accident"],
        "extractive_summary": "Deep pothole causing accidents near Central Gate.",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "area": "Oakridge Heights",
        "priority_score": 60,
        "priority_label": "High",
        "priority_reasons": [{"factor": "Immediate Hazard", "points": 60}],
    }
    report_id = db.insert_report(report_data, db_path=temp_db)
    assert report_id > 0

    # Read back with a brand new independent connection
    with db.get_db_connection(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reports WHERE id = ?;", (report_id,))
        row = cursor.fetchone()
        assert row is not None
        assert row["citizen_category"] == "Road damage"
        assert row["priority_score"] == 60
        assert row["workflow_status"] == "Submitted"


def test_tracking_token_lookup(temp_db):
    """Verify token generation and retrieval."""
    report_data = {
        "description": "Streetlight flickering continuously.",
        "citizen_category": "Streetlights / electrical",
        "predicted_category": "Streetlights / electrical",
        "latitude": 12.9820,
        "longitude": 77.6050,
        "area": "Maple Riverside",
    }
    report_id = db.insert_report(report_data, db_path=temp_db)
    rep = db.get_report_by_id(report_id, db_path=temp_db)
    token = rep["tracking_token"]

    assert token.startswith("CIVIC-")
    found = db.get_report_by_token(token, db_path=temp_db)
    assert found is not None
    assert found["id"] == report_id

    # Nonexistent token
    assert db.get_report_by_token("CIVIC-NONEXISTENT", db_path=temp_db) is None


def test_workflow_transitions(temp_db):
    """Verify workflow rules: department requirement and public note on resolve."""
    report_data = {
        "description": "Water pipe leak flooding basement.",
        "citizen_category": "Water supply",
        "predicted_category": "Water supply",
        "latitude": 12.9650,
        "longitude": 77.6120,
        "area": "Harbor Ward",
    }
    report_id = db.insert_report(report_data, db_path=temp_db)

    # 1. Attempt transition to 'Assigned' without department -> must fail
    success, msg = db.update_report_workflow(report_id, "Assigned", department=None, db_path=temp_db)
    assert not success
    assert "Department assignment is mandatory" in msg

    # 2. Transition to 'Assigned' with valid department -> must succeed
    success, msg = db.update_report_workflow(report_id, "Assigned", department="Water services", db_path=temp_db)
    assert success
    rep = db.get_report_by_id(report_id, db_path=temp_db)
    assert rep["workflow_status"] == "Assigned"
    assert rep["assigned_department"] == "Water services"

    # 3. Transition to 'In progress' -> must succeed
    success, msg = db.update_report_workflow(report_id, "In progress", db_path=temp_db)
    assert success

    # 4. Attempt transition to 'Resolved' without note -> must fail
    success, msg = db.update_report_workflow(report_id, "Resolved", note="", db_path=temp_db)
    assert not success
    assert "public resolution note is required" in msg

    # 5. Transition to 'Resolved' with note -> must succeed
    success, msg = db.update_report_workflow(
        report_id, "Resolved", note="Pipe valve replaced and tested.", is_public=True, db_path=temp_db
    )
    assert success
    rep = db.get_report_by_id(report_id, db_path=temp_db)
    assert rep["workflow_status"] == "Resolved"


def test_public_vs_internal_notes(temp_db):
    """Verify that public timeline strictly excludes internal officer notes."""
    report_data = {
        "description": "Garbage dump near marketplace.",
        "citizen_category": "Waste",
        "predicted_category": "Waste",
        "latitude": 12.9780,
        "longitude": 77.5850,
        "area": "Pineview Central",
    }
    report_id = db.insert_report(report_data, db_path=temp_db)

    # Add public event
    db.add_status_event(report_id, "note_added", note="Public notice: sanitation crew dispatched.", is_public=True, db_path=temp_db)
    # Add internal event
    db.add_status_event(report_id, "note_added", note="Internal note: vehicle #4 delayed due to fuel stop.", is_public=False, db_path=temp_db)

    public_events = db.get_report_events(report_id, public_only=True, db_path=temp_db)
    all_events = db.get_report_events(report_id, public_only=False, db_path=temp_db)

    assert len(all_events) == 3  # created + 2 notes
    assert len(public_events) == 2  # created + public note
    assert not any("vehicle #4 delayed" in e["note"] for e in public_events)


def test_priority_override(temp_db):
    """Verify priority override stores new score while preserving audit trail."""
    report_data = {
        "description": "Tree branch fallen on footpath.",
        "citizen_category": "Other",
        "predicted_category": "Other",
        "latitude": 12.9550,
        "longitude": 77.5750,
        "area": "Elmwood Industrial",
        "priority_score": 10,
        "priority_label": "Low",
    }
    report_id = db.insert_report(report_data, db_path=temp_db)

    # Empty reason must fail
    success, msg = db.override_priority(report_id, 80, "High", reason="", db_path=temp_db)
    assert not success

    # Valid override
    success, msg = db.override_priority(report_id, 80, "High", reason="Branch is leaning on powerline.", db_path=temp_db)
    assert success

    rep = db.get_report_by_id(report_id, db_path=temp_db)
    assert rep["priority_score"] == 10  # original score preserved
    assert rep["priority_override_score"] == 80
    assert rep["priority_override_label"] == "High"
    assert "powerline" in rep["priority_override_reason"]


def test_duplicate_link_no_self_link(temp_db):
    """Verify database prevents linking a report to itself."""
    report_data = {
        "description": "Test report",
        "citizen_category": "Other",
        "predicted_category": "Other",
        "latitude": 12.0,
        "longitude": 77.0,
        "area": "Oakridge Heights",
    }
    rep_id = db.insert_report(report_data, db_path=temp_db)
    success = db.record_duplicate_candidate(rep_id, rep_id, 0.95, 10.0, db_path=temp_db)
    assert not success
