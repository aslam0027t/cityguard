"""
Tests for AI & Analysis Pipeline
Categorization, summary extraction, Haversine distance, and explainable priority scoring.
"""

import pytest
import ai_pipeline as ai


def test_text_normalization():
    """Verify whitespace and casing normalization."""
    assert ai.normalize_text("  Pothole   ON MAIN street!  \n") == "pothole on main street!"
    assert ai.normalize_text("") == ""


def test_category_evidence():
    """Verify rule-based keyword matching and evidence extraction."""
    # Road damage
    cat, ev, review = ai.categorize_text("Huge crater and broken asphalt road surface.")
    assert cat == "Road damage"
    assert "crater" in ev or "asphalt" in ev
    assert not review

    # Waste
    cat, ev, review = ai.categorize_text("Overflowing bin with rotting garbage and trash.")
    assert cat == "Waste"
    assert "garbage" in ev or "trash" in ev

    # Drainage
    cat, ev, review = ai.categorize_text("Severely clogged drain with stagnant water and flooding.")
    assert cat == "Drainage / waterlogging"
    assert "drain" in ev or "stagnant water" in ev

    # Electrical
    cat, ev, review = ai.categorize_text("Sparking wire on broken streetlight pole.")
    assert cat == "Streetlights / electrical"
    assert "streetlight" in ev or "wire" in ev

    # Water supply
    cat, ev, review = ai.categorize_text("Water main pipe burst causing no drinking water.")
    assert cat == "Water supply"
    assert "water" in ev or "pipe burst" in ev


def test_ambiguous_categorization():
    """Verify fallback to 'Other' with needs_review=True when text lacks clear keywords."""
    cat, ev, review = ai.categorize_text("The situation here is completely unacceptable and stressful.")
    assert cat == "Other"
    assert review is True


def test_extractive_summary():
    """Verify extractive summary selects problem sentence without hallucinating."""
    text = (
        "Good morning civic officers. "
        "A huge deep pothole on Elmwood Avenue is causing severe vehicle damage and traffic stalls. "
        "Please look into this soon as possible."
    )
    summary = ai.extract_summary(text, category="Road damage")
    assert "pothole" in summary.lower()
    assert summary in text  # pure extractive, no generative additions


def test_haversine_distance():
    """Verify Haversine formula calculation in metres."""
    # Same point -> 0 meters
    assert ai.haversine_distance(12.9716, 77.5946, 12.9716, 77.5946) == 0.0

    # Approx 111 km for 1 degree latitude difference
    dist = ai.haversine_distance(12.0, 77.0, 13.0, 77.0)
    assert 110000 < dist < 112000

    # Two points ~150 meters apart
    d_close = ai.haversine_distance(12.9716, 77.5946, 12.9725, 77.5952)
    assert 50 < d_close < 200


def test_priority_immediate_hazard():
    """Verify +60 priority for explicit physical hazards."""
    text = "Exposed live wire sparking on sidewalk outside shop."
    score, label, factors, needs_review = ai.calculate_priority(text)
    assert score >= 60
    assert label == "High"
    assert any("Immediate Physical Hazard" in f["factor"] for f in factors)


def test_priority_sensitive_setting():
    """Verify +20 priority for sensitive settings like schools/hospitals."""
    text = "Pothole on access path near primary school gate."
    score, label, factors, needs_review = ai.calculate_priority(text)
    assert score >= 20
    assert any("Sensitive Community Setting" in f["factor"] for f in factors)


def test_priority_blocked_access():
    """Verify +20 priority for blocked road / access cutoff."""
    text = "Road blocked completely by fallen debris, traffic completely halted."
    score, label, factors, needs_review = ai.calculate_priority(text)
    assert score >= 20
    assert any("Critical Access Disruption" in f["factor"] for f in factors)


def test_priority_negation_handling():
    """Verify conservative negation handling prevents false hazard scoring."""
    # Text mentions 'hazard' and 'live wire' but with negation
    text = "Old telephone cable drooped down, not a hazard and not a live wire, but looks messy."
    score, label, factors, needs_review = ai.calculate_priority(text)

    # Must NOT have received 60 points for hazard!
    assert score < 60
    assert label == "Low"
    assert needs_review is True  # flagged for human verification
    assert any("Negated Hazard" in f["factor"] for f in factors)


def test_analysis_failure_without_data_loss(monkeypatch):
    """Verify pipeline error handling preserves complaint and flags incomplete status."""
    # 1. Test empty/missing input
    result_empty = ai.analyze_complaint(
        description=None,
        citizen_category="Waste",
        latitude=12.0,
        longitude=77.0,
        area="Hampankatta",
    )
    assert result_empty["analysis_status"] == "incomplete"
    assert result_empty["needs_review"] is True
    assert result_empty["analysis_error"] is not None

    # 2. Test unexpected internal exception handling
    monkeypatch.setattr(ai, "categorize_text", lambda text: (_ for _ in ()).throw(RuntimeError("Simulated pipeline crash")))
    result_crash = ai.analyze_complaint(
        description="A valid complaint text that hits a crash.",
        citizen_category="Waste",
        latitude=12.0,
        longitude=77.0,
        area="Hampankatta",
    )
    assert result_crash["analysis_status"] == "incomplete"
    assert result_crash["needs_review"] is True
    assert "Analysis encountered error" in result_crash["analysis_error"]
