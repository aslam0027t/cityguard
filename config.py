"""
CivicAction Configuration Module
Defines system constants, predefined demo areas, categories,
departments, workflow statuses, and experimental prototype parameters.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(DATA_DIR / "civicaction.db")))

# Supabase / Cloud Configuration
DB_BACKEND = os.getenv("DB_BACKEND", "sqlite").lower()
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL", "")

# Embedding Model
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Citizen / System Categories
CATEGORIES = [
    "Road damage",
    "Waste",
    "Drainage / waterlogging",
    "Streetlights / electrical",
    "Water supply",
    "Other",
]

# Municipal Departments
DEPARTMENTS = [
    "Roads",
    "Sanitation",
    "Drainage",
    "Electrical maintenance",
    "Water services",
]

# Permitted Workflow Statuses
WORKFLOW_STATUSES = [
    "Submitted",
    "Reviewed",
    "Assigned",
    "In progress",
    "Resolved",
]

# Valid Status Transitions
# Rule: A department must be assigned before entering 'Assigned' or 'In progress'
# Rule: A public resolution note is required before entering 'Resolved'
ALLOWED_TRANSITIONS = {
    "Submitted": ["Reviewed", "Assigned"],
    "Reviewed": ["Assigned", "Submitted"],
    "Assigned": ["In progress", "Reviewed", "Resolved"],
    "In progress": ["Resolved", "Assigned"],
    "Resolved": ["In progress", "Reviewed"],
}

# Real Mangaluru (Mangalore City, Karnataka) Municipal Areas with Anchor Coordinates
DEMO_AREAS = {
    "Hampankatta": {"lat": 12.8703, "lon": 74.8427},
    "Kadri Hills": {"lat": 12.8943, "lon": 74.8617},
    "Lalbagh - Ladyhill": {"lat": 12.8872, "lon": 74.8398},
    "Kankanady - Pumpwell": {"lat": 12.8668, "lon": 74.8624},
    "Surathkal - Kulai": {"lat": 13.0108, "lon": 74.7943},
}

# Sample Presets for Interactive Demo Form Filling (Mangalore City Landmarks)
SAMPLE_COORDINATES = [
    {"label": "Hampankatta Market Road", "area": "Hampankatta", "lat": 12.8705, "lon": 74.8429},
    {"label": "Kadri North School Gate", "area": "Kadri Hills", "lat": 12.8945, "lon": 74.8619},
    {"label": "Lalbagh MCC Head Office", "area": "Lalbagh - Ladyhill", "lat": 12.8874, "lon": 74.8400},
    {"label": "Kankanady Father Muller Hospital Junction", "area": "Kankanady - Pumpwell", "lat": 12.8670, "lon": 74.8626},
    {"label": "Surathkal Bus Terminal", "area": "Surathkal - Kulai", "lat": 13.0110, "lon": 74.7945},
    {"label": "Bejai KSRTC Bus Stand", "area": "Lalbagh - Ladyhill", "lat": 12.8841, "lon": 74.8510},
]

# Experimental Duplicate Detection Defaults
# Note: Demo parameters, not validated municipal standards.
DUPLICATE_SIMILARITY_THRESHOLD = 0.80  # Cosine similarity >= 0.80
DUPLICATE_MAX_DISTANCE_METERS = 150.0  # Within 150 meters
DUPLICATE_TIME_WINDOW_DAYS = 7         # Within 7 days

# Explainable Priority Demonstration Rules
PRIORITY_WEIGHTS = {
    "immediate_hazard": 60,       # Explicit immediate physical danger
    "sensitive_setting": 20,      # Explicit mention of school, hospital, clinic, etc.
    "blocked_access": 20,         # Explicit impassable road, severe flooding, total disruption
}
MAX_PRIORITY_SCORE = 100

PRIORITY_THRESHOLDS = {
    "High": (60, 100),
    "Medium": (30, 59),
    "Low": (0, 29),
}

# Text Constraints
MIN_DESCRIPTION_LENGTH = 10
MAX_DESCRIPTION_LENGTH = 2000
