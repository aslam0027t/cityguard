"""
CivicAction AI & Analysis Pipeline
Implements independently testable, transparent modules for:
- Text normalization
- Rule-based categorization with token evidence
- Extractive summarization
- Geographic Haversine distance
- Semantic similarity & duplicate candidate ranking (sentence-transformers)
- Explainable priority scoring with conservative negation handling
- Graceful error recovery and fallback
"""

import json
import logging
import math
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from config import (
    DEFAULT_EMBEDDING_MODEL,
    DUPLICATE_MAX_DISTANCE_METERS,
    DUPLICATE_SIMILARITY_THRESHOLD,
    DUPLICATE_TIME_WINDOW_DAYS,
    MAX_PRIORITY_SCORE,
    PRIORITY_THRESHOLDS,
    PRIORITY_WEIGHTS,
)

logger = logging.getLogger(__name__)

# Rule-based Categorization Dictionary
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "Road damage": [
        "pothole", "potholes", "crater", "craters", "asphalt", "tarmac", "road cave",
        "sinkhole", "uneven road", "broken road", "cracked pavement", "damaged road",
        "road surface", "speed breaker", "street surface", "gravel", "rutted road"
    ],
    "Waste": [
        "garbage", "trash", "waste", "dump", "dumping", "litter", "rubbish",
        "overflowing bin", "debris", "plastic waste", "rotting garbage", "stench",
        "foul smell", "refuse", "sanitation bin", "filth", "dead animal"
    ],
    "Drainage / waterlogging": [
        "drain", "drainage", "waterlogging", "waterlogged", "stagnant water", "flooding",
        "flooded", "clogged drain", "open drain", "sewage", "sewer", "manhole", "overflowing sewer",
        "gutter", "stormwater", "culvert", "cesspool", "rainwater"
    ],
    "Streetlights / electrical": [
        "streetlight", "street light", "lamp post", "electrical wire", "live wire",
        "hanging wire", "transformer", "power cable", "dark street", "sparking wire",
        "blackout", "no light", "street light off", "exposed wire", "short circuit"
    ],
    "Water supply": [
        "water supply", "drinking water", "tap water", "pipeline", "pipe burst",
        "leaking pipe", "low water pressure", "no water", "contaminated water",
        "muddy water", "water tanker", "water main", "supply cut"
    ],
}

# Explainable Priority Lexicon
HAZARD_PATTERNS = [
    r"\blive wire(s)?\b",
    r"\bsparking wire(s)?\b",
    r"\bexposed wire(s)?\b",
    r"\bopen manhole(s)?\b",
    r"\bsinkhole(s)?\b",
    r"\bdeep (open )?crater(s)?\b",
    r"\bopen crater(s)?\b",
    r"\bimmediate (danger|hazard)\b",
    r"\bcollapsing (wall|bridge|road|ceiling)\b",
    r"\belectric shock\b",
    r"\bgas leak\b",
    r"\bfalling pole\b",
    r"\bopen ditch\b",
    r"\bactive fire\b",
    r"\bsevere accident\b",
]

SENSITIVE_PATTERNS = [
    r"\bschool(s)?\b",
    r"\bhospital(s)?\b",
    r"\bclinic(s)?\b",
    r"\bkindergarten(s)?\b",
    r"\bdaycare\b",
    r"\bpediatric\b",
    r"\bnursing home\b",
    r"\bhealth center\b",
    r"\bprimary school\b",
]

DISRUPTION_PATTERNS = [
    r"\broad blocked\b",
    r"\bblocked road\b",
    r"\bimpassable\b",
    r"\bno water for \d+ days\b",
    r"\baccess (is )?(completely )?cut off\b",
    r"\bentire street flooded\b",
    r"\btraffic completely halted\b",
    r"\bcannot enter\b",
    r"\bcannot leave\b",
    r"\bstranded\b",
    r"\bno power for \d+ days\b",
]

# Negation patterns to conservatively avoid false positives
NEGATION_PATTERNS = [
    r"\bno\s+(immediate\s+)?(hazard|danger|live wire|risk|problem)\b",
    r"\bnot\s+(a\s+)?(hazard|dangerous|blocked|sparking|live)\b",
    r"\bisn't\s+(a\s+)?(hazard|dangerous|blocked)\b",
    r"\bwithout\s+any\s+(hazard|danger)\b",
    r"\brepaired\b.*\bno\s+hazard\b",
    r"\bfixed\b.*\bno\s+longer\b",
]


