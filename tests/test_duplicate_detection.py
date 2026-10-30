"""
Tests for Duplicate Candidate Detection
Verifies geographic distance filtering, time window filtering,
exclusion of resolved reports, exclusion of self, and mocked embedding threshold checks.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
import pytest
import ai_pipeline as ai


@pytest.fixture
def base_report():
    return {
        "id": 1,
        "description": "Massive deep pothole on Main Road causing traffic swerves.",
        "citizen_category": "Road damage",
        "predicted_category": "Road damage",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "area": "Oakridge Heights",
        "workflow_status": "Submitted",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def test_empty_candidate_set(base_report):
    """Verify empty list returned when no other reports exist."""
    candidates, warning = ai.find_duplicate_candidates(base_report, [])
    assert candidates == []
    assert warning is None


def test_exclusion_of_same_report(base_report):
    """Verify that a report is never evaluated as a candidate against itself."""
    # List containing only itself
    candidates, warning = ai.find_duplicate_candidates(base_report, [base_report])
    assert candidates == []


def test_distance_filtering(base_report):
    """Verify that complaints further than 150 meters are excluded before embedding calculation."""
    distant_report = {
        "id": 2,
        "description": "Massive deep pothole on Main Road causing traffic swerves.",
        "citizen_category": "Road damage",
        "predicted_category": "Road damage",
        # ~1 km away
        "latitude": 12.9800,
        "longitude": 77.6030,
        "area": "Oakridge Heights",
        "workflow_status": "Submitted",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    candidates, warning = ai.find_duplicate_candidates(base_report, [distant_report])
    assert candidates == []


def test_time_window_filtering(base_report):
    """Verify that complaints older than 7 days are excluded."""
    old_time = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    old_report = {
        "id": 3,
        "description": "Massive deep pothole on Main Road causing traffic swerves.",
        "citizen_category": "Road damage",
        "predicted_category": "Road damage",
        "latitude": 12.9717,  # ~15m away
        "longitude": 77.5947,
        "area": "Oakridge Heights",
        "workflow_status": "Submitted",
        "created_at": old_time,
    }
    candidates, warning = ai.find_duplicate_candidates(base_report, [old_report])
    assert candidates == []


def test_resolved_report_exclusion(base_report):
    """Verify that resolved complaints are excluded from active duplicate candidate suggestions."""
    resolved_report = {
        "id": 4,
        "description": "Massive deep pothole on Main Road causing traffic swerves.",
        "citizen_category": "Road damage",
        "predicted_category": "Road damage",
        "latitude": 12.9717,
        "longitude": 77.5947,
        "area": "Oakridge Heights",
        "workflow_status": "Resolved",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    candidates, warning = ai.find_duplicate_candidates(base_report, [resolved_report])
    assert candidates == []


def test_duplicate_candidate_with_mocked_embeddings(base_report):
    """
    Unit test using mocked embeddings to verify similarity thresholding logic.
    [MOCKED TEST: Mocking SentenceTransformer model output].
    """
    nearby_report = {
        "id": 5,
        "tracking_token": "CIVIC-MOCK-0001",
        "description": "Huge crater in road pavement right near Central Market.",
        "citizen_category": "Road damage",
        "predicted_category": "Road damage",
        "latitude": 12.9718,  # ~30m away
        "longitude": 77.5948,
        "area": "Oakridge Heights",
        "workflow_status": "Submitted",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    # Mock model: returns nearly identical vector for both sentences
    mock_model = MagicMock()
    # High similarity mock vector (e.g. cosine sim ~ 0.95)
    import numpy as np
    mock_model.encode.side_effect = [
        np.array([1.0, 0.0, 0.0]),  # new_report embedding
        np.array([[0.95, 0.31, 0.0]]),  # candidate embedding
    ]

    candidates, warning = ai.find_duplicate_candidates(
        new_report=base_report,
        candidate_reports=[nearby_report],
        model=mock_model,
        similarity_thresh=0.80,
    )

    assert len(candidates) == 1
    assert candidates[0]["candidate_id"] == 5
    assert candidates[0]["similarity_score"] >= 0.80
    assert candidates[0]["distance_meters"] <= 150.0
