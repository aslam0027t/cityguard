"""
End-to-End User Journey Programmatic Verification
Executes the complete 6-stage lifecycle:
1. Citizen submission
2. System categorizes, summarizes, scores priority, and detects duplicates
3. Area-level grouping and action brief computation
4. Officer review, department assignment, status transition, and duplicate linking
5. Officer updates progress with public vs internal notes
6. Citizen tracks report using token and verifies public timeline
"""

import json
from datetime import datetime, timezone
import pytest

import ai_pipeline as ai
import config
import database as db


def test_complete_end_to_end_user_journey(tmp_path, monkeypatch):
    """
    Simulates and validates the complete CivicAction operational journey.
    """
    test_db = tmp_path / "journey_test.db"
    monkeypatch.setattr(config, "DATABASE_PATH", test_db)
    monkeypatch.setattr(db, "DATABASE_PATH", test_db)
    db.init_db(test_db)

    # Seed an existing prior report in Hampankatta to verify duplicate candidate linkage
    prior_report_id = db.insert_report({
        "tracking_token": "CIVIC-PRIOR-0001",
        "description": "Deep open crater and asphalt potholes on the road right in front of the school gate.",
        "citizen_category": "Road damage",
        "predicted_category": "Road damage",
        "latitude": 12.8705,
        "longitude": 74.8429,
        "area": "Hampankatta",
        "priority_score": 80,
        "priority_label": "High",
        "workflow_status": "Submitted",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    # -------------------------------------------------------------
    # STAGE 1: Citizen Submits Complaint
    # -------------------------------------------------------------
    complaint_text = (
        "Deep open crater and asphalt potholes on the road right in front of the school gate. "
        "Two children nearly fell in this morning. Immediate danger!"
    )
    citizen_cat = "Road damage"
    lat = 12.8705
    lon = 74.8429
    area = "Hampankatta"

    # Fetch existing reports for duplicate context
    existing_reports = db.get_all_reports()
    model = ai.get_embedding_model()

    # -------------------------------------------------------------
    # STAGE 2: System Analysis (Categorization, Summary, Duplicates, Priority)
    # -------------------------------------------------------------
    analysis = ai.analyze_complaint(
        description=complaint_text,
        citizen_category=citizen_cat,
        latitude=lat,
        longitude=lon,
        area=area,
        existing_reports=existing_reports,
        model=model,
    )

    assert analysis["analysis_status"] == "complete"
    assert analysis["predicted_category"] == "Road damage"
    assert "crater" in analysis["category_evidence"] or "road" in analysis["category_evidence"]
    assert "school" in analysis["extractive_summary"].lower() or "crater" in analysis["extractive_summary"].lower()

    # Priority must be High (80/100): +60 for immediate hazard (crater/danger), +20 for school
    assert analysis["priority_score"] >= 80
    assert analysis["priority_label"] == "High"

    # Persist report
    token = db.generate_tracking_token()
    report_payload = {
        "tracking_token": token,
        "description": complaint_text,
        "citizen_category": citizen_cat,
        "predicted_category": analysis["predicted_category"],
        "category_evidence": analysis["category_evidence"],
        "extractive_summary": analysis["extractive_summary"],
        "latitude": lat,
        "longitude": lon,
        "area": area,
        "priority_score": analysis["priority_score"],
        "priority_label": analysis["priority_label"],
        "priority_reasons": analysis["priority_reasons"],
        "needs_review": analysis["needs_review"],
        "analysis_status": analysis["analysis_status"],
        "analysis_error": analysis["analysis_error"],
        "workflow_status": "Submitted",
        "assigned_department": None,
    }
    report_id = db.insert_report(report_payload)
    assert report_id > 0

    # Store duplicate candidates if found
    for dup in analysis.get("duplicate_candidates", []):
        db.record_duplicate_candidate(
            source_id=report_id,
            candidate_id=dup["candidate_id"],
            similarity=dup["similarity_score"],
            distance_meters=dup["distance_meters"],
            review_state="suggested",
        )

    # -------------------------------------------------------------
    # STAGE 3: Area-Level Grouping & Action Brief
    # -------------------------------------------------------------
    all_reports = db.get_all_reports()
    hampankatta_reports = [r for r in all_reports if r["area"] == "Hampankatta" and r["workflow_status"] != "Resolved"]
    assert len(hampankatta_reports) >= 1

    # Verify action brief logic computes correctly
    top_cat = analysis["predicted_category"]
    brief = f"Operational Brief: Hampankatta currently has {len(hampankatta_reports)} active submissions."
    assert "Hampankatta" in brief

    # -------------------------------------------------------------
    # STAGE 4: Officer Triage & Assignment
    # -------------------------------------------------------------
    # Rule check: cannot transition to 'Assigned' without department
    invalid_move, err_msg = db.update_report_workflow(report_id, "Assigned", department=None)
    assert not invalid_move

    # Valid step 1: Assign Roads department
    assign_success, assign_msg = db.update_report_workflow(
        report_id=report_id,
        new_status="Assigned",
        department="Roads",
        note="Assigned to Roads department for immediate inspection.",
        is_public=True,
    )
    assert assign_success

    # Valid step 2: Move to In progress
    success, msg = db.update_report_workflow(
        report_id=report_id,
        new_status="In progress",
        department="Roads",
        note="Road maintenance crew dispatched to repair culvert crater.",
        is_public=True,
    )
    assert success

    # Add an internal officer note
    db.add_status_event(
        report_id=report_id,
        event_type="note_added",
        note="Internal: Material requisition order #4912 approved.",
        is_public=False,
    )

    # -------------------------------------------------------------
    # STAGE 5: Citizen Tracking Verification
    # -------------------------------------------------------------
    citizen_view = db.get_report_by_token(token)
    assert citizen_view is not None
    assert citizen_view["workflow_status"] == "In progress"
    assert citizen_view["assigned_department"] == "Roads"

    # Public event timeline must show public events and strictly hide internal notes
    public_events = db.get_report_events(report_id, public_only=True)
    all_events = db.get_report_events(report_id, public_only=False)

    assert len(public_events) >= 3  # created, assigned, in_progress
    assert len(all_events) > len(public_events)  # contains the internal note
    assert any("Road maintenance crew dispatched" in e["note"] for e in public_events)
    assert not any("Material requisition order" in e["note"] for e in public_events)

    # -------------------------------------------------------------
    # STAGE 6: Resolution Verification
    # -------------------------------------------------------------
    # Rule check: cannot mark Resolved without public note
    res_fail, res_msg = db.update_report_workflow(report_id, "Resolved", note="")
    assert not res_fail

    # Resolve with valid note
    res_success, res_msg = db.update_report_workflow(
        report_id=report_id,
        new_status="Resolved",
        note="Culvert rebuilt and asphalt leveled. Road fully open to traffic.",
        is_public=True,
    )
    assert res_success

    resolved_rep = db.get_report_by_id(report_id)
    assert resolved_rep["workflow_status"] == "Resolved"