def normalize_text(text: str) -> str:
    """Normalize input text: lowercasing, whitespace trimming, cleaning excessive spaces."""
    if not text:
        return ""
    text = text.strip().lower()
    return re.sub(r"\s+", " ", text)


def categorize_text(text: str) -> Tuple[str, List[str], bool]:
    """
    Transparent, rule-based classification using keyword & phrase matching.
    Returns:
        predicted_category: str
        matched_evidence: List[str]
        needs_review: bool (True if ambiguous, conflicting, or zero matches)
    """
    norm_text = normalize_text(text)
    matched_by_cat: Dict[str, List[str]] = {}

    for cat, keywords in CATEGORY_KEYWORDS.items():
        found = []
        for kw in keywords:
            # Word boundary matching
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, norm_text):
                found.append(kw)
        if found:
            matched_by_cat[cat] = found

    if not matched_by_cat:
        return "Other", [], True

    # Find highest match count
    sorted_cats = sorted(matched_by_cat.items(), key=lambda x: len(x[1]), reverse=True)
    best_cat, best_evidence = sorted_cats[0]

    # Check for tie/conflict
    if len(sorted_cats) > 1 and len(sorted_cats[0][1]) == len(sorted_cats[1][1]):
        combined_evidence = best_evidence + sorted_cats[1][1]
        return "Other", combined_evidence, True

    return best_cat, best_evidence, False


