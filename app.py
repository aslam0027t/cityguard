"""
CityGuard 🛡️: Smart Civic Issue Intelligence & Operational Triage
Mangaluru City Corporation (MCC) • Public Works & Civic Action System

A state-of-the-art 2026 civic intelligence platform providing:
1. Citizen Grievance Portal: Transparent submission with instant explainable feedback
2. Officer Intelligence Dashboard: Area clustering, action briefs, queue triage, and duplicate resolution
3. Citizen Progress Tracker: Token-based lookup with public audit timeline
"""

import json
from datetime import datetime, timezone
import pandas as pd
import streamlit as st

import config
import database as db
import ai_pipeline as ai
import seed_data
import supabase_client

# -------------------------------------------------------------
# 1. PAGE CONFIGURATION & 2026 DESIGN SYSTEM
# -------------------------------------------------------------
st.set_page_config(
    page_title="CityGuard 🛡️ | Mangaluru Civic Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Premium 2026 Design System: Glassmorphism, Micro-interactions & Vibrant Aesthetics
st.markdown(
    """
    <style>
    /* Google Fonts: Plus Jakarta Sans & Outfit & JetBrains Mono */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    :root {
        --primary-gradient: linear-gradient(135deg, #0ea5e9 0%, #2563eb 50%, #4f46e5 100%);
        --accent-glow: rgba(37, 99, 235, 0.25);
        --card-bg: rgba(255, 255, 255, 0.88);
        --card-border: rgba(226, 232, 240, 0.8);
        --text-heading: #0f172a;
        --text-body: #334155;
        --text-muted: #64748b;
        --mcc-saffron: #f97316;
        --mcc-green: #10b981;
    }

    /* Core typography and smooth font rendering */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        color: var(--text-body);
        -webkit-font-smoothing: antialiased;
    }

    h1, h2, h3, h4, h5 {
        font-family: 'Outfit', sans-serif !important;
        letter-spacing: -0.02em;
        color: var(--text-heading);
    }

    /* Keyframe Animations */
    @keyframes fadeInSlideUp {
        0% { opacity: 0; transform: translateY(16px); }
        100% { opacity: 1; transform: translateY(0); }
    }

    @keyframes pulseGlow {
        0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.5); }
        70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
        100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }

    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Hero Header Card with Mangaluru Emblem Accent */
    .cityguard-hero {
        background: linear-gradient(-45deg, #091a36, #0e2954, #1b3d75, #08172e);
        background-size: 300% 300%;
        animation: gradientShift 15s ease infinite, fadeInSlideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1);
        color: white;
        padding: 1.8rem 2.2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.12);
        box-shadow: 0 20px 35px -10px rgba(10, 25, 47, 0.35);
        position: relative;
        overflow: hidden;
    }

    .cityguard-hero::before {
        content: "";
        position: absolute;
        top: -50%;
        right: -10%;
        width: 320px;
        height: 320px;
        background: radial-gradient(circle, rgba(14, 165, 233, 0.22) 0%, rgba(0,0,0,0) 70%);
        border-radius: 50%;
        pointer-events: none;
    }

    .cityguard-hero h1 {
        color: #ffffff !important;
        font-size: 2.1rem;
        font-weight: 800;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }

    .cityguard-hero p {
        color: #cbd5e1;
        font-size: 0.95rem;
        margin: 0.4rem 0 0 0;
        max-width: 820px;
    }

    .cityguard-hero .mcc-tag {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: rgba(255, 255, 255, 0.12);
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(8px);
        padding: 0.25rem 0.75rem;
        border-radius: 30px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.7rem;
        color: #38bdf8;
    }

    /* Modern Glassmorphic Container Card */
    .glass-card {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        backdrop-filter: blur(16px) saturate(180%);
        border-radius: 14px;
        padding: 1.4rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 8px 24px -4px rgba(15, 23, 42, 0.04), 0 2px 6px -1px rgba(15, 23, 42, 0.02);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
        animation: fadeInSlideUp 0.5s ease;
    }

    .glass-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 16px 32px -6px rgba(37, 99, 235, 0.08);
    }

    /* Metric KPI Cards */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 1rem;
        margin-bottom: 1.5rem;
    }

    .kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        transition: all 0.25s ease;
        position: relative;
        overflow: hidden;
    }

    .kpi-card:hover {
        transform: translateY(-4px);
        border-color: #3b82f6;
        box-shadow: 0 12px 20px -6px rgba(59, 130, 246, 0.15);
    }

    .kpi-card::after {
        content: "";
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background: var(--primary-gradient);
    }

    .kpi-val {
        font-family: 'Outfit', sans-serif;
        font-size: 1.8rem;
        font-weight: 800;
        color: #0f172a;
        line-height: 1.2;
    }

    .kpi-lbl {
        font-size: 0.72rem;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-top: 0.3rem;
    }

    /* Badges & Status Chips */
    .badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.02em;
    }

    .badge-high {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        color: #b91c1c;
        border: 1px solid #f87171;
    }

    .badge-high-pulse {
        animation: pulseGlow 2s infinite;
    }

    .badge-medium {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        color: #b45309;
        border: 1px solid #fbbf24;
    }

    .badge-low {
        background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
        color: #15803d;
        border: 1px solid #86efac;
    }

    /* Action Brief Panel */
    .action-brief-box {
        background: linear-gradient(135deg, #eff6ff 0%, #e0f2fe 100%);
        border: 1px solid #93c5fd;
        border-left: 5px solid #2563eb;
        border-radius: 10px;
        padding: 1.2rem;
        color: #1e3a8a;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.05);
    }

    .action-brief-box h4 {
        color: #1e40af !important;
        margin: 0 0 0.5rem 0;
        font-size: 1.15rem;
        font-weight: 700;
    }

    /* Disclaimer & Safety Notice */
    .civic-notice {
        background: #fffbeb;
        border-left: 4px solid #f59e0b;
        color: #92400e;
        padding: 0.8rem 1.1rem;
        border-radius: 6px;
        font-size: 0.86rem;
        margin-bottom: 1.2rem;
    }

    /* WhatsApp Button Pill */
    .wa-btn {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: #25D366;
        color: white !important;
        padding: 0.5rem 1rem;
        border-radius: 30px;
        font-weight: 700;
        font-size: 0.85rem;
        text-decoration: none;
        transition: transform 0.2s, background 0.2s;
        box-shadow: 0 4px 12px rgba(37, 211, 102, 0.25);
    }

    .wa-btn:hover {
        background: #1eb956;
        transform: translateY(-2px);
    }

    /* Preset Chip Button Styling */
    div[data-testid="stHorizontalBlock"] .stButton > button {
        border-radius: 8px;
        transition: all 0.2s ease;
    }

    div[data-testid="stHorizontalBlock"] .stButton > button:hover {
        border-color: #2563eb;
        color: #2563eb;
        transform: translateY(-1px);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------
# 2. SYSTEM INITIALIZATION & CACHING
# -------------------------------------------------------------
db.init_db()

@st.cache_resource(show_spinner=False)
def load_cached_model():
    """Load and cache local SentenceTransformer model instance safely."""
    return ai.get_embedding_model(config.DEFAULT_EMBEDDING_MODEL)


# -------------------------------------------------------------
# 3. SIDEBAR NAVIGATION & SYSTEM SETTINGS
# -------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:0.2rem;">
            <div style="font-size:2rem;">🛡️</div>
            <div>
                <div style="font-family:'Outfit', sans-serif; font-size:1.35rem; font-weight:800; color:#0f172a; line-height:1.1;">CityGuard</div>
                <div style="font-size:0.75rem; color:#0284c7; font-weight:700; letter-spacing:0.02em;">MANGALURU CITY CORPORATION</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    nav_selection = st.radio(
        "Navigation",
        ["Report an issue", "Officer dashboard", "Track my report"],
        index=0,
    )

    st.markdown("---")
    st.markdown("##### 📍 Mangaluru Civic Desk")
    st.caption("Empowering MCC Ward Officers & Citizens across Karnataka with explainable, prioritized action.")

    # WhatsApp Quick Helpline Link
    st.markdown(
        """
        <div style="margin: 0.6rem 0 1rem 0;">
            <a href="https://wa.me/918242220306?text=Hello%20CityGuard%20Mangaluru%20Helpdesk%2C%20I%20have%20a%20civic%20query" target="_blank" class="wa-btn">
                <span>💬 WhatsApp Civic Helpdesk</span>
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("##### ⚙️ Demonstration Controls")

    # Seed Data Button
    if st.button("🌱 Load Mangaluru Demo Data (40 Reports)"):
        with st.spinner("Seeding authentic Mangalore complaints..."):
            count = seed_data.seed_database(force_reseed=False)
            if count > 0:
                st.success(f"Added {count} Mangaluru civic records.")
                st.rerun()
            else:
                st.info("Demo data already loaded (40 Mangaluru records present).")

    # Safe Confirmed Reset
    with st.expander("⚠️ Database Reset"):
        st.write("Reset SQLite database to empty state for testing clean submissions.")
        confirm_reset = st.checkbox("Confirm database reset", key="chk_confirm_reset")
        if st.button("Execute Reset", type="primary"):
            if confirm_reset:
                db.reset_database(confirm=True)
                st.success("Database has been reset.")
                st.rerun()
            else:
                st.warning("Please check the confirmation box first.")

    # Supabase Cloud Sync Controls
    with st.expander("☁️ Supabase Cloud Sync"):
        if supabase_client.is_supabase_configured():
            st.success("🟢 Connected to Supabase")
            if st.button("Test Supabase Connection"):
                ok, msg = supabase_client.test_supabase_connection()
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
            if st.button("Sync SQLite Reports to Supabase"):
                with st.spinner("Synchronizing to Supabase..."):
                    ok, msg, count = supabase_client.sync_sqlite_to_supabase()
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
        else:
            st.caption("Active Backend: Local SQLite (`data/civicaction.db`)")
            st.info("💡 To connect Supabase:\n1. Open `.env`\n2. Set `SUPABASE_URL` & `SUPABASE_KEY`\n3. Execute `supabase_schema.sql` in your Supabase SQL Editor.")

    st.markdown("---")
    st.caption("CityGuard v2.0 • Mangalore City Corporation Prototype")


# =============================================================
# SCREEN 1: REPORT AN ISSUE (CITIZEN VIEW)
# =============================================================
if nav_selection == "Report an issue":
    st.markdown(
        """
        <div class="cityguard-hero">
            <div class="mcc-tag">🏛️ Mangaluru City Corporation (MCC) • Public Action Portal</div>
            <h1>Report a Civic Issue</h1>
            <p>Your grievance is instantly analyzed with transparent AI categorization, explainable priority scoring, and semantic duplicate detection across Mangaluru's municipal wards.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    form_col, preset_col = st.columns([1.5, 1], gap="large")

    # Initialize session state for pre-filling form from presets
    if "form_desc" not in st.session_state:
        st.session_state.form_desc = ""
    if "form_cat" not in st.session_state:
        st.session_state.form_cat = config.CATEGORIES[0]
    if "form_area" not in st.session_state:
        st.session_state.form_area = list(config.DEMO_AREAS.keys())[0]
    if "form_lat" not in st.session_state:
        st.session_state.form_lat = config.DEMO_AREAS[st.session_state.form_area]["lat"]
    if "form_lon" not in st.session_state:
        st.session_state.form_lon = config.DEMO_AREAS[st.session_state.form_area]["lon"]

    with preset_col:
        st.markdown(
            """
            <div class="glass-card">
                <h4 style="margin:0 0 0.4rem 0;">📍 Mangaluru City Landmarks</h4>
                <p style="font-size:0.85rem; color:#64748b; margin-bottom:0.8rem;">Click any landmark to auto-fill verified GPS coordinates:</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for p in config.SAMPLE_COORDINATES:
            if st.button(f"📌 {p['label']} ({p['area']})", key=f"btn_p_{p['label']}", use_container_width=True):
                st.session_state.form_area = p["area"]
                st.session_state.form_lat = p["lat"]
                st.session_state.form_lon = p["lon"]
                if "Market" in p["label"]:
                    st.session_state.form_desc = "Massive open pothole in the asphalt near Hampankatta Central Market road. Vehicles are swerving into oncoming traffic."
                    st.session_state.form_cat = "Road damage"
                elif "School" in p["label"]:
                    st.session_state.form_desc = "Asphalt collapsed forming a deep sinkhole right outside the school gate. Two school children nearly fell in this morning. Immediate danger!"
                    st.session_state.form_cat = "Road damage"
                elif "Hospital" in p["label"]:
                    st.session_state.form_desc = "Uncollected medical waste and rotting organic garbage dumped outside hospital emergency gate. Serious health hazard."
                    st.session_state.form_cat = "Waste"
                elif "Terminal" in p["label"]:
                    st.session_state.form_desc = "Main water pipeline burst near highway turn shooting drinking water 10 feet into the air. Clean water wasted."
                    st.session_state.form_cat = "Water supply"
                elif "Bus Stand" in p["label"]:
                    st.session_state.form_desc = "Drainage culvert overflowing with black sewer water onto KSRTC bus stand passenger walkway."
                    st.session_state.form_cat = "Drainage / waterlogging"
                st.rerun()

    with form_col:
        with st.form("citizen_complaint_form"):
            selected_cat = st.selectbox(
                "Category (What type of issue is this?)",
                config.CATEGORIES,
                index=config.CATEGORIES.index(st.session_state.form_cat) if st.session_state.form_cat in config.CATEGORIES else 0,
            )

            complaint_text = st.text_area(
                "Describe the issue in detail",
                value=st.session_state.form_desc,
                height=130,
                placeholder="e.g. Deep crater in the road right in front of the school gate. Two children nearly fell in this morning. Immediate hazard!",
                help="Provide exact landmarks, safety hazards, and disruption details.",
            )

            c_area, c_lat, c_lon = st.columns(3)
            with c_area:
                selected_area = st.selectbox(
                    "Mangaluru Ward / Area",
                    list(config.DEMO_AREAS.keys()),
                    index=list(config.DEMO_AREAS.keys()).index(st.session_state.form_area) if st.session_state.form_area in config.DEMO_AREAS else 0,
                )
            with c_lat:
                input_lat = st.number_input("Latitude", value=float(st.session_state.form_lat), format="%.4f")
            with c_lon:
                input_lon = st.number_input("Longitude", value=float(st.session_state.form_lon), format="%.4f")

            submit_btn = st.form_submit_button("🚀 Submit Complaint to CityGuard", type="primary", use_container_width=True)

        if submit_btn:
            # Inline Validation
            clean_text = complaint_text.strip()
            if len(clean_text) < config.MIN_DESCRIPTION_LENGTH:
                st.error(f"Description is too short. Please provide at least {config.MIN_DESCRIPTION_LENGTH} characters of detail.")
            elif len(clean_text) > config.MAX_DESCRIPTION_LENGTH:
                st.error(f"Description exceeds maximum allowed limit of {config.MAX_DESCRIPTION_LENGTH} characters.")
            else:
                with st.spinner("Analyzing complaint and checking duplicate records in Mangaluru..."):
                    existing_reps = db.get_all_reports()
                    model = load_cached_model()

                    # Run AI Pipeline
                    analysis = ai.analyze_complaint(
                        description=clean_text,
                        citizen_category=selected_cat,
                        latitude=input_lat,
                        longitude=input_lon,
                        area=selected_area,
                        existing_reports=existing_reps,
                        model=model,
                    )

                    # Generate Tracking Token & Persist
                    token = db.generate_tracking_token()
                    report_payload = {
                        "tracking_token": token,
                        "description": clean_text,
                        "citizen_category": selected_cat,
                        "predicted_category": analysis["predicted_category"],
                        "category_evidence": analysis["category_evidence"],
                        "extractive_summary": analysis["extractive_summary"],
                        "latitude": input_lat,
                        "longitude": input_lon,
                        "area": selected_area,
                        "priority_score": analysis["priority_score"],
                        "priority_label": analysis["priority_label"],
                        "priority_reasons": analysis["priority_reasons"],
                        "needs_review": analysis["needs_review"],
                        "analysis_status": analysis["analysis_status"],
                        "analysis_error": analysis["analysis_error"],
                        "workflow_status": "Submitted",
                        "assigned_department": None,
                    }

                    new_report_id = db.insert_report(report_payload)

                    # Record duplicate candidate relationships if surfaced
                    for dup in analysis.get("duplicate_candidates", []):
                        db.record_duplicate_candidate(
                            source_id=new_report_id,
                            candidate_id=dup["candidate_id"],
                            similarity=dup["similarity_score"],
                            distance_meters=dup["distance_meters"],
                            review_state="suggested",
                        )

                # Instant Feedback Receipt Card
                st.markdown(
                    f"""
                    <div style="background:#ecfdf5; border:1px solid #6ee7b7; border-radius:12px; padding:1.5rem; margin-top:1.5rem; animation:fadeInSlideUp 0.5s ease;">
                        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #d1fae5; padding-bottom:0.8rem; margin-bottom:1rem;">
                            <div>
                                <div style="font-size:0.75rem; color:#047857; font-weight:700; text-transform:uppercase;">Official Tracking Token</div>
                                <div style="font-family:'JetBrains Mono', monospace; font-size:1.6rem; font-weight:800; color:#065f46;">{token}</div>
                            </div>
                            <div style="background:#059669; color:white; padding:0.35rem 1rem; border-radius:20px; font-weight:700; font-size:0.85rem;">
                                Submitted & Logged
                            </div>
                        </div>
                        <p style="margin:0 0 0.8rem 0; font-size:0.95rem; color:#064e3b;">
                            <strong>✅ Your complaint has been submitted to Mangalore City Corporation.</strong> Keep this token to track progress in the Citizen Tracker.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Explainability Breakdown
                with st.expander("🔍 View Transparent AI Analysis Receipt", expanded=True):
                    r_c1, r_c2, r_c3 = st.columns(3)
                    with r_c1:
                        st.markdown("**Rule-Based Category**")
                        st.write(f"`{analysis['predicted_category']}`")
                        ev_list = json.loads(analysis["category_evidence"])
                        if ev_list:
                            st.caption(f"Matched keyword tokens: {', '.join(ev_list)}")
                        else:
                            st.caption("No dominant keywords found; flagged for officer review.")

                    with r_c2:
                        st.markdown("**Salient Summary**")
                        st.write(f'"{analysis["extractive_summary"]}"')

                    with r_c3:
                        st.markdown("**Explainable Priority**")
                        p_label = analysis["priority_label"]
                        p_score = analysis["priority_score"]
                        badge_style = "badge-high badge-high-pulse" if p_label == "High" else ("badge-medium" if p_label == "Medium" else "badge-low")
                        st.markdown(f"<span class='badge-pill {badge_style}'>{p_label} ({p_score}/100)</span>", unsafe_allow_html=True)

                    # Factor breakdown
                    reasons = json.loads(analysis["priority_reasons"])
                    if reasons:
                        st.markdown("**Priority Point Justifications:**")
                        for r in reasons:
                            st.write(f"- **{r.get('factor')}** (+{r.get('points')} pts): {r.get('explanation')}")

                    # Duplicate Alert (if any nearby candidates detected)
                    duplicates = analysis.get("duplicate_candidates", [])
                    if duplicates:
                        st.markdown("---")
                        st.markdown(f"**🔗 Potential Semantic Duplicate Warning ({len(duplicates)} nearby reports found):**")
                        for d in duplicates:
                            st.info(
                                f"• Report #{d['candidate_id']} ({d['candidate_token']}) located **{d['distance_meters']}m** away — "
                                f"Semantic similarity: **{d['similarity_score']:.2f}**\n\n"
                                f"*{d['candidate_summary']}*"
                            )
                        st.caption("Note: Your complaint remains an independent submission. Ward officers will review duplicate links during dispatch.")

    # Citizen FAQ Section
    st.markdown("---")
    st.markdown("### ❓ Frequently Asked Questions")
    with st.expander("How does CityGuard assign priority to my complaint?"):
        st.write(
            "CityGuard uses a transparent, explainable additive scoring policy:\n"
            "- **+60 points** for immediate physical hazards (e.g. deep sinkholes, exposed live wires, structural collapses).\n"
            "- **+20 points** for sensitive community settings (e.g. schools, hospitals, childcare centers).\n"
            "- **+20 points** for critical access disruption (e.g. flooded road, impassable street, total water cut).\n"
            "Reports scoring 60–100 are ranked **High**, 30–59 are **Medium**, and 0–29 are **Low**."
        )
    with st.expander("Does CityGuard delete or merge duplicate complaints?"):
        st.write(
            "No! Unlike conventional systems, CityGuard retains the independent identity and tracking token of every citizen's submission. "
            "When duplicate issues are detected, they are linked as related items so field crews can coordinate a single dispatch without erasing citizen records."
        )
    with st.expander("Is my personal data visible on the public tracker?"):
        st.write(
            "No. CityGuard guarantees strict citizen privacy. Only public municipal service notes, department assignments, and workflow statuses are visible on the public tracker. "
            "Internal officer notes, budget codes, and citizen contact information are strictly excluded."
        )


# =============================================================
# SCREEN 2: OFFICER DASHBOARD (TRIAGE & OPERATIONS)
# =============================================================
elif nav_selection == "Officer dashboard":
    st.markdown(
        """
        <div class="cityguard-hero">
            <div class="mcc-tag">🛠️ Mangaluru City Corporation (MCC) • Municipal Operations Console</div>
            <h1>CityGuard Officer Dashboard</h1>
            <p>Actionable municipal intelligence for Mangaluru ward engineers, field superintendents, and department coordinators.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    all_reports = db.get_all_reports()

    if not all_reports:
        st.info("No complaints found in the database. Use '🌱 Load Mangaluru Demo Data (40 Reports)' in the sidebar to populate realistic complaints.")
    else:
        df = pd.DataFrame(all_reports)

        # Compute effective priority (respecting officer overrides)
        df["effective_priority"] = df.apply(
            lambda r: r["priority_override_score"] if pd.notnull(r["priority_override_score"]) else r["priority_score"],
            axis=1,
        )
        df["effective_label"] = df.apply(
            lambda r: r["priority_override_label"] if pd.notnull(r["priority_override_label"]) and r["priority_override_label"] else r["priority_label"],
            axis=1,
        )

        # -----------------------------------------------------
        # 1. KPI METRIC CARDS
        # -----------------------------------------------------
        total_reports = len(df)
        open_reports = len(df[df["workflow_status"] != "Resolved"])
        high_priority_open = len(df[(df["effective_priority"] >= 60) & (df["workflow_status"] != "Resolved")])
        unassigned_reports = len(df[(df["assigned_department"].isna()) | (df["assigned_department"] == "")])
        resolved_reports = len(df[df["workflow_status"] == "Resolved"])
        needs_review_count = len(df[df["needs_review"] == 1])

        st.markdown(
            f"""
            <div class="kpi-container">
                <div class="kpi-card">
                    <div class="kpi-val">{total_reports}</div>
                    <div class="kpi-lbl">Total Reports</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-val" style="color:#2563eb;">{open_reports}</div>
                    <div class="kpi-lbl">Active Open</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-val" style="color:#dc2626;">{high_priority_open}</div>
                    <div class="kpi-lbl">High-Priority Open</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-val" style="color:#d97706;">{unassigned_reports}</div>
                    <div class="kpi-lbl">Unassigned</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-val" style="color:#16a34a;">{resolved_reports}</div>
                    <div class="kpi-lbl">Resolved</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-val" style="color:#7c3aed;">{needs_review_count}</div>
                    <div class="kpi-lbl">Needs Review</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # -----------------------------------------------------
        # 2. AREA-LEVEL GROUPING & ACTION BRIEF
        # -----------------------------------------------------
        st.markdown("### 📊 Area-Level Grouping & Action Brief")

        area_selected = st.selectbox(
            "Select Mangaluru Ward to Inspect",
            ["All Wards"] + list(config.DEMO_AREAS.keys()),
            index=0,
        )

        active_df = df[df["workflow_status"] != "Resolved"]
        if area_selected != "All Wards":
            area_active_df = active_df[active_df["area"] == area_selected]
        else:
            area_active_df = active_df

        # Calculate Confirmed Unique Groups vs Raw Submissions
        area_sub_count = len(area_active_df)
        area_cats = area_active_df["predicted_category"].value_counts()
        top_cat = area_cats.index[0] if not area_cats.empty else "None"
        top_cat_count = area_cats.iloc[0] if not area_cats.empty else 0
        area_high_p = len(area_active_df[area_active_df["effective_priority"] >= 60])

        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT source_report_id, candidate_report_id FROM duplicate_relationships WHERE review_state = 'confirmed';")
            pairs = cursor.fetchall()
            adj = {}
            for p in pairs:
                s, c = p[0], p[1]
                adj.setdefault(s, set()).add(c)
                adj.setdefault(c, set()).add(s)

            visited = set()
            clusters = 0
            for r_id in area_active_df["id"]:
                if r_id not in visited:
                    clusters += 1
                    queue = [r_id]
                    visited.add(r_id)
                    while queue:
                        curr = queue.pop(0)
                        for neighbor in adj.get(curr, []):
                            if neighbor in area_active_df["id"].values and neighbor not in visited:
                                visited.add(neighbor)
                                queue.append(neighbor)

        confirmed_unique_issues = clusters

        # Generate Action Brief
        dept_recs = {
            "Road damage": "Roads & Civil Works Division",
            "Waste": "Sanitation & Solid Waste Management",
            "Drainage / waterlogging": "Drainage & Stormwater Maintenance",
            "Streetlights / electrical": "MESCOM / City Electrical Maintenance",
            "Water supply": "Municipal Water Services & Pipe Network",
            "Other": "General Municipal Grievance Cell",
        }
        recommended_dept = dept_recs.get(top_cat, "General Municipal Cell")

        st.markdown(
            f"""
            <div class="action-brief-box">
                <h4>📋 Operational Brief: {area_selected}</h4>
                <div style="font-size:0.95rem; line-height:1.6;">
                    • <strong>Current Workload:</strong> {area_sub_count} raw submissions representing <strong>{confirmed_unique_issues} unique physical problem clusters</strong>.<br>
                    • <strong>Primary Complaint Pattern:</strong> <code>{top_cat}</code> ({top_cat_count} active reports).<br>
                    • <strong>High-Risk Safety Alerts:</strong> <span style="color:#b91c1c; font-weight:700;">{area_high_p} severe issues</span> require immediate site inspection.<br>
                    • <strong>Recommended Response:</strong> Deploy <strong>{recommended_dept}</strong> for combined route inspection.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # -----------------------------------------------------
        # 3. INTERACTIVE QUEUE & MAP
        # -----------------------------------------------------
        m_col1, m_col2 = st.columns([1, 1], gap="medium")

        with m_col1:
            st.markdown("##### 🗺️ Geographic Distribution (Mangaluru)")
            map_data = area_active_df[["latitude", "longitude"]].copy()
            if not map_data.empty:
                st.map(map_data, zoom=12, use_container_width=True)
            else:
                st.info("No active complaints to display on map.")

        with m_col2:
            st.markdown("##### ⚡ Quick Queue Filter")
            filter_cat = st.multiselect("Filter Category", config.CATEGORIES, default=[])
            filter_prio = st.multiselect("Filter Priority", ["High", "Medium", "Low"], default=[])

            filtered_df = area_active_df
            if filter_cat:
                filtered_df = filtered_df[filtered_df["predicted_category"].isin(filter_cat)]
            if filter_prio:
                filtered_df = filtered_df[filtered_df["effective_label"].isin(filter_prio)]

            st.caption(f"Showing **{len(filtered_df)}** prioritized reports in queue.")

        # Data Table Sorted by Effective Priority Descending, then Created At Ascending
        st.markdown("##### Filtered Reports Queue")
        display_columns = [
            "id", "tracking_token", "area", "predicted_category",
            "effective_priority", "effective_label", "workflow_status",
            "assigned_department", "needs_review", "created_at"
        ]
        st.dataframe(filtered_df[display_columns], use_container_width=True, height=260)

        # -----------------------------------------------------
        # 4. REPORT DETAIL & OFFICER TRIAGE DRAWER
        # -----------------------------------------------------
        st.markdown("---")
        st.markdown("### 🛠️ Officer Triage & Review Console")

        available_ids = filtered_df["id"].tolist() if not filtered_df.empty else df["id"].tolist()
        selected_report_id = st.selectbox(
            "Select Report to Inspect and Update",
            available_ids,
            format_func=lambda x: f"Report #{x} — [{df[df['id']==x]['tracking_token'].values[0]}] ({df[df['id']==x]['area'].values[0]}) - {df[df['id']==x]['extractive_summary'].values[0][:60]}...",
        )

        if selected_report_id:
            rep = db.get_report_by_id(selected_report_id)
            if rep:
                triage_col1, triage_col2 = st.columns([1, 1], gap="large")

                with triage_col1:
                    st.markdown("##### 📄 Complaint Information")
                    st.write(f"**Tracking Token:** `{rep['tracking_token']}`")
                    st.write(f"**Submitted At (UTC):** {rep['created_at']}")
                    st.write(f"**Ward / Area:** {rep['area']} ({rep['latitude']:.4f}, {rep['longitude']:.4f})")
                    st.write(f"**Citizen Category:** `{rep['citizen_category']}`")
                    st.write(f"**Predicted Category:** `{rep['predicted_category']}` (Rule-based)")

                    try:
                        ev_list = json.loads(rep["category_evidence"])
                        if ev_list:
                            st.caption(f"Category Evidence Tokens: {', '.join(ev_list)}")
                    except Exception:
                        pass

                    st.write(f"**Extractive Summary:** {rep['extractive_summary']}")
                    st.text_area("Full Description", rep["description"], height=90, disabled=True)

                    # Priority Breakdown
                    st.markdown("##### ⚖️ Priority Breakdown")
                    eff_score = rep["priority_override_score"] if rep["priority_override_score"] is not None else rep["priority_score"]
                    eff_label = rep["priority_override_label"] or rep["priority_label"]
                    badge_style = "badge-high badge-high-pulse" if eff_label == "High" else ("badge-medium" if eff_label == "Medium" else "badge-low")
                    st.markdown(
                        f"Current Priority: <span class='badge-pill {badge_style}'>{eff_label} ({eff_score}/100)</span>",
                        unsafe_allow_html=True,
                    )

                    if rep["priority_override_reason"]:
                        st.warning(f"⚠️ Overridden by Officer: {rep['priority_override_reason']}")
                    else:
                        try:
                            reasons = json.loads(rep["priority_reasons"])
                            for r in reasons:
                                st.write(f"- **{r.get('factor')}** (+{r.get('points')} pts): {r.get('explanation')}")
                        except Exception:
                            pass

                    # Officer Priority Override Expander
                    with st.expander("✏️ Override Priority (Requires Audit Reason)"):
                        with st.form(f"form_override_prio_{rep['id']}"):
                            override_label = st.selectbox("New Priority Label", ["High", "Medium", "Low"])
                            override_score = st.slider("New Score", 0, 100, 75 if override_label=="High" else (45 if override_label=="Medium" else 20))
                            override_reason = st.text_input("Mandatory Reason for Override", placeholder="e.g. Verified high hazard during MCC site inspection")
                            btn_override = st.form_submit_button("Apply Override")

                        if btn_override:
                            if not override_reason.strip():
                                st.error("A reason is mandatory for priority override.")
                            else:
                                success, msg = db.override_priority(rep["id"], override_score, override_label, override_reason)
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)

                with triage_col2:
                    st.markdown("##### 🔄 Workflow & Department Assignment")
                    st.write(f"**Current Status:** `{rep['workflow_status']}`")
                    st.write(f"**Assigned Department:** `{rep['assigned_department'] or 'Unassigned'}`")

                    # Workflow Update Form
                    with st.form(f"form_workflow_update_{rep['id']}"):
                        new_dept = st.selectbox(
                            "Assign Department",
                            config.DEPARTMENTS,
                            index=config.DEPARTMENTS.index(rep["assigned_department"]) if rep["assigned_department"] in config.DEPARTMENTS else 0,
                        )

                        current_stat = rep["workflow_status"]
                        valid_next = config.ALLOWED_TRANSITIONS.get(current_stat, [current_stat])
                        status_options = list(dict.fromkeys([current_stat] + valid_next))

                        new_status = st.selectbox("Update Status", status_options, index=0)
                        workflow_note = st.text_area("Progress / Resolution Note", placeholder="Mandatory if resolving issue...")
                        is_public_note = st.checkbox("Make note visible to citizen", value=True)

                        btn_update_workflow = st.form_submit_button("Update Workflow", type="primary")

                    if btn_update_workflow:
                        success, msg = db.update_report_workflow(
                            report_id=rep["id"],
                            new_status=new_status,
                            department=new_dept,
                            note=workflow_note,
                            is_public=is_public_note,
                        )
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

                    # Duplicate Candidates Review
                    st.markdown("##### 🔗 Semantic Duplicate Review")
                    duplicates = db.get_duplicates_for_report(rep["id"])
                    if duplicates:
                        for d in duplicates:
                            with st.container():
                                st.write(
                                    f"• **Report #{d['candidate_report_id']}** (`{d['tracking_token']}`) "
                                    f"— State: `{d['review_state']}` | Sim: **{d['similarity_score']:.2f}** | Dist: **{d['distance_meters']}m**"
                                )
                                st.caption(f"Summary: {d['extractive_summary']}")

                                btn_c1, btn_c2 = st.columns(2)
                                with btn_c1:
                                    if st.button("Confirm Link", key=f"btn_confirm_dup_{d['relationship_id']}"):
                                        db.update_duplicate_review_state(d["relationship_id"], "confirmed")
                                        st.success("Duplicate confirmed and linked.")
                                        st.rerun()
                                Danger_btn = btn_c2
                                with Danger_btn:
                                    if st.button("Reject Suggestion", key=f"btn_reject_dup_{d['relationship_id']}"):
                                        db.update_duplicate_review_state(d["relationship_id"], "rejected")
                                        st.info("Suggestion rejected.")
                                        st.rerun()
                    else:
                        st.caption("No duplicate candidates recorded for this report.")

                    # Audit History Timeline
                    with st.expander("📜 View Complete Event Audit Trail"):
                        events = db.get_report_events(rep["id"], public_only=False)
                        for ev in events:
                            v_badge = "🌐 Public" if ev["is_public"] else "🔒 Internal"
                            st.write(f"• **{ev['created_at'][:16]} UTC** — [{v_badge}] `{ev['event_type']}`: {ev['note']}")


# =============================================================
# SCREEN 3: TRACK MY REPORT (CITIZEN VIEW)
# =============================================================
elif nav_selection == "Track my report":
    st.markdown(
        """
        <div class="cityguard-hero">
            <div class="mcc-tag">🔍 Mangaluru City Corporation (MCC) • Citizen Progress Tracking</div>
            <h1>Track Your Report</h1>
            <p>Enter your 16-character tracking token to view real-time municipal action, field team dispatches, and public resolution milestones.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    t_col1, t_col2 = st.columns([2, 1])
    with t_col1:
        query_token = st.text_input(
            "Enter Tracking Token",
            placeholder="e.g. CIVIC-A1B2-C3D4",
            help="Your tracking token was provided when you submitted your complaint.",
        ).strip().upper()

    with t_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        search_btn = st.button("🔎 Check Status", type="primary", use_container_width=True)

    if query_token or search_btn:
        if not query_token:
            st.warning("Please enter a valid tracking token.")
        else:
            report = db.get_report_by_token(query_token)

            if not report:
                st.error(f"No grievance found matching token `{query_token}`. Please double-check your token.")
            else:
                status = report["workflow_status"]
                status_colors = {
                    "Submitted": "#0284c7",
                    "Reviewed": "#3b82f6",
                    "Assigned": "#d97706",
                    "In progress": "#7c3aed",
                    "Resolved": "#16a34a",
                }
                color = status_colors.get(status, "#64748b")

                st.markdown(
                    f"""
                    <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:12px; padding:1.8rem; margin-bottom:1.5rem; box-shadow:0 8px 24px -4px rgba(0,0,0,0.06); animation:fadeInSlideUp 0.5s ease;">
                        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #f1f5f9; padding-bottom:1rem; margin-bottom:1.2rem;">
                            <div>
                                <span style="font-size:0.75rem; color:#64748b; font-weight:700; text-transform:uppercase; letter-spacing:0.04em;">Official Tracking Token</span>
                                <div style="font-size:1.8rem; font-weight:800; color:#0f172a; font-family:'JetBrains Mono', monospace;">{report['tracking_token']}</div>
                            </div>
                            <div style="background:{color}; color:white; padding:0.45rem 1.4rem; border-radius:24px; font-weight:700; font-size:1rem; box-shadow:0 4px 12px {color}33;">
                                {status}
                            </div>
                        </div>
                        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:1.2rem; font-size:0.92rem;">
                            <div><strong>Assigned Department:</strong><br><span style="color:#2563eb; font-weight:600;">{report['assigned_department'] or 'Pending Review'}</span></div>
                            <div><strong>Mangaluru Ward:</strong><br>{report['area']}</div>
                            <div><strong>Category:</strong><br>{report['citizen_category']}</div>
                            <div><strong>Submitted At:</strong><br>{report['created_at'][:10]} {report['created_at'][11:16]} UTC</div>
                        </div>
                        <div style="margin-top:1.2rem; padding:1rem; background:#f8fafc; border-radius:8px; font-size:0.92rem; border-left:4px solid #3b82f6;">
                            <strong>Summary:</strong> {report['extractive_summary']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Confirmed Related Issue Notice (if any)
                confirmed_related = db.check_has_confirmed_related(report["id"])
                if confirmed_related:
                    for cr in confirmed_related:
                        st.info(
                            f"ℹ️ **Coordinated Response Notice**: This report has been linked with confirmed related report "
                            f"`{cr['tracking_token']}`. Mangalore City Corporation field teams are coordinating a unified inspection."
                        )

                # Public Progress Timeline (Chronological, strictly filtering out internal notes)
                st.markdown("### 📋 Public Progress Timeline")
                events = db.get_report_events(report["id"], public_only=True)

                if not events:
                    st.write("No progress events recorded yet.")
                else:
                    for idx, ev in enumerate(events):
                        icon = "✅" if ev["event_type"] == "created" else ("🔧" if ev["event_type"] == "assigned" else ("📢" if ev["event_type"] == "status_change" else "📝"))
                        st.markdown(
                            f"""
                            <div style="border-left: 3px solid #3b82f6; padding-left: 1.2rem; margin-left: 0.6rem; margin-bottom: 1.2rem;">
                                <div style="font-size:0.8rem; color:#64748b; font-weight:600;">{ev['created_at'][:10]} {ev['created_at'][11:16]} UTC</div>
                                <div style="font-weight:700; color:#1e293b; margin:0.15rem 0; font-size:0.95rem;">{icon} {ev['event_type'].replace('_', ' ').title()}</div>
                                <div style="color:#475569; font-size:0.92rem; background:#f8fafc; padding:0.6rem 0.9rem; border-radius:6px; margin-top:0.3rem;">{ev['note']}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                st.caption("🔒 Privacy Guarantee: Only verified public municipal progress notes are displayed. Internal officer deliberations are excluded.")
