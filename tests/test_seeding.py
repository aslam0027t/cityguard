"""
Tests for Synthetic Data Seeding and Reset
Verifies idempotent seeding, category breakdown, and safe reset behavior.
"""

import os
import tempfile
from pathlib import Path
import pytest

import database as db
import seed_data


@pytest.fixture
def temp_db(monkeypatch):
    """Create isolated temporary database and monkeypatch config.DATABASE_PATH."""
    fd, path_str = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    path = Path(path_str)
    monkeypatch.setattr(seed_data, "init_db", lambda: db.init_db(path))
    monkeypatch.setattr(seed_data, "get_db_connection", lambda: db.get_db_connection(path))
    monkeypatch.setattr(seed_data, "get_all_reports", lambda: db.get_all_reports(path))
    monkeypatch.setattr(seed_data, "insert_report", lambda *args, **kwargs: db.insert_report(*args, **{**kwargs, "db_path": path}))
    monkeypatch.setattr(seed_data, "add_status_event", lambda *args, **kwargs: db.add_status_event(*args, **{**kwargs, "db_path": path}))
    monkeypatch.setattr(seed_data, "record_duplicate_candidate", lambda *args, **kwargs: db.record_duplicate_candidate(*args, **{**kwargs, "db_path": path}))

    db.init_db(path)
    yield path
    if path.exists():
        try:
            os.remove(path)
        except Exception:
            pass


def test_idempotent_seeding(temp_db):
    """Verify that running seed twice does not create duplicate records."""
    # First seed
    count1 = seed_data.seed_database(force_reseed=False)
    assert count1 == 40

    all_reports = db.get_all_reports(temp_db)
    assert len(all_reports) == 40

    # Second seed (idempotent run)
    count2 = seed_data.seed_database(force_reseed=False)
    assert count2 == 0

    # Still 40 reports
    all_reports_after = db.get_all_reports(temp_db)
    assert len(all_reports_after) == 40


def test_seed_category_breakdown(temp_db):
    """Verify that 40 reports match the required category distribution."""
    seed_data.seed_database(force_reseed=False)
    reports = db.get_all_reports(temp_db)

    cat_counts = {}
    for r in reports:
        cat = r["citizen_category"]
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    assert cat_counts.get("Road damage") == 8
    assert cat_counts.get("Waste") == 8
    assert cat_counts.get("Drainage / waterlogging") == 10
    assert cat_counts.get("Streetlights / electrical") == 8
    assert cat_counts.get("Water supply") == 5 or cat_counts.get("Water supply") == 6
    # Note: 1 ambiguous report has citizen_category="Other" in the raw complaints, total 40
    assert len(reports) == 40


def test_safe_reset_and_manual_preservation(temp_db):
    """Verify manual report addition and database reset."""
    seed_data.seed_database(force_reseed=False)

    # Insert a manual report
    manual_rep = {
        "description": "Manual user submission for test verification.",
        "citizen_category": "Waste",
        "predicted_category": "Waste",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "area": "Oakridge Heights",
    }
    m_id = db.insert_report(manual_rep, db_path=temp_db)
    assert len(db.get_all_reports(temp_db)) == 41

    # Reset without confirmation -> must fail
    res = db.reset_database(confirm=False, db_path=temp_db)
    assert not res
    assert len(db.get_all_reports(temp_db)) == 41

    # Confirmed reset
    res_confirmed = db.reset_database(confirm=True, db_path=temp_db)
    assert res_confirmed is True
    assert len(db.get_all_reports(temp_db)) == 0