def extract_summary(text: str, category: Optional[str] = None) -> str:
    """
    Produce a concise extractive summary by identifying the most salient
    complaint/issue sentence from the citizen's original text.
    Does not use generative AI; strictly selects verified sentences.
    """
    if not text or not text.strip():
        return ""

    raw_sentences = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 5]

    if not sentences:
        return text.strip()[:140]

    if len(sentences) == 1:
        return sentences[0][:200]

    # Score sentences based on problem indicator keywords
    indicator_words = {
        "overflowing", "broken", "damaged", "leaking", "sparking", "blocked",
        "hazard", "dangerous", "flooded", "pothole", "stench", "garbage",
        "accident", "urgent", "deep", "burst", "cut off", "severe"
    }
    if category and category in CATEGORY_KEYWORDS:
        indicator_words.update(CATEGORY_KEYWORDS[category])

    scored_sentences = []
    for s in sentences:
        norm = normalize_text(s)
        score = sum(1 for w in indicator_words if re.search(r"\b" + re.escape(w) + r"\b", norm))
        # Prefer moderate length sentences (not too short, not unwieldy)
        length_penalty = 0.5 if len(s) > 180 else 1.0
        scored_sentences.append((score * length_penalty, s))

    scored_sentences.sort(key=lambda x: x[0], reverse=True)
    best_sentence = scored_sentences[0][1]
    return best_sentence[:200]


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth in metres
    using the Haversine formula. Pure Python standard library implementation.
    """
    r = 6371000.0  # Earth radius in metres
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def has_negated_hazard(norm_text: str) -> bool:
    """Check if hazard terms are explicitly negated in the text."""
    for pattern in NEGATION_PATTERNS:
        if re.search(pattern, norm_text):
            return True
    return False


def calculate_priority(text: str) -> Tuple[int, str, List[Dict[str, Any]], bool]:
    """
    Explainable, rule-based priority scoring.
    Returns:
        score: int (0 to 100)
        label: str ('High', 'Medium', 'Low')
        factors: List[Dict[str, Any]] (detailed audit evidence)
        needs_review: bool
    """
    norm_text = normalize_text(text)
    score = 0
    factors: List[Dict[str, Any]] = []
    needs_review = False

    is_negated = has_negated_hazard(norm_text)
    if is_negated:
        needs_review = True

    # 1. Immediate Physical Hazard (+60)
    matched_hazards = []
    if not is_negated:
        for p in HAZARD_PATTERNS:
            match = re.search(p, norm_text)
            if match:
                matched_hazards.append(match.group(0))

    if matched_hazards:
        pts = PRIORITY_WEIGHTS["immediate_hazard"]
        score += pts
        factors.append({
            "factor": "Immediate Physical Hazard",
            "points": pts,
            "evidence": matched_hazards,
            "explanation": f"Report contains explicit hazard language: {', '.join(matched_hazards)}."
        })
    elif is_negated:
        factors.append({
            "factor": "Negated Hazard Detected",
            "points": 0,
            "evidence": ["Negation pattern detected"],
            "explanation": "Text contains hazard words but in a negated context; flagged for human review."
        })

    # 2. Sensitive Setting (+20)
    matched_sensitive = []
    for p in SENSITIVE_PATTERNS:
        match = re.search(p, norm_text)
        if match:
            matched_sensitive.append(match.group(0))

    if matched_sensitive:
        pts = PRIORITY_WEIGHTS["sensitive_setting"]
        score += pts
        factors.append({
            "factor": "Sensitive Community Setting",
            "points": pts,
            "evidence": matched_sensitive,
            "explanation": f"Located near sensitive facility: {', '.join(matched_sensitive)}."
        })

    # 3. Blocked Access / Disruption (+20)
    matched_disruptions = []
    for p in DISRUPTION_PATTERNS:
        match = re.search(p, norm_text)
        if match:
            matched_disruptions.append(match.group(0))

    if matched_disruptions:
        pts = PRIORITY_WEIGHTS["blocked_access"]
        score += pts
        factors.append({
            "factor": "Critical Access Disruption",
            "points": pts,
            "evidence": matched_disruptions,
            "explanation": f"Report indicates impassable access or total utility outage: {', '.join(matched_disruptions)}."
        })

    # Cap score
    score = min(score, MAX_PRIORITY_SCORE)

    # Determine Label
    if score >= 60:
        label = "High"
    elif score >= 30:
        label = "Medium"
    else:
        label = "Low"

    return score, label, factors, needs_review


# Embedding Model Loader (Streamlit resource cacheable or standalone)
_EMBEDDING_MODEL_INSTANCE = None
_EMBEDDING_MODEL_ERROR = None


def get_embedding_model(model_name: str = DEFAULT_EMBEDDING_MODEL):
    """
    Safely load SentenceTransformer embedding model.
    Caches instance in-memory. Returns None if torch/transformers unavailable.
    """
    global _EMBEDDING_MODEL_INSTANCE, _EMBEDDING_MODEL_ERROR
    if _EMBEDDING_MODEL_INSTANCE is not None:
        return _EMBEDDING_MODEL_INSTANCE
    if _EMBEDDING_MODEL_ERROR is not None:
        return None

    try:
        from sentence_transformers import SentenceTransformer
        _EMBEDDING_MODEL_INSTANCE = SentenceTransformer(model_name)
        return _EMBEDDING_MODEL_INSTANCE
    except Exception as e:
        _EMBEDDING_MODEL_ERROR = str(e)
        logger.warning(f"Could not load SentenceTransformer: {e}")
        return None


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two numeric vectors."""
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm_a = math.sqrt(sum(a * a for a in vec1))
    norm_b = math.sqrt(sum(b * b for b in vec2))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def find_duplicate_candidates(
    new_report: Dict[str, Any],
    candidate_reports: List[Dict[str, Any]],
    model=None,
    similarity_thresh: float = DUPLICATE_SIMILARITY_THRESHOLD,
    max_dist_m: float = DUPLICATE_MAX_DISTANCE_METERS,
    time_window_days: int = DUPLICATE_TIME_WINDOW_DAYS,
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Find and rank duplicate candidates based on:
    - Distance <= max_dist_m (Haversine)
    - Time difference <= time_window_days
    - Excludes resolved complaints
    - Excludes same report
    - Compatible category
    - Cosine similarity >= similarity_thresh
    Returns:
        candidates: List of ranked candidate dicts
        warning: Optional message if semantic model was unavailable
    """
    new_id = new_report.get("id")
    new_lat = float(new_report["latitude"])
    new_lon = float(new_report["longitude"])
    new_desc = new_report["description"]
    new_cat = new_report.get("citizen_category") or new_report.get("predicted_category")
    new_created_str = new_report.get("created_at")
    
    try:
        new_dt = datetime.fromisoformat(new_created_str) if new_created_str else datetime.now(timezone.utc)
    except Exception:
        new_dt = datetime.now(timezone.utc)

    # 1. Geographic and Temporal Pre-filtering
    filtered: List[Tuple[Dict[str, Any], float, float]] = []
    for cand in candidate_reports:
        # Exclude self
        if new_id is not None and cand.get("id") == new_id:
            continue
        # Exclude resolved complaints
        if cand.get("workflow_status") == "Resolved":
            continue

        cand_lat = float(cand["latitude"])
        cand_lon = float(cand["longitude"])
        dist = haversine_distance(new_lat, new_lon, cand_lat, cand_lon)
        if dist > max_dist_m:
            continue

        # Time difference filter
        cand_created_str = cand.get("created_at")
        try:
            cand_dt = datetime.fromisoformat(cand_created_str) if cand_created_str else new_dt
            diff_days = abs((new_dt - cand_dt).total_seconds()) / 86400.0
        except Exception:
            diff_days = 0.0

        if diff_days > time_window_days:
            continue

        # Category compatibility check (allow if same category or either is 'Other')
        cand_cat = cand.get("citizen_category") or cand.get("predicted_category")
        if new_cat and cand_cat and new_cat != "Other" and cand_cat != "Other":
            if new_cat != cand_cat:
                continue

        filtered.append((cand, dist, diff_days))

    if not filtered:
        return [], None

    # 2. Semantic Similarity Calculation
    if model is None:
        model = get_embedding_model()

    if model is None:
        return [], "Semantic embedding model unavailable. Semantic duplicate detection was skipped."

    try:
        new_emb = model.encode(new_desc, convert_to_numpy=True).tolist()
        cand_texts = [item[0]["description"] for item in filtered]
        cand_embs = model.encode(cand_texts, convert_to_numpy=True).tolist()
    except Exception as e:
        logger.error(f"Embedding computation error: {e}")
        return [], f"Semantic embedding calculation failed: {e}"

    results = []
    for i, (cand, dist, diff_days) in enumerate(filtered):
        sim = cosine_similarity(new_emb, cand_embs[i])
        if sim >= similarity_thresh:
            results.append({
                "candidate_id": cand["id"],
                "candidate_token": cand["tracking_token"],
                "summary": cand.get("extractive_summary") or cand["description"][:100],
                "similarity_score": round(float(sim), 4),
                "distance_meters": round(dist, 1),
                "days_elapsed": round(diff_days, 1),
                "area": cand.get("area"),
                "status": cand.get("workflow_status"),
                "note": "Suggested candidate for officer review; review required before confirming.",
            })

    # Sort descending by similarity
    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    return results, None


def analyze_complaint(
    description: str,
    citizen_category: str,
    latitude: float,
    longitude: float,
    area: str,
    existing_reports: Optional[List[Dict[str, Any]]] = None,
    model=None,
) -> Dict[str, Any]:
    """
    Orchestrate complete pipeline analysis for a complaint.
    Guarantees that errors do not discard the complaint, instead producing
    truthful 'incomplete' status with an explainable error note.
    """
    if not description or not isinstance(description, str) or not description.strip():
        return {
            "analysis_status": "incomplete",
            "analysis_error": "Description is empty or missing; manual review required.",
            "predicted_category": "Other",
            "category_evidence": [],
            "extractive_summary": "",
            "priority_score": 0,
            "priority_label": "Low",
            "priority_reasons": [{
                "factor": "Analysis Incomplete",
                "points": 0,
                "evidence": [],
                "explanation": "Automated analysis was incomplete; human officer review required."
            }],
            "needs_review": True,
            "duplicate_candidates": [],
        }

    try:
        pred_cat, cat_evidence, cat_review = categorize_text(description)
        summary = extract_summary(description, category=pred_cat)
        p_score, p_label, p_factors, p_review = calculate_priority(description)

        needs_review = cat_review or p_review

        # Duplicate checking if existing reports are supplied
        temp_report = {
            "id": None,
            "description": description,
            "citizen_category": citizen_category,
            "predicted_category": pred_cat,
            "latitude": latitude,
            "longitude": longitude,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        duplicate_candidates = []
        dup_warning = None
        if existing_reports:
            duplicate_candidates, dup_warning = find_duplicate_candidates(
                temp_report, existing_reports, model=model
            )

        return {
            "analysis_status": "complete",
            "analysis_error": dup_warning,
            "predicted_category": pred_cat,
            "category_evidence": cat_evidence,
            "extractive_summary": summary,
            "priority_score": p_score,
            "priority_label": p_label,
            "priority_reasons": p_factors,
            "needs_review": needs_review,
            "duplicate_candidates": duplicate_candidates,
        }

    except Exception as e:
        logger.error(f"Analysis pipeline error: {e}", exc_info=True)
        return {
            "analysis_status": "incomplete",
            "analysis_error": f"Analysis encountered error: {str(e)}",
            "predicted_category": "Other",
            "category_evidence": [],
            "extractive_summary": description.strip()[:140],
            "priority_score": 0,
            "priority_label": "Low",
            "priority_reasons": [{
                "factor": "Analysis Incomplete",
                "points": 0,
                "evidence": [],
                "explanation": "Automated analysis was incomplete; human officer review required."
            }],
            "needs_review": True,
            "duplicate_candidates": [],
        }
