"""
CityGuard Synthetic Data Generator (Mangaluru City Corporation - MCC)
Generates 40 realistic, diverse civic complaints across 5 real Mangalore municipal zones:
- Hampankatta (Central Commercial & Market District)
- Kadri Hills (Residential, Kadri Temple, Park, & Nanthoor corridor)
- Lalbagh - Ladyhill (MCC City Corporation HQ, MG Road, & Ladyhill Circle)
- Kankanady - Pumpwell (Healthcare corridor, Father Muller, & Pumpwell Junction)
- Surathkal - Kulai (Industrial belt, Coastal Highway, & Educational zone)

Explicitly covers:
- Paraphrased duplicate clusters (e.g. monsoon pothole crater in Hampankatta)
- Distant reports with identical phrasing (testing distance filtering across city)
- Nearby reports with mismatched categories (testing category guardrails)
- Explicit high-risk safety hazards (e.g. exposed culvert near school)
- Negated hazard phrasing ("repaired, no danger")
- Ambiguous complaints requiring review
- Pre-resolved reports to verify duplicate exclusion
- Idempotent seeding using unique `seed_id`
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path

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


# 40 Real Mangaluru Municipal Complaints
RAW_SEED_COMPLAINTS: List[Dict[str, Any]] = [
    # ---------------- ROAD DAMAGE (8 Reports) ----------------
    {
        "seed_id": "SEED-ROAD-001",
        "description": "Massive deep pothole on Hampankatta K.S. Rao Road near Central Market. Cars are swerving dangerously into oncoming traffic to avoid it.",
        "citizen_category": "Road damage",
        "area": "Hampankatta",
        "lat": 12.8705,
        "lon": 74.8429,
        "created_at": days_ago(2, 3),
        "status": "Submitted",
        "department": None,
    },
    {
        # Paraphrased duplicate of SEED-ROAD-001 (same location within 35m, 1 day later)
        "seed_id": "SEED-ROAD-002",
        "description": "Huge crater in the asphalt right opposite Central Market entrance on K.S. Rao Road. Several two-wheelers nearly crashed this morning.",
        "citizen_category": "Road damage",
        "area": "Hampankatta",
        "lat": 12.8706,
        "lon": 74.8430,
        "created_at": days_ago(1, 1),
        "status": "Submitted",
        "department": None,
    },
    {
        # Distant report with similar wording in Surathkal (> 15 km away) to test distance filtering
        "seed_id": "SEED-ROAD-003",
        "description": "Deep pothole on highway road near Surathkal port junction. Heavy trucks are swerving to avoid tire damage.",
        "citizen_category": "Road damage",
        "area": "Surathkal - Kulai",
        "lat": 13.0108,
        "lon": 74.7943,
        "created_at": days_ago(3, 4),
        "status": "Reviewed",
        "department": "Roads",
    },
    {
        # Explicit hazard: road collapsing near school
        "seed_id": "SEED-ROAD-004",
        "description": "Asphalt is collapsing road surface forming a sinkhole right in front of Hampankatta St. Aloysius School Gate. Deep ditch exposes culvert.",
        "citizen_category": "Road damage",
        "area": "Hampankatta",
        "lat": 12.8710,
        "lon": 74.8435,
        "created_at": days_ago(0, 5),
        "status": "Assigned",
        "department": "Roads",
    },
    {
        # Negated hazard scenario
        "seed_id": "SEED-ROAD-005",
        "description": "Road surface repaired last week, not a hazard now, but contractors left loose gravel on the corner of Surathkal 4th cross.",
        "citizen_category": "Road damage",
        "area": "Surathkal - Kulai",
        "lat": 13.0112,
        "lon": 74.7948,
        "created_at": days_ago(4, 2),
        "status": "Reviewed",
        "department": "Roads",
    },
    {
        "seed_id": "SEED-ROAD-006",
        "description": "Cracked pavement and uneven road along Kadri Park promenade causing morning walkers and elderly pedestrians to trip.",
        "citizen_category": "Road damage",
        "area": "Kadri Hills",
        "lat": 12.8945,
        "lon": 74.8619,
        "created_at": days_ago(5, 6),
        "status": "In progress",
        "department": "Roads",
    },
    {
        # Resolved complaint (must be excluded from active duplicate candidate suggestions)
        "seed_id": "SEED-ROAD-007",
        "description": "Broken road surface and sharp asphalt edges on Kankanady 2nd Cross near junction.",
        "citizen_category": "Road damage",
        "area": "Kankanady - Pumpwell",
        "lat": 12.8670,
        "lon": 74.8626,
        "created_at": days_ago(9, 0),
        "status": "Resolved",
        "department": "Roads",
        "resolution_note": "Asphalt patched and surface rolled by Mangalore City Corporation road crew.",
    },
    {
        "seed_id": "SEED-ROAD-008",
        "description": "Road blocked completely by collapsed retaining wall and broken road boulders after storm near Kadri Temple hillside road.",
        "citizen_category": "Road damage",
        "area": "Kadri Hills",
        "lat": 12.8950,
        "lon": 74.8625,
        "created_at": days_ago(1, 4),
        "status": "Assigned",
        "department": "Roads",
    },

    # ---------------- WASTE (8 Reports) ----------------
    {
        "seed_id": "SEED-WASTE-001",
        "description": "Overflowing bin and uncollected garbage rotting on the corner of Kankanady Market Road. Terrible stench attracting stray dogs.",
        "citizen_category": "Waste",
        "area": "Kankanady - Pumpwell",
        "lat": 12.8669,
        "lon": 74.8625,
        "created_at": days_ago(1, 2),
        "status": "Submitted",
        "department": None,
    },
    {
        # Duplicate of SEED-WASTE-001 (same location within 30m, 12 hours later)
        "seed_id": "SEED-WASTE-002",
        "description": "Severe garbage dumping behind Kankanady Market Road shops. Trash has spilled across the entire sidewalk with foul smell.",
        "citizen_category": "Waste",
        "area": "Kankanady - Pumpwell",
        "lat": 12.8671,
        "lon": 74.8627,
        "created_at": days_ago(0, 14),
        "status": "Submitted",
        "department": None,
    },
    {
        # Nearby to SEED-ROAD-001 in Hampankatta (within 35m) but incompatible category (Waste vs Road damage)
        "seed_id": "SEED-WASTE-003",
        "description": "Commercial plastic waste and rubbish dumped in open lot adjacent to Central Market parking.",
        "citizen_category": "Waste",
        "area": "Hampankatta",
        "lat": 12.8704,
        "lon": 74.8428,
        "created_at": days_ago(2, 1),
        "status": "Submitted",
        "department": None,
    },
    {
        # Sensitive setting: Hospital (Father Muller Hospital)
        "seed_id": "SEED-WASTE-004",
        "description": "Medical refuse and rotting waste dumped illegally outside Kankanady Father Muller Hospital emergency gate.",
        "citizen_category": "Waste",
        "area": "Kankanady - Pumpwell",
        "lat": 12.8672,
        "lon": 74.8628,
        "created_at": days_ago(0, 8),
        "status": "Assigned",
        "department": "Sanitation",
    },
    {
        "seed_id": "SEED-WASTE-005",
        "description": "Construction debris and bulk trash blocking pedestrian walkway near Surathkal industrial freight siding.",
        "citizen_category": "Waste",
        "area": "Surathkal - Kulai",
        "lat": 13.0115,
        "lon": 74.7950,
        "created_at": days_ago(3, 1),
        "status": "Reviewed",
        "department": "Sanitation",
    },
    {
        # Resolved waste issue
        "seed_id": "SEED-WASTE-006",
        "description": "Dead animal and rotting trash pile on Kadri Park walking track pathway.",
        "citizen_category": "Waste",
        "area": "Kadri Hills",
        "lat": 12.8940,
        "lon": 74.8612,
        "created_at": days_ago(6, 0),
        "status": "Resolved",
        "department": "Sanitation",
        "resolution_note": "Special MCC sanitation team cleared carcass and sanitized pavement.",
    },
    {
        "seed_id": "SEED-WASTE-007",
        "description": "Community sanitation bin broken and upside down, spilling litter across Lalbagh public park lawn.",
        "citizen_category": "Waste",
        "area": "Lalbagh - Ladyhill",
        "lat": 12.8870,
        "lon": 74.8395,
        "created_at": days_ago(4, 5),
        "status": "Reviewed",
        "department": "Sanitation",
    },
    {
        "seed_id": "SEED-WASTE-008",
        "description": "Massive plastic dump and chemical container filth near Surathkal industrial warehouse gate 4.",
        "citizen_category": "Waste",
        "area": "Surathkal - Kulai",
        "lat": 13.0105,
        "lon": 74.7940,
        "created_at": days_ago(2, 6),
        "status": "In progress",
        "department": "Sanitation",
    },

    # ---------------- DRAINAGE / WATERLOGGING (10 Reports) ----------------
    # Notice: Kadri Hills cluster for Area Action Brief demonstration!
    {
        "seed_id": "SEED-DRAIN-001",
        "description": "Severely clogged storm drain causing stagnant water and overflowing sewer on Kadri Temple south lane.",
        "citizen_category": "Drainage / waterlogging",
        "area": "Kadri Hills",
        "lat": 12.8943,
        "lon": 74.8617,
        "created_at": days_ago(1, 6),
        "status": "Submitted",
        "department": None,
    },
    {
        # Paraphrased duplicate of SEED-DRAIN-001 (within 45m, 10 hours later)
        "seed_id": "SEED-DRAIN-002",
        "description": "Open drain overflowing with black sewage water near Kadri Temple south lane houses. Flooding into ground floor stairs.",
        "citizen_category": "Drainage / waterlogging",
        "area": "Kadri Hills",
        "lat": 12.8944,
        "lon": 74.8618,
        "created_at": days_ago(0, 18),
        "status": "Submitted",
        "department": None,
    },
    {
        # Third in cluster at Kadri Hills (Drainage + blocked access)
        "seed_id": "SEED-DRAIN-003",
        "description": "Rainwater flooding culvert completely blocked. Entire street flooded with waterlogging reaching 2 feet deep near Kadri Park.",
        "citizen_category": "Drainage / waterlogging",
        "area": "Kadri Hills",
        "lat": 12.8946,
        "lon": 74.8620,
        "created_at": days_ago(1, 0),
        "status": "Assigned",
        "department": "Drainage",
    },
    {
        # Fourth in Kadri Hills
        "seed_id": "SEED-DRAIN-004",
        "description": "Stormwater gutter choked with silt and debris on Kadri Hills 3rd avenue causing waterlogging.",
        "citizen_category": "Drainage / waterlogging",
        "area": "Kadri Hills",
        "lat": 12.8938,
        "lon": 74.8610,
        "created_at": days_ago(2, 4),
        "status": "Reviewed",
        "department": "Drainage",
    },
    {
        # Hazard: Open manhole near school in Hampankatta
        "seed_id": "SEED-DRAIN-005",
        "description": "Open manhole uncovered on the sidewalk right outside Hampankatta St. Aloysius School Gate. Deep sewer drop is an active hazard for children.",
        "citizen_category": "Drainage / waterlogging",
        "area": "Hampankatta",
        "lat": 12.8711,
        "lon": 74.8436,
        "created_at": days_ago(0, 3),
        "status": "Assigned",
        "department": "Drainage",
    },
    {
        "seed_id": "SEED-DRAIN-006",
        "description": "Drainage cesspool overflowing into Lalbagh MCC bus stop passenger concourse.",
        "citizen_category": "Drainage / waterlogging",
        "area": "Lalbagh - Ladyhill",
        "lat": 12.8871,
        "lon": 74.8396,
        "created_at": days_ago(3, 7),
        "status": "Reviewed",
        "department": "Drainage",
    },
    {
        "seed_id": "SEED-DRAIN-007",
        "description": "Broken culvert wall causing sewage backup into residential basements on Pumpwell 5th Cross.",
        "citizen_category": "Drainage / waterlogging",
        "area": "Kankanady - Pumpwell",
        "lat": 12.8665,
        "lon": 74.8620,
        "created_at": days_ago(2, 8),
        "status": "In progress",
        "department": "Drainage",
    },
    {
        "seed_id": "SEED-DRAIN-008",
        "description": "Industrial stormwater drain blocked by factory slag on Surathkal 1st Main road.",
        "citizen_category": "Drainage / waterlogging",
        "area": "Surathkal - Kulai",
        "lat": 13.0110,
        "lon": 74.7945,
        "created_at": days_ago(4, 0),
        "status": "Reviewed",
        "department": "Drainage",
    },
    {
        # Negation test: puddle without hazard
        "seed_id": "SEED-DRAIN-009",
        "description": "Minor water puddle on Hampankatta avenue, no danger or flooding, but drain cover makes a loud clanging noise when vehicles drive over.",
        "citizen_category": "Drainage / waterlogging",
        "area": "Hampankatta",
        "lat": 12.8708,
        "lon": 74.8432,
        "created_at": days_ago(5, 1),
        "status": "Reviewed",
        "department": "Drainage",
    },
    {
        # Waterlogging in underpass / access blocked (Pumpwell junction famous waterlogging spot)
        "seed_id": "SEED-DRAIN-010",
        "description": "Severe monsoon flooding in Pumpwell circle underpass. Water level 3 feet, impassable road, vehicles stuck completely.",
        "citizen_category": "Drainage / waterlogging",
        "area": "Kankanady - Pumpwell",
        "lat": 12.8660,
        "lon": 74.8615,
        "created_at": days_ago(0, 4),
        "status": "Assigned",
        "department": "Drainage",
    },

    # ---------------- STREETLIGHTS / ELECTRICAL (8 Reports) ----------------
    {
        "seed_id": "SEED-ELEC-001",
        "description": "Streetlight pole bent and lamp post off for over a week along Hampankatta residential colony.",
        "citizen_category": "Streetlights / electrical",
        "area": "Hampankatta",
        "lat": 12.8701,
        "lon": 74.8424,
        "created_at": days_ago(3, 5),
        "status": "Submitted",
        "department": None,
    },
    {
        # Duplicate of SEED-ELEC-001 (same pole, within 25m, 1 day later)
        "seed_id": "SEED-ELEC-002",
        "description": "Street light completely dead and dark on corner of Hampankatta residential colony. Pitch black night road.",
        "citizen_category": "Streetlights / electrical",
        "area": "Hampankatta",
        "lat": 12.8702,
        "lon": 74.8425,
        "created_at": days_ago(2, 6),
        "status": "Submitted",
        "department": None,
    },
    {
        # High Risk: Exposed live wire
        "seed_id": "SEED-ELEC-003",
        "description": "Live electric wire hanging down from transformer pole right near Ladyhill circle bus shelter! Sparks flying in rain. Immediate life hazard!",
        "citizen_category": "Streetlights / electrical",
        "area": "Lalbagh - Ladyhill",
        "lat": 12.8875,
        "lon": 74.8402,
        "created_at": days_ago(0, 2),
        "status": "Assigned",
        "department": "Electrical maintenance",
    },
    {
        # Near hospital
        "seed_id": "SEED-ELEC-004",
        "description": "All street lamps extinguished along road leading to Kankanady Father Muller Hospital entrance. Patients struggling in darkness.",
        "citizen_category": "Streetlights / electrical",
        "area": "Kankanady - Pumpwell",
        "lat": 12.8674,
        "lon": 74.8630,
        "created_at": days_ago(1, 8),
        "status": "In progress",
        "department": "Electrical maintenance",
    },
    {
        "seed_id": "SEED-ELEC-005",
        "description": "Flickering streetlights creating strobe light effect along Kadri Hills ring road.",
        "citizen_category": "Streetlights / electrical",
        "area": "Kadri Hills",
        "lat": 12.8948,
        "lon": 74.8622,
        "created_at": days_ago(4, 9),
        "status": "Reviewed",
        "department": "Electrical maintenance",
    },
    {
        # Negated electrical hazard
        "seed_id": "SEED-ELEC-006",
        "description": "Electric line was disconnected by technicians and is not live now, but the empty cable bracket is hanging loose over Hampankatta pavement.",
        "citizen_category": "Streetlights / electrical",
        "area": "Hampankatta",
        "lat": 12.8709,
        "lon": 74.8433,
        "created_at": days_ago(5, 3),
        "status": "Reviewed",
        "department": "Electrical maintenance",
    },
    {
        "seed_id": "SEED-ELEC-007",
        "description": "Underground electrical cable junction box cover missing on Surathkal highway pavement. Kids riding bicycles nearby.",
        "citizen_category": "Streetlights / electrical",
        "area": "Surathkal - Kulai",
        "lat": 13.0118,
        "lon": 74.7952,
        "created_at": days_ago(0, 9),
        "status": "Assigned",
        "department": "Electrical maintenance",
    },
    {
        # Resolved electrical
        "seed_id": "SEED-ELEC-008",
        "description": "Blown fuse on municipal lamp pole outside Lalbagh post office.",
        "citizen_category": "Streetlights / electrical",
        "area": "Lalbagh - Ladyhill",
        "lat": 12.8868,
        "lon": 74.8392,
        "created_at": days_ago(8, 0),
        "status": "Resolved",
        "department": "Electrical maintenance",
        "resolution_note": "Fuse replaced and LED luminaire restored by MESCOM electrical line crew.",
    },

    # ---------------- WATER SUPPLY (6 Reports) ----------------
    {
        "seed_id": "SEED-WATER-001",
        "description": "Major main pipeline burst shooting water 10 feet into the air on Surathkal highway. Potable water flooding road.",
        "citizen_category": "Water supply",
        "area": "Surathkal - Kulai",
        "lat": 13.0109,
        "lon": 74.7944,
        "created_at": days_ago(0, 6),
        "status": "Assigned",
        "department": "Water services",
    },
    {
        # Duplicate of SEED-WATER-001 (same burst pipe, within 30m, 3 hours later)
        "seed_id": "SEED-WATER-002",
        "description": "Broken municipal water pipe leaking drinking water continuously near Surathkal highway turn. Clean water wasted.",
        "citizen_category": "Water supply",
        "area": "Surathkal - Kulai",
        "lat": 13.0111,
        "lon": 74.7946,
        "created_at": days_ago(0, 3),
        "status": "Submitted",
        "department": None,
    },
    {
        "seed_id": "SEED-WATER-003",
        "description": "No tap water supply for 4 consecutive days in Lalbagh Gandhinagar residential blocks. Water tanker urgently needed.",
        "citizen_category": "Water supply",
        "area": "Lalbagh - Ladyhill",
        "lat": 12.8876,
        "lon": 74.8404,
        "created_at": days_ago(1, 10),
        "status": "In progress",
        "department": "Water services",
    },
    {
        "seed_id": "SEED-WATER-004",
        "description": "Brown discolored drinking water coming from municipal tap line with mud odor in Kadri Hills homes.",
        "citizen_category": "Water supply",
        "area": "Kadri Hills",
        "lat": 12.8941,
        "lon": 74.8614,
        "created_at": days_ago(2, 2),
        "status": "Reviewed",
        "department": "Water services",
    },
    {
        "seed_id": "SEED-WATER-005",
        "description": "Water pipeline valve chamber cover broken on Kankanady Bypass. Water gushing when pressure valve opens.",
        "citizen_category": "Water supply",
        "area": "Kankanady - Pumpwell",
        "lat": 12.8667,
        "lon": 74.8622,
        "created_at": days_ago(3, 3),
        "status": "Reviewed",
        "department": "Water services",
    },
    {
        # Resolved water supply issue
        "seed_id": "SEED-WATER-006",
        "description": "Leaking pipe valve on water tanker refilling station near Hampankatta water works.",
        "citizen_category": "Water supply",
        "area": "Hampankatta",
        "lat": 12.8702,
        "lon": 74.8423,
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

        desc = item["description"]
        cit_cat = item["citizen_category"]
        area = item["area"]
        lat = item["lat"]
        lon = item["lon"]
        created = item["created_at"]
        status = item["status"]
        dept = item["department"]

        # Run through full AI pipeline
        analysis = analyze_complaint(
            description=desc,
            citizen_category=cit_cat,
            latitude=lat,
            longitude=lon,
            area=area,
            existing_reports=existing_reports,
            model=model,
        )

        # Build payload
        token = f"CIVIC-{sid.replace('SEED-', '')}"
        report_payload = {
            "seed_id": sid,
            "tracking_token": token,
            "description": desc,
            "citizen_category": cit_cat,
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
            "workflow_status": status,
            "assigned_department": dept,
            "created_at": created,
        }

        report_id = insert_report(report_payload)
        inserted_count += 1

        # Record duplicate candidates
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
        report_payload["tracking_token"] = token
        existing_reports.append(report_payload)

    if verbose:
        print(f"Successfully seeded {inserted_count} synthetic Mangaluru complaints.")
    return inserted_count


if __name__ == "__main__":
    count = seed_database(force_reseed=True, verbose=True)
    print(f"Seed complete. {count} records processed.")
