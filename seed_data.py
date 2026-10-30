"""
CivicAction Synthetic Data Generator
Generates 40 realistic, diverse fictional municipal complaints across 5 demo areas.
Explicitly covers:
- Paraphrased duplicate clusters
- Distant reports with identical phrasing
- Nearby reports with mismatched categories
- Explicit high-risk safety hazards
- Negated hazard phrasing
- Ambiguous complaints requiring review
- Pre-resolved reports to verify duplicate exclusion
- Idempotent seeding using unique `seed_id`
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from ai_pipeline import analyze_complaint, get_embedding_model
from config import DEMO_AREAS
from database import (
    add_status_event,
    get_all_reports,
    get_db_connection,
    init_db,
    insert_report,
    record_duplicate_candidate,
    utc_now_iso,
)

NOW = datetime.now(timezone.utc)

def days_ago(d: float, hours: float = 0) -> str:
    """Helper to generate consistent ISO UTC timestamps in the past."""
    dt = NOW - timedelta(days=d, hours=hours)
    return dt.isoformat()


# 40 Fictional Complaints
RAW_SEED_COMPLAINTS: List[Dict[str, Any]] = [
    # ---------------- ROAD DAMAGE (8 Reports) ----------------
    {
        "seed_id": "SEED-ROAD-001",
        "description": "Massive deep pothole on Oakridge Main Road near Central Market. Cars are swerving dangerously into oncoming traffic to avoid it.",
        "citizen_category": "Road damage",
        "area": "Oakridge Heights",
        "lat": 12.9718,
        "lon": 77.5948,
        "created_at": days_ago(2, 3),
        "status": "Submitted",
        "department": None,
    },
    {
        # Paraphrased duplicate of SEED-ROAD-001 (same location within 40m, 1 day later)
        "seed_id": "SEED-ROAD-002",
        "description": "Huge crater in the asphalt right opposite Central Market entrance. Several two-wheelers nearly crashed this morning.",
        "citizen_category": "Road damage",
        "area": "Oakridge Heights",
        "lat": 12.9719,
        "lon": 77.5949,
        "created_at": days_ago(1, 1),
        "status": "Submitted",
        "department": None,
    },
    {
        # Distant report with similar wording in Harbor Ward (> 3 km away) to test distance filtering
        "seed_id": "SEED-ROAD-003",
        "description": "Deep pothole on harbor boulevard near dock gate 2. Cars are swerving to avoid tire damage.",
        "citizen_category": "Road damage",
        "area": "Harbor Ward",
        "lat": 12.9650,
        "lon": 77.6120,
        "created_at": days_ago(3, 4),
        "status": "Reviewed",
        "department": "Roads",
    },
    {
        # Explicit hazard: road collapsing
        "seed_id": "SEED-ROAD-004",
        "description": "Asphalt is collapsing road surface forming a sinkhole right in front of Oakridge North Primary School. Deep ditch exposes culvert.",
        "citizen_category": "Road damage",
        "area": "Oakridge Heights",
        "lat": 12.9725,
        "lon": 77.5952,
        "created_at": days_ago(0, 5),
        "status": "Assigned",
        "department": "Roads",
    },
    {
        # Negated hazard scenario
        "seed_id": "SEED-ROAD-005",
        "description": "Road surface repaired last week, not a hazard now, but contractors left loose gravel on the corner of Elmwood 4th cross.",
        "citizen_category": "Road damage",
        "area": "Elmwood Industrial",
        "lat": 12.9552,
        "lon": 77.5752,
        "created_at": days_ago(4, 2),
        "status": "Reviewed",
        "department": "Roads",
    },
    {
        "seed_id": "SEED-ROAD-006",
        "description": "Cracked pavement and uneven road along Maple Riverside promenade causing pedestrians to trip.",
        "citizen_category": "Road damage",
        "area": "Maple Riverside",
        "lat": 12.9822,
        "lon": 77.6054,
        "created_at": days_ago(5, 6),
        "status": "In progress",
        "department": "Roads",
    },
    {
        # Resolved complaint (must be excluded from active duplicate candidate suggestions)
        "seed_id": "SEED-ROAD-007",
        "description": "Broken road surface and sharp asphalt edges on Pineview 2nd Ave near junction.",
        "citizen_category": "Road damage",
        "area": "Pineview Central",
        "lat": 12.9782,
        "lon": 77.5852,
        "created_at": days_ago(9, 0),
        "status": "Resolved",
        "department": "Roads",
        "resolution_note": "Asphalt patched and surface rolled by municipal road crew.",
    },
    {
        "seed_id": "SEED-ROAD-008",
        "description": "Road blocked completely by collapsed retaining wall and broken road boulders after storm near Maple hillside road.",
        "citizen_category": "Road damage",
        "area": "Maple Riverside",
        "lat": 12.9830,
        "lon": 77.6060,
        "created_at": days_ago(1, 4),
        "status": "Assigned",
        "department": "Roads",
    },

    # ---------------- WASTE (8 Reports) ----------------
    {
        "seed_id": "SEED-WASTE-001",
        "description": "Overflowing bin and uncollected garbage rotting on the corner of Pineview Market Street. Terrible stench attracting stray dogs.",
        "citizen_category": "Waste",
        "area": "Pineview Central",
        "lat": 12.9785,
        "lon": 77.5858,
        "created_at": days_ago(1, 2),
        "status": "Submitted",
        "department": None,
    },
    {
        # Duplicate of SEED-WASTE-001 (same location within 30m, 12 hours later)
        "seed_id": "SEED-WASTE-002",
        "description": "Severe garbage dumping behind Pineview Market street shops. Trash has spilled across the entire sidewalk with foul smell.",
        "citizen_category": "Waste",
        "area": "Pineview Central",
        "lat": 12.9786,
        "lon": 77.5859,
        "created_at": days_ago(0, 14),
        "status": "Submitted",
        "department": None,
    },
    {
        # Nearby to SEED-ROAD-001 in Oakridge (within 35m) but incompatible category (Waste vs Road damage)
        "seed_id": "SEED-WASTE-003",
        "description": "Commercial plastic waste and rubbish dumped in open lot adjacent to Central Market parking.",
        "citizen_category": "Waste",
        "area": "Oakridge Heights",
        "lat": 12.9717,
        "lon": 77.5947,
        "created_at": days_ago(2, 1),
        "status": "Submitted",
        "department": None,
    },
    {
        # Sensitive setting: Hospital
        "seed_id": "SEED-WASTE-004",
        "description": "Medical refuse and rotting waste dumped illegally outside Harbor Ward Primary Hospital emergency entrance.",
        "citizen_category": "Waste",
        "area": "Harbor Ward",
        "lat": 12.9655,
        "lon": 77.6125,
        "created_at": days_ago(0, 8),
        "status": "Assigned",
        "department": "Sanitation",
    },
    {
        "seed_id": "SEED-WASTE-005",
        "description": "Construction debris and bulk trash blocking pedestrian walkway near Elmwood industrial freight siding.",
        "citizen_category": "Waste",
        "area": "Elmwood Industrial",
        "lat": 12.9558,
        "lon": 77.5758,
        "created_at": days_ago(3, 1),
        "status": "Reviewed",
        "department": "Sanitation",
    },
    {
        # Resolved waste issue
        "seed_id": "SEED-WASTE-006",
        "description": "Dead animal and rotting trash pile on Maple Riverside greenway path.",
        "citizen_category": "Waste",
        "area": "Maple Riverside",
        "lat": 12.9818,
        "lon": 77.6048,
        "created_at": days_ago(6, 0),
        "status": "Resolved",
        "department": "Sanitation",
        "resolution_note": "Special sanitation pickup cleared carcass and sanitized pavement.",
    },
    {
        "seed_id": "SEED-WASTE-007",
        "description": "Community sanitation bin broken and upside down, spilling litter across Pineview playground lawn.",
        "citizen_category": "Waste",
        "area": "Pineview Central",
        "lat": 12.9778,
        "lon": 77.5845,
        "created_at": days_ago(4, 5),
        "status": "Reviewed",
        "department": "Sanitation",
    },
    {
        "seed_id": "SEED-WASTE-008",
        "description": "Massive plastic dump and chemical container filth near Elmwood warehouse gate 4.",
        "citizen_category": "Waste",
        "area": "Elmwood Industrial",
        "lat": 12.9548,
        "lon": 77.5745,
        "created_at": days_ago(2, 6),
        "status": "In progress",
        "department": "Sanitation",
    },

    # ---------------- DRAINAGE / WATERLOGGING (10 Reports) ----------------
    # Notice: Maple Riverside cluster for Area Action Brief demonstration!
    {
        "seed_id": "SEED-DRAIN-001",
        "description": "Severely clogged drain causing stagnant water and overflowing sewer on Maple Riverside south lane.",
        "citizen_category": "Drainage / waterlogging",
        "area": "Maple Riverside",
        "lat": 12.9821,
        "lon": 77.6052,
        "created_at": days_ago(1, 6),
        "status": "Submitted",
        "department": None,
    },
    {
        # Paraphrased duplicate of SEED-DRAIN-001 (within 45m, 10 hours later)
        "seed_id": "SEED-DRAIN-002",
        "description": "Open drain overflowing with black sewage water near Maple Riverside south lane houses. Flooding into ground floor stairs.",
        "citizen_category": "Drainage / waterlogging",
        "area": "Maple Riverside",
        "lat": 12.9823,
        "lon": 77.6053,
        "created_at": days_ago(0, 18),
        "status": "Submitted",
        "department": None,
    },
    {
        # Third in cluster at Maple Riverside (Drainage + blocked access)
        "seed_id": "SEED-DRAIN-003",
        "description": "Rainwater flooding culvert completely blocked. Entire street flooded with waterlogging reaching 2 feet deep near Riverside park.",
        "citizen_category": "Drainage / waterlogging",
        "area": "Maple Riverside",
        "lat": 12.9825,
        "lon": 77.6056,
        "created_at": days_ago(1, 0),
        "status": "Assigned",
        "department": "Drainage",
    },
    {
        # Fourth in Maple Riverside
        "seed_id": "SEED-DRAIN-004",
        "description": "Stormwater gutter choked with silt and debris on Maple Riverside 3rd avenue causing waterlogging.",
        "citizen_category": "Drainage / waterlogging",
        "area": "Maple Riverside",
        "lat": 12.9815,
        "lon": 77.6045,
        "created_at": days_ago(2, 4),
        "status": "Reviewed",
        "department": "Drainage",
    },
    {
        # Hazard: Open manhole near school
        "seed_id": "SEED-DRAIN-005",
        "description": "Open manhole uncovered on the sidewalk right outside Oakridge Primary School. Deep sewer drop is an active hazard for children.",
        "citizen_category": "Drainage / waterlogging",
        "area": "Oakridge Heights",
        "lat": 12.9726,
        "lon": 77.5953,
        "created_at": days_ago(0, 3),
        "status": "Assigned",
        "department": "Drainage",
    },
    {
        "seed_id": "SEED-DRAIN-006",
        "description": "Drainage cesspool overflowing into Harbor Ward ferry terminal pedestrian concourse.",
        "citizen_category": "Drainage / waterlogging",
        "area": "Harbor Ward",
        "lat": 12.9648,
        "lon": 77.6118,
        "created_at": days_ago(3, 7),
        "status": "Reviewed",
        "department": "Drainage",
    },
    {
        "seed_id": "SEED-DRAIN-007",
        "description": "Broken culvert wall causing sewage backup into residential basements on Pineview 5th street.",
        "citizen_category": "Drainage / waterlogging",
        "area": "Pineview Central",
        "lat": 12.9788,
        "lon": 77.5862,
        "created_at": days_ago(2, 8),
        "status": "In progress",
        "department": "Drainage",
    },
    {
        "seed_id": "SEED-DRAIN-008",
        "description": "Industrial stormwater drain blocked by factory slag on Elmwood 1st Main road.",
        "citizen_category": "Drainage / waterlogging",
        "area": "Elmwood Industrial",
        "lat": 12.9554,
        "lon": 77.5754,
        "created_at": days_ago(4, 1),
        "status": "Reviewed",
        "department": "Drainage",
    },
    {
        # Resolved drainage report
        "seed_id": "SEED-DRAIN-009",
        "description": "Heavy waterlogging and clogged drain grating at Pineview Central roundabout.",
        "citizen_category": "Drainage / waterlogging",
        "area": "Pineview Central",
        "lat": 12.9775,
        "lon": 77.5840,
        "created_at": days_ago(8, 0),
        "status": "Resolved",
        "department": "Drainage",
        "resolution_note": "Jetting machine cleared the storm grate; water drained completely.",
    },
    {
        # Negated drainage hazard
        "seed_id": "SEED-DRAIN-010",
        "description": "Minor water puddle on Oakridge avenue, no danger or flooding, but drain cover makes a loud clanging noise when vehicles drive over.",
        "citizen_category": "Drainage / waterlogging",
        "area": "Oakridge Heights",
        "lat": 12.9712,
        "lon": 77.5940,
        "created_at": days_ago(3, 2),
        "status": "Submitted",
        "department": None,
    },

    # ---------------- STREETLIGHTS / ELECTRICAL (8 Reports) ----------------
    {
        # Extreme hazard: Live wire
        "seed_id": "SEED-ELEC-001",
        "description": "Downed electrical wire is a live wire sparking on wet pavement near Harbor Ward Primary Hospital clinic gate. Immediate danger of electric shock!",
        "citizen_category": "Streetlights / electrical",
        "area": "Harbor Ward",
        "lat": 12.9656,
        "lon": 77.6126,
        "created_at": days_ago(0, 2),
        "status": "Assigned",
        "department": "Electrical maintenance",
    },
    {
        # Paraphrased duplicate of SEED-ELEC-001 (within 30m, 1 hour later)
        "seed_id": "SEED-ELEC-002",
        "description": "High voltage power cable hanging down and sparking wire near the hospital entrance. Pedestrians running in panic.",
        "citizen_category": "Streetlights / electrical",
        "area": "Harbor Ward",
        "lat": 12.9657,
        "lon": 77.6127,
        "created_at": days_ago(0, 1),
        "status": "Submitted",
        "department": None,
    },
    {
        "seed_id": "SEED-ELEC-003",
        "description": "Streetlight pole bent and lamp post off for over a week along Oakridge residential colony.",
        "citizen_category": "Streetlights / electrical",
        "area": "Oakridge Heights",
        "lat": 12.9720,
        "lon": 77.5950,
        "created_at": days_ago(3, 5),
        "status": "Reviewed",
        "department": "Electrical maintenance",
    },
    {
        "seed_id": "SEED-ELEC-004",
        "description": "Complete blackout on Pineview avenue 4. Five consecutive street lights off creating pitch dark street.",
        "citizen_category": "Streetlights / electrical",
        "area": "Pineview Central",
        "lat": 12.9781,
        "lon": 77.5851,
        "created_at": days_ago(1, 8),
        "status": "Assigned",
        "department": "Electrical maintenance",
    },
    {
        # Resolved electrical issue
        "seed_id": "SEED-ELEC-005",
        "description": "Exposed wire junction box on streetlight pole at Maple Riverside bridge.",
        "citizen_category": "Streetlights / electrical",
        "area": "Maple Riverside",
        "lat": 12.9824,
        "lon": 77.6055,
        "created_at": days_ago(7, 4),
        "status": "Resolved",
        "department": "Electrical maintenance",
        "resolution_note": "Junction box re-insulated and waterproof casing secured.",
    },
    {
        "seed_id": "SEED-ELEC-006",
        "description": "Electrical transformer buzzing loudly with intermittent smoke at Elmwood heavy freight yard.",
        "citizen_category": "Streetlights / electrical",
        "area": "Elmwood Industrial",
        "lat": 12.9556,
        "lon": 77.5756,
        "created_at": days_ago(0, 9),
        "status": "In progress",
        "department": "Electrical maintenance",
    },
    {
        # Negated electrical hazard
        "seed_id": "SEED-ELEC-007",
        "description": "Old telephone cable drooping across alley, not a live wire and no hazard, but hangs too low for delivery vans.",
        "citizen_category": "Streetlights / electrical",
        "area": "Oakridge Heights",
        "lat": 12.9710,
        "lon": 77.5935,
        "created_at": days_ago(4, 3),
        "status": "Submitted",
        "department": None,
    },
    {
        "seed_id": "SEED-ELEC-008",
        "description": "Streetlight flickering like a strobe all night right outside residential bedroom windows on Harbor Ward 3rd cross.",
        "citizen_category": "Streetlights / electrical",
        "area": "Harbor Ward",
        "lat": 12.9645,
        "lon": 77.6115,
        "created_at": days_ago(2, 7),
        "status": "Reviewed",
        "department": "Electrical maintenance",
    },

    # ---------------- WATER SUPPLY (6 Reports) ----------------
    {
        # Major disruption: No water for 4 days
        "seed_id": "SEED-WATER-001",
        "description": "Drinking water supply cut completely. No water for 4 days in entire Maple Riverside block B. Residents carrying buckets from canal.",
        "citizen_category": "Water supply",
        "area": "Maple Riverside",
        "lat": 12.9819,
        "lon": 77.6049,
        "created_at": days_ago(1, 3),
        "status": "Assigned",
        "department": "Water services",
    },
    {
        # Paraphrased duplicate of SEED-WATER-001 (within 60m, 12 hours later)
        "seed_id": "SEED-WATER-002",
        "description": "Total tap water failure in Maple Riverside block B apartments. Main pipeline dried up and no supply for multiple days.",
        "citizen_category": "Water supply",
        "area": "Maple Riverside",
        "lat": 12.9820,
        "lon": 77.6050,
        "created_at": days_ago(0, 15),
        "status": "Submitted",
        "department": None,
    },
    {
        "seed_id": "SEED-WATER-003",
        "description": "Water main burst underground gushing clean drinking water across Elmwood industrial depot road.",
        "citizen_category": "Water supply",
        "area": "Elmwood Industrial",
        "lat": 12.9553,
        "lon": 77.5753,
        "created_at": days_ago(0, 6),
        "status": "In progress",
        "department": "Water services",
    },
    {
        "seed_id": "SEED-WATER-004",
        "description": "Severely contaminated water and muddy water with sewage smell coming out of household taps in Harbor Ward sector 4.",
        "citizen_category": "Water supply",
        "area": "Harbor Ward",
        "lat": 12.9652,
        "lon": 77.6122,
        "created_at": days_ago(2, 5),
        "status": "Reviewed",
        "department": "Water services",
    },
    {
        # Ambiguous report: should trigger 'Other' and needs_review=True
        "seed_id": "SEED-WATER-005",
        "description": "The current civic situation on 7th cross is completely unbearable for all residents and requires immediate official intervention.",
        "citizen_category": "Other",
        "area": "Pineview Central",
        "lat": 12.9783,
        "lon": 77.5853,
        "created_at": days_ago(3, 8),
        "status": "Submitted",
        "department": None,
    },
    {
        # Resolved water supply issue
        "seed_id": "SEED-WATER-006",
        "description": "Leaking pipe valve on water tanker refilling station near Oakridge Heights water works.",
        "citizen_category": "Water supply",
        "area": "Oakridge Heights",
        "lat": 12.9714,
        "lon": 77.5942,
        "created_at": days_ago(10, 0),
        "status": "Resolved",
        "department": "Water services",
        "resolution_note": "Pressure valve replaced by municipal water works technician.",
    },
]


def seed_database(force_reseed: bool = False, verbose: bool = False) -> int:
    """
    Idempotently seed the SQLite database with 40 synthetic records.
    Never overwrites or deletes manual citizen submissions.
    Uses the real analysis pipeline to compute categories, summaries, and priorities.
    Returns count of newly inserted seed reports.
    """
    init_db()

    # Pre-fetch existing seed IDs
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT seed_id FROM reports WHERE seed_id IS NOT NULL;")
        existing_seeds = {row["seed_id"] for row in cursor.fetchall()}

    if existing_seeds and not force_reseed:
        if verbose:
            print(f"Database already contains {len(existing_seeds)} seeded records. Skipping.")
        return 0

    inserted_count = 0
    model = get_embedding_model()

    # Fetch existing reports for duplicate matching context
    existing_reports = get_all_reports()

    for item in RAW_SEED_COMPLAINTS:
        sid = item["seed_id"]
        if sid in existing_seeds and not force_reseed:
            continue

        # Run real analysis pipeline! Do not hardcode AI results.
        analysis = analyze_complaint(
            description=item["description"],
            citizen_category=item["citizen_category"],
            latitude=item["lat"],
            longitude=item["lon"],
            area=item["area"],
            existing_reports=existing_reports,
            model=model,
        )

        report_payload = {
            "seed_id": sid,
            "description": item["description"],
            "citizen_category": item["citizen_category"],
            "predicted_category": analysis["predicted_category"],
            "category_evidence": analysis["category_evidence"],
            "extractive_summary": analysis["extractive_summary"],
            "latitude": item["lat"],
            "longitude": item["lon"],
            "area": item["area"],
            "priority_score": analysis["priority_score"],
            "priority_label": analysis["priority_label"],
            "priority_reasons": analysis["priority_reasons"],
            "needs_review": analysis["needs_review"],
            "analysis_status": analysis["analysis_status"],
            "analysis_error": analysis["analysis_error"],
            "workflow_status": item.get("status", "Submitted"),
            "assigned_department": item.get("department"),
            "created_at": item["created_at"],
        }

        report_id = insert_report(report_payload)
        inserted_count += 1

        # Record duplicate candidates in database if identified
        for dup in analysis.get("duplicate_candidates", []):
            cand_id = dup["candidate_id"]
            sim = dup["similarity_score"]
            dist = dup["distance_meters"]
            record_duplicate_candidate(
                source_id=report_id,
                candidate_id=cand_id,
                similarity=sim,
                distance_meters=dist,
                review_state="suggested",
            )

        # If item has resolution note or specific workflow events, record them
        if item.get("status") == "Resolved" and item.get("resolution_note"):
            add_status_event(
                report_id=report_id,
                event_type="status_change",
                previous_value="In progress",
                new_value="Resolved",
                note=item["resolution_note"],
                is_public=True,
            )
        elif item.get("status") in ("Assigned", "In progress") and item.get("department"):
            add_status_event(
                report_id=report_id,
                event_type="assigned",
                previous_value=None,
                new_value=item["department"],
                note=f"Assigned to {item['department']} department.",
                is_public=True,
            )

        # Add newly inserted report to working list for subsequent duplicate checks
        report_payload["id"] = report_id
        report_payload["tracking_token"] = f"CIVIC-SEED-{inserted_count:04d}"
        existing_reports.append(report_payload)

    if verbose:
        print(f"Successfully seeded {inserted_count} synthetic complaints.")
    return inserted_count


if __name__ == "__main__":
    count = seed_database(verbose=True)
    print(f"Seed complete. {count} records processed.")
