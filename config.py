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

# Predefined Fictional Demo Areas with Anchor Coordinates
DEMO_AREAS = {
    "Oakridge Heights": {"lat": 12.9716, "lon": 77.5946},
    "Maple Riverside": {"lat": 12.9820, "lon": 77.6050},
    "Harbor Ward": {"lat": 12.9650, "lon": 77.6120},
    "Pineview Central": {"lat": 12.9780, "lon": 77.5850},
    "Elmwood Industrial": {"lat": 12.9550, "lon": 77.5750},
}

# Sample Presets for Interactive Demo Form Filling
SAMPLE_COORDINATES = [
    {"label": "Oakridge Central Market", "area": "Oakridge Heights", "lat": 12.9718, "lon": 77.5948},
    {"label": "Oakridge North School Gate", "area": "Oakridge Heights", "lat": 12.9725, "lon": 77.5952},
    {"label": "Maple Riverside Bridge", "area": "Maple Riverside", "lat": 12.9822, "lon": 77.6054},
    {"label": "Harbor Ward Primary Hospital", "area": "Harbor Ward", "lat": 12.9655, "lon": 77.6125},
    {"label": "Pineview Junction", "area": "Pineview Central", "lat": 12.9784, "lon": 77.5855},
    {"label": "Elmwood Cargo Terminal", "area": "Elmwood Industrial", "lat": 12.9555, "lon": 77.5755},
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
