"""
CITYGUARD 🛡️: Smart Civic Issue Reporting and Management Platform
Organization: Mangaluru City Corporation (MCC)
Tagline: "Building a Cleaner, Safer and Smarter Mangaluru."

A premium, enterprise-level 2026 civic-technology platform:
- Premium Dark Navy Theme (#0B1220 background, #16243A cards, #3B82F6 blue, #22C55E green)
- Brand Identity: Professional shield + location-pin logo
- Complete citizen reporting, tracking, real-time analytics, and officer triage workflows
"""

import os
import json
import base64
import textwrap
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import streamlit as st

import config
import database as db
import ai_pipeline as ai
import seed_data
import supabase_client

# -------------------------------------------------------------
# 1. PAGE SETUP & ENTERPRISE DARK NAVY DESIGN SYSTEM
# -------------------------------------------------------------
st.set_page_config(
    page_title="CITYGUARD | Mangaluru City Corporation",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

def render_html(html_str: str) -> None:
    """Safely render raw HTML elements cleanly without Markdown code-block interpretation."""
    st.html(textwrap.dedent(html_str).strip())

# Professional CITYGUARD Shield + Location-Pin SVG Logo
CITYGUARD_LOGO_SVG = (
    '<svg width="40" height="40" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">'
    '<path d="M18 3L5 8.5V17.5C5 25.5 10.5 32.5 18 34.5C25.5 32.5 31 25.5 31 17.5V8.5L18 3Z" fill="url(#shield-grad)" stroke="#3B82F6" stroke-width="1.8"/>'
    '<circle cx="18" cy="16" r="4.5" fill="#22C55E"/>'
    '<path d="M18 10C14.7 10 12 12.7 12 16C12 20.5 18 26.5 18 26.5C18 26.5 24 20.5 24 16C24 12.7 21.3 10 18 10ZM18 18.5C16.6 18.5 15.5 17.4 15.5 16C15.5 14.6 16.6 13.5 18 13.5C19.4 13.5 20.5 14.6 20.5 16C20.5 17.4 19.4 18.5 18 18.5Z" fill="#FFFFFF"/>'
    '<defs>'
    '<linearGradient id="shield-grad" x1="18" y1="3" x2="18" y2="34.5" gradientUnits="userSpaceOnUse">'
    '<stop stop-color="#1E3A8A"/>'
    '<stop offset="1" stop-color="#0F172A"/>'
    '</linearGradient>'
    '</defs>'
    '</svg>'
)

# Enterprise 2026 CSS Theme
st.markdown(
    """
    <style>
    /* Modern Inter & Outfit Typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@500;600;700;800;900&family=JetBrains+Mono:wght@400;600;700&display=swap');

    :root {
        --bg-main: #0B1220;
        --card-bg: #16243A;
        --card-border: rgba(255, 255, 255, 0.08);
        --primary-blue: #3B82F6;
        --primary-hover: #2563EB;
        --success-green: #22C55E;
        --warning-amber: #F59E0B;
        --danger-red: #EF4444;
        --text-white: #F8FAFC;
        --text-muted: #94A3B8;
        --text-dark: #64748B;
    }

    /* Top-level background override */
    .stApp {
        background-color: var(--bg-main) !important;
        color: var(--text-white) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        -webkit-font-smoothing: antialiased;
    }

    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif !important;
        letter-spacing: -0.02em !important;
        color: var(--text-white) !important;
    }

    p, span, div, label {
        color: var(--text-muted);
    }

    /* Animated Hero Card */
    @keyframes heroGradientAnimation {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    @keyframes fadeInSlide {
        from { opacity: 0; transform: translateY(14px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes pulseHighHazard {
        0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.6); }
        70% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
        100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }

    .cityguard-hero-section {
        background: linear-gradient(135deg, #0f1f38, #16243a, #0b1a2f, #1e3a8a);
        background-size: 300% 300%;
        animation: heroGradientAnimation 14s ease infinite, fadeInSlide 0.6s ease;
        border: 1px solid rgba(59, 130, 246, 0.25);
        border-radius: 16px;
        padding: 2.2rem 2.4rem;
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.6);
        position: relative;
        overflow: hidden;
    }

    .cityguard-hero-section::after {
        content: "";
        position: absolute;
        bottom: -30%;
        right: -10%;
        width: 360px;
        height: 360px;
        background: radial-gradient(circle, rgba(59, 130, 246, 0.18) 0%, rgba(0,0,0,0) 70%);
        border-radius: 50%;
        pointer-events: none;
    }

    .hero-badge-mcc {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(59, 130, 246, 0.15);
        border: 1px solid rgba(59, 130, 246, 0.35);
        color: #60a5fa !important;
        padding: 0.3rem 0.9rem;
        border-radius: 30px;
        font-size: 0.76rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.8rem;
    }

    .cityguard-hero-section h1 {
        font-size: 2.4rem !important;
        font-weight: 900 !important;
        color: #ffffff !important;
        line-height: 1.15;
        margin: 0 0 0.8rem 0;
    }

    .cityguard-hero-section p {
        font-size: 1.05rem;
        color: #cbd5e1 !important;
        line-height: 1.6;
        max-width: 820px;
        margin: 0 0 1.4rem 0;
    }

    /* Enterprise Cards */
    .enterprise-card {
        background: var(--card-bg) !important;
        border: 1px solid var(--card-border) !important;
        border-radius: 14px;
        padding: 1.4rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
        animation: fadeInSlide 0.5s ease;
    }

    .enterprise-card:hover {
        transform: translateY(-3px);
        border-color: rgba(59, 130, 246, 0.4) !important;
        box-shadow: 0 16px 32px -6px rgba(59, 130, 246, 0.12);
    }

    /* KPI Metrics in Grid */
    .kpi-stat-card {
        background: #16243A;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.2rem 1rem;
        text-align: center;
        transition: all 0.25s ease;
        position: relative;
        overflow: hidden;
    }

    .kpi-stat-card:hover {
        transform: translateY(-4px);
        border-color: #3B82F6;
        box-shadow: 0 12px 24px -6px rgba(59, 130, 246, 0.25);
    }

    .kpi-stat-card::after {
        content: "";
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background: linear-gradient(90deg, #3B82F6, #22C55E);
    }

    .kpi-number {
        font-family: 'Outfit', sans-serif;
        font-size: 2.1rem;
        font-weight: 800;
        color: #ffffff;
        line-height: 1.1;
    }

    .kpi-caption {
        font-size: 0.74rem;
        font-weight: 700;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.4rem;
    }

    /* Priority Chips */
    .chip-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.28rem 0.85rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
    }

    .chip-high {
        background: rgba(239, 68, 68, 0.15);
        color: #f87171 !important;
        border: 1px solid rgba(239, 68, 68, 0.4);
    }

    .chip-high-glow {
        animation: pulseHighHazard 2s infinite;
    }

    .chip-medium {
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24 !important;
        border: 1px solid rgba(245, 158, 11, 0.4);
    }

    .chip-low {
        background: rgba(34, 197, 94, 0.15);
        color: #4ade80 !important;
        border: 1px solid rgba(34, 197, 94, 0.4);
    }

    /* Action Brief Panel */
    .brief-panel {
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.3) 0%, rgba(22, 36, 58, 0.6) 100%);
        border: 1px solid rgba(59, 130, 246, 0.4);
        border-left: 5px solid #3B82F6;
        border-radius: 12px;
        padding: 1.4rem;
        margin-bottom: 1.5rem;
    }

    .brief-panel h4 {
        color: #60a5fa !important;
        margin: 0 0 0.6rem 0;
        font-size: 1.25rem;
    }

    /* WhatsApp Button */
    .btn-whatsapp-civic {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: #25D366;
        color: #ffffff !important;
        padding: 0.55rem 1.1rem;
        border-radius: 30px;
        font-weight: 700;
        font-size: 0.86rem;
        text-decoration: none;
        box-shadow: 0 4px 14px rgba(37, 211, 102, 0.3);
        transition: transform 0.2s, background 0.2s;
    }

    .btn-whatsapp-civic:hover {
        background: #1eb956;
        transform: translateY(-2px);
    }

    /* Form Inputs Overrides for Dark Navy Theme */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div,
    .stNumberInput > div > div > input {
        background-color: #0F172A !important;
        color: #F8FAFC !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 8px !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
    }

    /* Sidebar Background */
    section[data-testid="stSidebar"] {
        background-color: #090F1A !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }

    /* Segmented Navigation Tab Bar */
    div[role="radiogroup"] {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 0.6rem !important;
        background: #0E1726 !important;
        padding: 0.45rem 0.65rem !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        margin-bottom: 1.5rem !important;
    }
    div[role="radiogroup"] label {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        padding: 0.5rem 1.15rem !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }
    div[role="radiogroup"] label:hover {
        background: rgba(59, 130, 246, 0.15) !important;
        border-color: rgba(59, 130, 246, 0.4) !important;
    }
    div[role="radiogroup"] label[data-checked="true"],
    div[role="radiogroup"] label:has(input:checked) {
        background: #3B82F6 !important;
        border-color: #3B82F6 !important;
        box-shadow: 0 4px 14px rgba(59, 130, 246, 0.35) !important;
    }
    div[role="radiogroup"] label[data-checked="true"] div[data-testid="stMarkdownContainer"] p,
    div[role="radiogroup"] label:has(input:checked) div[data-testid="stMarkdownContainer"] p {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }
    div[role="radiogroup"] input[type="radio"] {
        display: none !important;
    }
    div[role="radiogroup"] div[data-testid="stMarkdownContainer"] p {
        color: #94A3B8 !important;
        font-weight: 500 !important;
        margin: 0 !important;
    }

    /* Footer */
    .cityguard-footer {
        margin-top: 3.5rem;
        padding-top: 2rem;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        color: #64748B;
        font-size: 0.86rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------
# 2. CACHING & DATABASE INITIALIZATION
# -------------------------------------------------------------
db.init_db()

# Ensure uploads directory exists
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@st.cache_resource(show_spinner=False)
def load_cached_model():
    """Safely load and cache the SentenceTransformer embedding model."""
    return ai.get_embedding_model(config.DEFAULT_EMBEDDING_MODEL)


# -------------------------------------------------------------
# 3. GLOBAL NAVIGATION BAR & BRAND HEADER
# -------------------------------------------------------------
render_html(
    f"""
    <div style="display:flex; justify-content:space-between; align-items:center; padding:0.8rem 0; border-bottom:1px solid rgba(255,255,255,0.08); margin-bottom:1.5rem;">
        <div style="display:flex; align-items:center; gap:0.9rem;">
            {CITYGUARD_LOGO_SVG}
            <div>
                <div style="font-family:'Outfit', sans-serif; font-size:1.6rem; font-weight:900; color:#FFFFFF; letter-spacing:-0.03em; line-height:1;">CITYGUARD</div>
                <div style="font-size:0.75rem; color:#3B82F6; font-weight:700; letter-spacing:0.04em; text-transform:uppercase;">Mangaluru City Corporation (MCC)</div>
            </div>
        </div>
        <div style="display:flex; align-items:center; gap:1.2rem;">
            <span style="font-size:0.82rem; color:#94A3B8; font-style:italic;">"Building a Cleaner, Safer and Smarter Mangaluru."</span>
            <a href="https://wa.me/918242220306?text=Hello%20CITYGUARD%20Mangaluru%20Helpdesk" target="_blank" class="btn-whatsapp-civic">
                <span>💬 MCC Helpline</span>
            </a>
        </div>
    </div>
    """
)

# Top Responsive Navigation Segment
nav_options = ["🏠 Home", "📝 Report Issue", "🔍 Track Complaint", "📊 Live Dashboard", "ℹ️ About Us"]
default_idx = 0
if "nav_direct" in st.session_state and st.session_state["nav_direct"] in nav_options:
    default_idx = nav_options.index(st.session_state.pop("nav_direct"))

active_tab = st.radio(
    "Navigation Menu",
    nav_options,
    horizontal=True,
    label_visibility="collapsed",
    index=default_idx,
)

# Sidebar with Officer Admin Access & System Controls
with st.sidebar:
    render_html(
        f"""
        <div style="display:flex; align-items:center; gap:0.7rem; margin-bottom:1rem; padding-bottom:0.8rem; border-bottom:1px solid rgba(255,255,255,0.08);">
            {CITYGUARD_LOGO_SVG}
            <div>
                <div style="font-family:'Outfit', sans-serif; font-weight:800; color:#FFF; font-size:1.15rem;">CITYGUARD</div>
                <div style="font-size:0.68rem; color:#3B82F6; font-weight:700;">MCC CIVIC TECH PLATFORM</div>
            </div>
        </div>
        """
    )

    st.markdown("##### 🔐 Municipal Portal Access")
    admin_view_toggle = st.toggle("Officer / Admin Triage Drawer", value=False)
    if admin_view_toggle:
        st.info("Officer mode active. Head to **Live Dashboard** to review triage queue, assign departments, and link duplicate issues.")

    st.markdown("---")
    st.markdown("##### ⚙️ Demonstration Controls")

    # Seed demo data button
    if st.button("🌱 Load Mangaluru Data (40 Records)", use_container_width=True):
        with st.spinner("Seeding verified Mangaluru complaints..."):
            count = seed_data.seed_database(force_reseed=False)
            if count > 0:
                st.success(f"Added {count} Mangaluru civic records.")
                st.rerun()
            else:
                st.info("Database already seeded (40 Mangaluru records present).")

    # Confirmed database reset
    with st.expander("⚠️ Database Reset"):
        st.caption("Reset SQLite database to empty state for clean submission testing.")
        confirm_reset = st.checkbox("Confirm reset", key="chk_mcc_reset")
        if st.button("Execute Reset", type="primary", use_container_width=True):
            if confirm_reset:
                db.reset_database(confirm=True)
                st.success("Database has been reset.")
                st.rerun()
            else:
                st.warning("Please check confirmation box first.")

    # Supabase Cloud Sync
    with st.expander("☁️ Supabase Cloud Sync"):
        if supabase_client.is_supabase_configured():
            st.success("🟢 Supabase Connected")
            if st.button("Test Connection", use_container_width=True):
                ok, msg = supabase_client.test_supabase_connection()
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
            if st.button("Sync to Supabase", use_container_width=True):
                with st.spinner("Syncing to cloud..."):
                    ok, msg, c_synced = supabase_client.sync_sqlite_to_supabase()
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
        else:
            st.caption("Storage: Local SQLite (`data/civicaction.db`)")
            st.info("💡 Add `SUPABASE_URL` and `SUPABASE_KEY` in `.env` to connect.")

    st.markdown("---")
    st.caption("CITYGUARD v2.5 • Mangaluru City Corporation (MCC)")


# =============================================================
# VIEW 1: HOME (HERO SECTION & TRUST METRICS)
# =============================================================
if active_tab == "🏠 Home":
    render_html(
        """
        <div class="cityguard-hero-section">
            <div class="hero-badge-mcc">🏛️ Official MCC Civic Action Portal • Mangaluru City Corporation</div>
            <h1>Building a Better Mangaluru<br>Starts With You.</h1>
            <p>Report civic issues, track their progress and help make Mangaluru a cleaner, safer and smarter city with CITYGUARD.</p>
        </div>
        """
    )

    # Action Quick Launch Buttons
    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1.2])
    with btn_col1:
        if st.button("🚀 Report an Issue Now", type="primary", use_container_width=True):
            st.session_state["nav_direct"] = "📝 Report Issue"
            st.rerun()
    with btn_col2:
        if st.button("🔍 Track Existing Complaint", use_container_width=True):
            st.session_state["nav_direct"] = "🔍 Track Complaint"
            st.rerun()

    render_html("<div style='height:1rem;'></div>")

    # Real Database Live Metrics Summary
    all_reps = db.get_all_reports()
    total_reps = len(all_reps)
    resolved_reps = len([r for r in all_reps if r["workflow_status"] == "Resolved"])
    pending_reps = len([r for r in all_reps if r["workflow_status"] == "Submitted"])
    inprogress_reps = len([r for r in all_reps if r["workflow_status"] == "In progress"])
    res_percentage = round((resolved_reps / total_reps * 100), 1) if total_reps > 0 else 0

    st.markdown("### 📊 Live Municipal Performance Overview")
    render_html(
        f"""
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:1rem; margin-bottom:2rem;">
            <div class="kpi-stat-card">
                <div class="kpi-number">{total_reps}</div>
                <div class="kpi-caption">Total Complaints Logged</div>
            </div>
            <div class="kpi-stat-card">
                <div class="kpi-number" style="color:#22C55E;">{resolved_reps}</div>
                <div class="kpi-caption">Resolved & Cleared</div>
            </div>
            <div class="kpi-stat-card">
                <div class="kpi-number" style="color:#3B82F6;">{inprogress_reps}</div>
                <div class="kpi-caption">Crew Dispatched / Active</div>
            </div>
            <div class="kpi-stat-card">
                <div class="kpi-number" style="color:#F59E0B;">{pending_reps}</div>
                <div class="kpi-caption">Under Ward Review</div>
            </div>
            <div class="kpi-stat-card">
                <div class="kpi-number" style="color:#A855F7;">{res_percentage}%</div>
                <div class="kpi-caption">Resolution Efficiency</div>
            </div>
        </div>
        """
    )

    # Trust Indicators & Municipal Architecture
    st.markdown("### 🛡️ Why Citizens and Municipal Authorities Trust CITYGUARD")
    t_c1, t_c2, t_c3 = st.columns(3)
    with t_c1:
        render_html(
            """
            <div class="enterprise-card">
                <div style="font-size:2rem; margin-bottom:0.5rem;">⚡</div>
                <h4 style="color:#FFF; margin:0 0 0.4rem 0;">AI Urgency & Explainable Priority</h4>
                <p style="font-size:0.9rem; line-height:1.5;">Every complaint is mathematically scored (+60 hazard, +20 setting, +20 access) with clear reasons so critical emergencies are addressed first.</p>
            </div>
            """
        )
    with t_c2:
        render_html(
            """
            <div class="enterprise-card">
                <div style="font-size:2rem; margin-bottom:0.5rem;">🔗</div>
                <h4 style="color:#FFF; margin:0 0 0.4rem 0;">Semantic Duplicate Intelligence</h4>
                <p style="font-size:0.9rem; line-height:1.5;">Nearby reports within 150m are clustered using Sentence Transformers. Individual tracking tokens are never deleted, ensuring unified dispatch.</p>
            </div>
            """
        )
    with t_c3:
        render_html(
            """
            <div class="enterprise-card">
                <div style="font-size:2rem; margin-bottom:0.5rem;">🔒</div>
                <h4 style="color:#FFF; margin:0 0 0.4rem 0;">Citizen Privacy Guarantee</h4>
                <p style="font-size:0.9rem; line-height:1.5;">Public progress timelines show only verified municipal milestones. Internal officer notes, budgets, and personal citizen contact details remain strictly private.</p>
            </div>
            """
        )


# =============================================================
# VIEW 2: REPORT AN ISSUE (COMPLAINT REPORTING SYSTEM)
# =============================================================
elif active_tab == "📝 Report Issue":
    render_html(
        """
        <div class="cityguard-hero-section">
            <div class="hero-badge-mcc">📝 Mangaluru City Corporation • Citizen Grievance Portal</div>
            <h1>Report a Civic Issue</h1>
            <p>Submit your complaint directly to Mangaluru City Corporation. CITYGUARD uses AI to categorize, summarize, and prioritize urgent safety hazards in real-time.</p>
        </div>
        """
    )

    f_col, p_col = st.columns([1.5, 1], gap="large")

    # Session state for landmark presets
    if "p_desc" not in st.session_state:
        st.session_state.p_desc = ""
    if "p_cat" not in st.session_state:
        st.session_state.p_cat = config.CATEGORIES[0]
    if "p_area" not in st.session_state:
        st.session_state.p_area = list(config.DEMO_AREAS.keys())[0]
    if "p_lat" not in st.session_state:
        st.session_state.p_lat = config.DEMO_AREAS[st.session_state.p_area]["lat"]
    if "p_lon" not in st.session_state:
        st.session_state.p_lon = config.DEMO_AREAS[st.session_state.p_area]["lon"]

    with p_col:
        render_html(
            """
            <div class="enterprise-card">
                <h4 style="margin:0 0 0.4rem 0; color:#FFF;">📍 Mangaluru Landmark Quick-Fill</h4>
                <p style="font-size:0.86rem; color:#94A3B8; margin-bottom:0.8rem;">Click a recognized landmark to automatically populate verified coordinates:</p>
            </div>
            """
        )

        for p in config.SAMPLE_COORDINATES:
            if st.button(f"📌 {p['label']} ({p['area']})", key=f"btn_p_{p['label']}", use_container_width=True):
                st.session_state.p_area = p["area"]
                st.session_state.p_lat = p["lat"]
                st.session_state.p_lon = p["lon"]
                if "Market" in p["label"]:
                    st.session_state.p_desc = "Massive open pothole in the asphalt near Hampankatta Central Market road. Vehicles are swerving into oncoming traffic."
                    st.session_state.p_cat = "Road damage"
                elif "School" in p["label"]:
                    st.session_state.p_desc = "Asphalt collapsed forming a deep sinkhole right outside the school gate. Two school children nearly fell in this morning. Immediate danger!"
                    st.session_state.p_cat = "Road damage"
                elif "Hospital" in p["label"]:
                    st.session_state.p_desc = "Uncollected medical waste and rotting organic garbage dumped outside hospital emergency gate. Serious health hazard."
                    st.session_state.p_cat = "Waste"
                elif "Terminal" in p["label"]:
                    st.session_state.p_desc = "Main water pipeline burst near highway turn shooting drinking water 10 feet into the air. Clean water wasted."
                    st.session_state.p_cat = "Water supply"
                elif "Bus Stand" in p["label"]:
                    st.session_state.p_desc = "Drainage culvert overflowing with black sewer water onto KSRTC bus stand passenger walkway."
                    st.session_state.p_cat = "Drainage / waterlogging"
                st.rerun()

    with f_col:
        with st.form("cityguard_complaint_form"):
            category_icons = {
                "Road damage": "🛣️ Road damage",
                "Waste": "🗑️ Waste",
                "Drainage / waterlogging": "🌊 Drainage / waterlogging",
                "Streetlights / electrical": "💡 Streetlights / electrical",
                "Water supply": "🚰 Water supply",
                "Other": "📌 Other",
            }
            formatted_categories = [category_icons.get(c, c) for c in config.CATEGORIES]

            selected_cat_formatted = st.selectbox(
                "Issue Category",
                formatted_categories,
                index=config.CATEGORIES.index(st.session_state.p_cat) if st.session_state.p_cat in config.CATEGORIES else 0,
            )
            selected_cat = selected_cat_formatted.split(" ", 1)[1] if " " in selected_cat_formatted else selected_cat_formatted

            complaint_text = st.text_area(
                "Detailed Complaint Description",
                value=st.session_state.p_desc,
                height=130,
                placeholder="Describe the issue, landmarks, safety hazards, and disruption details...",
            )

            # Live Character Counter
            char_count = len(complaint_text.strip())
            st.caption(f"Character count: {char_count} / {config.MAX_DESCRIPTION_LENGTH} (Min {config.MIN_DESCRIPTION_LENGTH})")

            # Photo / Media Upload with Preview
            uploaded_media = st.file_uploader(
                "Attach Photo or Video Evidence (Optional)",
                type=["jpg", "jpeg", "png", "mp4"],
                help="Upload visual evidence of the civic issue to assist municipal field engineers.",
            )

            if uploaded_media:
                if uploaded_media.type.startswith("image"):
                    st.image(uploaded_media, caption="Uploaded Evidence Preview", width=300)
                elif uploaded_media.type.startswith("video"):
                    st.video(uploaded_media)

            # Location inputs
            w_col, lat_col, lon_col = st.columns(3)
            with w_col:
                selected_ward = st.selectbox(
                    "Mangaluru Ward",
                    list(config.DEMO_AREAS.keys()),
                    index=list(config.DEMO_AREAS.keys()).index(st.session_state.p_area) if st.session_state.p_area in config.DEMO_AREAS else 0,
                )
            with lat_col:
                in_lat = st.number_input("Latitude", value=float(st.session_state.p_lat), format="%.4f")
            with lon_col:
                in_lon = st.number_input("Longitude", value=float(st.session_state.p_lon), format="%.4f")

            submit_action = st.form_submit_button("🚀 Submit Complaint to CITYGUARD", type="primary", use_container_width=True)

        if submit_action:
            clean_desc = complaint_text.strip()
            if len(clean_desc) < config.MIN_DESCRIPTION_LENGTH:
                st.error(f"Description must contain at least {config.MIN_DESCRIPTION_LENGTH} characters of detail.")
            elif len(clean_desc) > config.MAX_DESCRIPTION_LENGTH:
                st.error(f"Description exceeds maximum allowed limit of {config.MAX_DESCRIPTION_LENGTH} characters.")
            else:
                with st.spinner("AI analyzing complaint, calculating priority score, and scanning nearby duplicates..."):
                    existing_reps = db.get_all_reports()
                    model = load_cached_model()

                    analysis = ai.analyze_complaint(
                        description=clean_desc,
                        citizen_category=selected_cat,
                        latitude=in_lat,
                        longitude=in_lon,
                        area=selected_ward,
                        existing_reports=existing_reps,
                        model=model,
                    )

                    # Save uploaded photo if present
                    saved_filename = None
                    if uploaded_media:
                        saved_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_media.name}"
                        file_save_path = UPLOAD_DIR / saved_filename
                        with open(file_save_path, "wb") as f:
                            f.write(uploaded_media.getbuffer())

                    # Persist Report
                    token = db.generate_tracking_token()
                    report_payload = {
                        "tracking_token": token,
                        "description": clean_desc,
                        "citizen_category": selected_cat,
                        "predicted_category": analysis["predicted_category"],
                        "category_evidence": analysis["category_evidence"],
                        "extractive_summary": analysis["extractive_summary"],
                        "latitude": in_lat,
                        "longitude": in_lon,
                        "area": selected_ward,
                        "priority_score": analysis["priority_score"],
                        "priority_label": analysis["priority_label"],
                        "priority_reasons": analysis["priority_reasons"],
                        "needs_review": analysis["needs_review"],
                        "analysis_status": analysis["analysis_status"],
                        "analysis_error": analysis["analysis_error"],
                        "workflow_status": "Submitted",
                        "assigned_department": None,
                    }
                    rep_id = db.insert_report(report_payload)

                    for dup in analysis.get("duplicate_candidates", []):
                        db.record_duplicate_candidate(
                            source_id=rep_id,
                            candidate_id=dup["candidate_id"],
                            similarity=dup["similarity_score"],
                            distance_meters=dup["distance_meters"],
                            review_state="suggested",
                        )

                # Modern Success Receipt Card
                render_html(
                    f"""
                    <div style="background:#16243A; border:1px solid #22C55E; border-radius:14px; padding:1.6rem; margin-top:1.5rem; animation:fadeInSlide 0.5s ease;">
                        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:1rem; margin-bottom:1.2rem;">
                            <div>
                                <div style="font-size:0.75rem; color:#22C55E; font-weight:700; text-transform:uppercase;">Official CITYGUARD Tracking ID</div>
                                <div style="font-family:'JetBrains Mono', monospace; font-size:1.8rem; font-weight:800; color:#FFFFFF;">{token}</div>
                            </div>
                            <div style="background:#22C55E; color:#0B1220; padding:0.4rem 1.2rem; border-radius:20px; font-weight:800; font-size:0.88rem;">
                                Submitted & Logged
                            </div>
                        </div>
                        <p style="margin:0; font-size:0.95rem; color:#E2E8F0;">
                            <strong>✅ Your complaint has been recorded in the Mangaluru City Corporation system.</strong> You can track live field updates under <strong>Track Complaint</strong>.
                        </p>
                    </div>
                    """
                )

                # AI Explainability Receipt Expander
                with st.expander("🔍 Transparent AI Intelligence Receipt", expanded=True):
                    rc1, rc2, rc3 = st.columns(3)
                    with rc1:
                        st.markdown("**Rule-Based Classification**")
                        st.write(f"`{analysis['predicted_category']}`")
                        raw_ev = analysis.get("category_evidence", [])
                        ev_list = json.loads(raw_ev) if isinstance(raw_ev, str) else (raw_ev or [])
                        if ev_list:
                            st.caption(f"Matched keyword evidence: {', '.join(ev_list)}")
                    with rc2:
                        st.markdown("**Extractive Summary**")
                        st.write(f'"{analysis["extractive_summary"]}"')
                    with rc3:
                        st.markdown("**Explainable Priority**")
                        pl = analysis["priority_label"]
                        ps = analysis["priority_score"]
                        chip_class = "chip-high chip-high-glow" if pl == "High" else ("chip-medium" if pl == "Medium" else "chip-low")
                        render_html(f"<span class='chip-pill {chip_class}'>{pl} ({ps}/100)</span>")

                    raw_reasons = analysis.get("priority_reasons", [])
                    reasons = json.loads(raw_reasons) if isinstance(raw_reasons, str) else (raw_reasons or [])
                    if reasons:
                        st.markdown("**Point Allocation Factors:**")
                        for r in reasons:
                            st.write(f"- **{r.get('factor')}** (+{r.get('points')} pts): {r.get('explanation')}")

                    dups = analysis.get("duplicate_candidates", [])
                    if dups:
                        st.markdown("---")
                        st.markdown(f"**🔗 Potential Nearby Duplicate Complaints ({len(dups)} detected within 150m):**")
                        for d in dups:
                            st.info(f"• Report #{d['candidate_id']} ({d['candidate_token']}) — {d['distance_meters']}m away | Similarity: {d['similarity_score']:.2f}")


# =============================================================
# VIEW 3: TRACK COMPLAINT (CITIZEN TRACKING)
# =============================================================
elif active_tab == "🔍 Track Complaint":
    render_html(
        """
        <div class="cityguard-hero-section">
            <div class="hero-badge-mcc">🔍 Live Citizen Tracking Portal • Mangaluru City Corporation</div>
            <h1>Track Your Complaint</h1>
            <p>Enter your 16-character CITYGUARD tracking ID to view real-time department assignments, field team dispatches, and public resolution milestones.</p>
        </div>
        """
    )

    tc1, tc2 = st.columns([2, 1])
    with tc1:
        query_token = st.text_input(
            "Enter CITYGUARD Tracking Token",
            placeholder="e.g. CIVIC-A1B2-C3D4",
        ).strip().upper()
    with tc2:
        render_html("<div style='height:1.75rem;'></div>")
        search_clicked = st.button("🔎 Look Up Status", type="primary", use_container_width=True)

    if query_token or search_clicked:
        if not query_token:
            st.warning("Please enter a valid tracking token.")
        else:
            rep = db.get_report_by_token(query_token)
            if not rep:
                st.error(f"No grievance found matching token `{query_token}`. Please check the ID or contact the MCC Helpline.")
            else:
                stat = rep["workflow_status"]
                status_colors = {
                    "Submitted": "#3B82F6",
                    "Reviewed": "#60A5FA",
                    "Assigned": "#F59E0B",
                    "In progress": "#A855F7",
                    "Resolved": "#22C55E",
                }
                badge_col = status_colors.get(stat, "#64748B")

                render_html(
                    f"""
                    <div class="enterprise-card" style="border:1px solid {badge_col};">
                        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:1rem; margin-bottom:1.2rem;">
                            <div>
                                <span style="font-size:0.75rem; color:#94A3B8; font-weight:700; text-transform:uppercase;">Complaint Tracking Token</span>
                                <div style="font-size:1.8rem; font-weight:800; color:#FFFFFF; font-family:'JetBrains Mono', monospace;">{rep['tracking_token']}</div>
                            </div>
                            <div style="background:{badge_col}; color:#FFFFFF; padding:0.45rem 1.4rem; border-radius:24px; font-weight:800; font-size:1rem; box-shadow:0 4px 14px {badge_col}44;">
                                {stat}
                            </div>
                        </div>
                        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:1.2rem; font-size:0.92rem;">
                            <div><strong style="color:#FFF;">Assigned Department:</strong><br><span style="color:#3B82F6; font-weight:600;">{rep['assigned_department'] or 'Pending Ward Review'}</span></div>
                            <div><strong style="color:#FFF;">Mangaluru Ward:</strong><br>{rep['area']}</div>
                            <div><strong style="color:#FFF;">Category:</strong><br>{rep['citizen_category']}</div>
                            <div><strong style="color:#FFF;">Submitted On:</strong><br>{rep['created_at'][:10]} {rep['created_at'][11:16]} UTC</div>
                        </div>
                        <div style="margin-top:1.2rem; padding:1rem; background:rgba(0,0,0,0.25); border-radius:8px; font-size:0.92rem; border-left:4px solid #3B82F6;">
                            <strong style="color:#FFF;">Summary:</strong> {rep['extractive_summary']}
                        </div>
                    </div>
                    """
                )

                # Confirmed Related Duplicate Warning
                confirmed_rel = db.check_has_confirmed_related(rep["id"])
                if confirmed_rel:
                    for cr in confirmed_rel:
                        st.info(
                            f"ℹ️ **Coordinated Response Notice**: This complaint has been linked with confirmed related complaint "
                            f"`{cr['tracking_token']}`. MCC field teams are coordinating a unified route inspection."
                        )

                # Public Event Audit Trail
                st.markdown("### 📋 Public Service Timeline")
                events = db.get_report_events(rep["id"], public_only=True)
                if not events:
                    st.write("No progress updates logged yet.")
                else:
                    for ev in events:
                        icon = "✅" if ev["event_type"] == "created" else ("🔧" if ev["event_type"] == "assigned" else ("📢" if ev["event_type"] == "status_change" else "📝"))
                        render_html(
                            f"""
                            <div style="border-left: 3px solid #3B82F6; padding-left: 1.2rem; margin-left: 0.6rem; margin-bottom: 1.2rem;">
                                <div style="font-size:0.8rem; color:#94A3B8; font-weight:600;">{ev['created_at'][:10]} {ev['created_at'][11:16]} UTC</div>
                                <div style="font-weight:700; color:#FFFFFF; margin:0.15rem 0; font-size:0.95rem;">{icon} {ev['event_type'].replace('_', ' ').title()}</div>
                                <div style="color:#CBD5E1; font-size:0.92rem; background:rgba(255,255,255,0.03); padding:0.6rem 0.9rem; border-radius:6px; margin-top:0.3rem;">{ev['note']}</div>
                            </div>
                            """
                        )

                st.caption("🔒 Privacy Guarantee: Only verified public municipal progress milestones are displayed. Internal officer deliberations are excluded.")


# =============================================================
# VIEW 4: LIVE DASHBOARD (ANALYTICS, MAP & TRIAGE)
# =============================================================
elif active_tab == "📊 Live Dashboard":
    render_html(
        """
        <div class="cityguard-hero-section">
            <div class="hero-badge-mcc">📊 Mangaluru City Corporation • Live Intelligence & Operations</div>
            <h1>CITYGUARD Live Dashboard</h1>
            <p>Real-time municipal grievance data, ward clustering, and action briefs across Mangaluru's municipal wards.</p>
        </div>
        """
    )

    all_reports = db.get_all_reports()

    if not all_reports:
        st.info("No complaints found in the database. Use '🌱 Load Mangaluru Data (40 Records)' in the sidebar to populate realistic complaints.")
    else:
        df = pd.DataFrame(all_reports)

        df["effective_priority"] = df.apply(
            lambda r: r["priority_override_score"] if pd.notnull(r["priority_override_score"]) else r["priority_score"],
            axis=1,
        )
        df["effective_label"] = df.apply(
            lambda r: r["priority_override_label"] if pd.notnull(r["priority_override_label"]) and r["priority_override_label"] else r["priority_label"],
            axis=1,
        )

        # KPI Metrics
        total_reps = len(df)
        open_reps = len(df[df["workflow_status"] != "Resolved"])
        high_p_reps = len(df[(df["effective_priority"] >= 60) & (df["workflow_status"] != "Resolved")])
        unassigned_reps = len(df[(df["assigned_department"].isna()) | (df["assigned_department"] == "")])
        resolved_reps = len(df[df["workflow_status"] == "Resolved"])
        needs_review_reps = len(df[df["needs_review"] == 1])

        render_html(
            f"""
            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap:1rem; margin-bottom:1.5rem;">
                <div class="kpi-stat-card">
                    <div class="kpi-number">{total_reps}</div>
                    <div class="kpi-caption">Total Reports</div>
                </div>
                <div class="kpi-stat-card">
                    <div class="kpi-number" style="color:#3B82F6;">{open_reps}</div>
                    <div class="kpi-caption">Active Open</div>
                </div>
                <div class="kpi-stat-card">
                    <div class="kpi-number" style="color:#EF4444;">{high_p_reps}</div>
                    <div class="kpi-caption">High-Hazard Open</div>
                </div>
                <div class="kpi-stat-card">
                    <div class="kpi-number" style="color:#F59E0B;">{unassigned_reps}</div>
                    <div class="kpi-caption">Unassigned</div>
                </div>
                <div class="kpi-stat-card">
                    <div class="kpi-number" style="color:#22C55E;">{resolved_reps}</div>
                    <div class="kpi-caption">Resolved</div>
                </div>
                <div class="kpi-stat-card">
                    <div class="kpi-number" style="color:#A855F7;">{needs_review_reps}</div>
                    <div class="kpi-caption">Needs Review</div>
                </div>
            </div>
            """
        )

        # Ward Selection & Action Brief
        st.markdown("### 📊 Area-Level Grouping & Action Brief")
        selected_ward_filter = st.selectbox(
            "Select Mangaluru Ward to Inspect",
            ["All Wards"] + list(config.DEMO_AREAS.keys()),
            index=0,
        )

        active_df = df[df["workflow_status"] != "Resolved"]
        if selected_ward_filter != "All Wards":
            ward_df = active_df[active_df["area"] == selected_ward_filter]
        else:
            ward_df = active_df

        w_count = len(ward_df)
        w_cats = ward_df["predicted_category"].value_counts()
        w_top_cat = w_cats.index[0] if not w_cats.empty else "None"
        w_top_count = w_cats.iloc[0] if not w_cats.empty else 0
        w_high_p = len(ward_df[ward_df["effective_priority"] >= 60])

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
            for r_id in ward_df["id"]:
                if r_id not in visited:
                    clusters += 1
                    queue = [r_id]
                    visited.add(r_id)
                    while queue:
                        curr = queue.pop(0)
                        for neighbor in adj.get(curr, []):
                            if neighbor in ward_df["id"].values and neighbor not in visited:
                                visited.add(neighbor)
                                queue.append(neighbor)

        dept_recs = {
            "Road damage": "Roads & Civil Works Division",
            "Waste": "Sanitation & Solid Waste Management",
            "Drainage / waterlogging": "Drainage & Stormwater Maintenance",
            "Streetlights / electrical": "MESCOM / City Electrical Maintenance",
            "Water supply": "Municipal Water Services & Pipe Network",
            "Other": "General Municipal Grievance Cell",
        }
        rec_dept = dept_recs.get(w_top_cat, "General Municipal Cell")

        render_html(
            f"""
            <div class="brief-panel">
                <h4>📋 Operational Brief: {selected_ward_filter}</h4>
                <div style="font-size:0.95rem; line-height:1.6; color:#E2E8F0;">
                    • <strong>Current Workload:</strong> {w_count} raw complaints representing <strong>{clusters} unique physical issue clusters</strong>.<br>
                    • <strong>Primary Complaint Pattern:</strong> <code>{w_top_cat}</code> ({w_top_count} active reports).<br>
                    • <strong>High-Risk Safety Alerts:</strong> <span style="color:#EF4444; font-weight:700;">{w_high_p} severe issues</span> require immediate site inspection.<br>
                    • <strong>Recommended Response:</strong> Deploy <strong>{rec_dept}</strong> for combined route inspection.
                </div>
            </div>
            """
        )

        # Interactive Map & Queue Filters
        m1, m2 = st.columns([1, 1], gap="medium")
        with m1:
            st.markdown("##### 🗺️ Geographic Distribution (Mangaluru)")
            map_data = ward_df[["latitude", "longitude"]].copy()
            if not map_data.empty:
                st.map(map_data, zoom=12, use_container_width=True)
            else:
                st.info("No active complaints to display on map.")

        with m2:
            st.markdown("##### ⚡ Queue Filters")
            f_cat = st.multiselect("Category", config.CATEGORIES, default=[])
            f_prio = st.multiselect("Priority", ["High", "Medium", "Low"], default=[])

            filtered_df = ward_df
            if f_cat:
                filtered_df = filtered_df[filtered_df["predicted_category"].isin(f_cat)]
            if f_prio:
                filtered_df = filtered_df[filtered_df["effective_label"].isin(f_prio)]

            st.caption(f"Showing **{len(filtered_df)}** prioritized reports in queue.")

        st.markdown("##### Filtered Complaint Queue")
        disp_cols = ["id", "tracking_token", "area", "predicted_category", "effective_priority", "effective_label", "workflow_status", "assigned_department", "created_at"]
        st.dataframe(filtered_df[disp_cols], use_container_width=True, height=260)

        # Officer Triage Drawer (if enabled in sidebar)
        if admin_view_toggle:
            st.markdown("---")
            st.markdown("### 🛠️ Officer Triage & Review Console")
            avail_ids = filtered_df["id"].tolist() if not filtered_df.empty else df["id"].tolist()
            sel_id = st.selectbox("Select Report to Review & Dispatch", avail_ids, format_func=lambda x: f"Report #{x} — [{df[df['id']==x]['tracking_token'].values[0]}] ({df[df['id']==x]['area'].values[0]}) - {df[df['id']==x]['extractive_summary'].values[0][:60]}...")

            if sel_id:
                r_rep = db.get_report_by_id(sel_id)
                if r_rep:
                    tc1, tc2 = st.columns([1, 1], gap="large")
                    with tc1:
                        st.markdown("##### 📄 Complaint Information")
                        st.write(f"**Token:** `{r_rep['tracking_token']}` | **Ward:** {r_rep['area']}")
                        st.write(f"**Category:** `{r_rep['predicted_category']}` | **Submitted:** {r_rep['created_at'][:16]} UTC")
                        st.text_area("Description", r_rep["description"], height=90, disabled=True)

                        # Priority override
                        with st.expander("✏️ Priority Override (Audit Logged)"):
                            with st.form(f"prio_override_form_{r_rep['id']}"):
                                new_lbl = st.selectbox("New Label", ["High", "Medium", "Low"])
                                new_sc = st.slider("New Score", 0, 100, 75 if new_lbl=="High" else 45)
                                rsn = st.text_input("Mandatory Justification", placeholder="Verified during site inspection...")
                                if st.form_submit_button("Save Priority Override"):
                                    if not rsn.strip():
                                        st.error("Justification is mandatory.")
                                    else:
                                        db.override_priority(r_rep["id"], new_sc, new_lbl, rsn)
                                        st.success("Priority override recorded.")
                                        st.rerun()

                    with tc2:
                        st.markdown("##### 🔄 Department Assignment & Workflow")
                        with st.form(f"workflow_update_form_{r_rep['id']}"):
                            n_dept = st.selectbox("Assign Department", config.DEPARTMENTS, index=config.DEPARTMENTS.index(r_rep["assigned_department"]) if r_rep["assigned_department"] in config.DEPARTMENTS else 0)
                            cur_stat = r_rep["workflow_status"]
                            valid_next = config.ALLOWED_TRANSITIONS.get(cur_stat, [cur_stat])
                            stat_opts = list(dict.fromkeys([cur_stat] + valid_next))
                            n_stat = st.selectbox("Update Status", stat_opts, index=0)
                            w_note = st.text_area("Progress / Resolution Note")
                            is_pub = st.checkbox("Visible on citizen timeline", value=True)

                            if st.form_submit_button("Update Workflow", type="primary"):
                                s_ok, s_msg = db.update_report_workflow(r_rep["id"], n_stat, n_dept, w_note, is_pub)
                                if s_ok:
                                    st.success(s_msg)
                                    st.rerun()
                                else:
                                    st.error(s_msg)

                        # Duplicate candidates review
                        dups = db.get_duplicates_for_report(r_rep["id"])
                        if dups:
                            st.markdown("##### 🔗 Suggested Duplicate Links")
                            for d in dups:
                                st.write(f"• #{d['candidate_report_id']} ({d['tracking_token']}) — State: `{d['review_state']}` | Sim: {d['similarity_score']:.2f} | Dist: {d['distance_meters']}m")
                                b1, b2 = st.columns(2)
                                with b1:
                                    if st.button("Confirm Link", key=f"c_dup_{d['relationship_id']}"):
                                        db.update_duplicate_review_state(d["relationship_id"], "confirmed")
                                        st.success("Linked duplicate.")
                                        st.rerun()
                                with b2:
                                    if st.button("Reject", key=f"r_dup_{d['relationship_id']}"):
                                        db.update_duplicate_review_state(d["relationship_id"], "rejected")
                                        st.info("Rejected.")
                                        st.rerun()


# =============================================================
# VIEW 5: ABOUT US & CITIZEN FAQ
# =============================================================
elif active_tab == "ℹ️ About Us":
    render_html(
        """
        <div class="cityguard-hero-section">
            <div class="hero-badge-mcc">ℹ️ About CITYGUARD • Mangaluru City Corporation (MCC)</div>
            <h1>About CITYGUARD</h1>
            <p>Empowering citizens and municipal engineers across Mangaluru with transparent, AI-prioritized civic action.</p>
        </div>
        """
    )

    a1, a2 = st.columns([1.3, 1], gap="large")

    with a1:
        render_html(
            """
            <div class="enterprise-card">
                <h3 style="color:#FFF; margin-top:0;">Our Mission</h3>
                <p style="font-size:0.95rem; line-height:1.6;">
                    <strong>CITYGUARD</strong> is Mangaluru City Corporation's flagship public action portal.
                    By bridging citizens directly with municipal ward engineers and response crews,
                    CITYGUARD turns scattered reports into prioritized, explainable, and trackable civic action.
                </p>
                <h4 style="color:#3B82F6; margin-top:1.2rem;">Mangaluru Municipal Zones Covered</h4>
                <ul style="font-size:0.9rem; line-height:1.8; color:#CBD5E1;">
                    <li><strong>Hampankatta</strong> (Central Commercial, Market & Educational Hub)</li>
                    <li><strong>Kadri Hills</strong> (Residential greenways, Kadri Temple, & Nanthoor Corridor)</li>
                    <li><strong>Lalbagh - Ladyhill</strong> (MCC City Corporation Headquarters & MG Road)</li>
                    <li><strong>Kankanady - Pumpwell</strong> (Healthcare Hub, Father Muller Hospital & South Bypass)</li>
                    <li><strong>Surathkal - Kulai</strong> (Coastal Highway, NITK Corridor & Industrial Zone)</li>
                </ul>
            </div>
            """
        )

    with a2:
        render_html(
            """
            <div class="enterprise-card">
                <h3 style="color:#FFF; margin-top:0;">MCC Civic Action Desk</h3>
                <p style="font-size:0.9rem; color:#94A3B8;">Mangaluru City Corporation Headquarters<br>MG Road, Lalbagh, Mangaluru, Karnataka - 575003</p>
                <div style="margin:1rem 0;">
                    <a href="https://wa.me/918242220306?text=Hello%20CITYGUARD%20Mangaluru%20Helpdesk" target="_blank" class="btn-whatsapp-civic">
                        <span>💬 WhatsApp Helpline: +91 824 222 0306</span>
                    </a>
                </div>
                <div style="font-size:0.86rem; color:#94A3B8; line-height:1.6;">
                    • <strong>Municipal Landline:</strong> 0824-2220306<br>
                    • <strong>Emergency Control Room:</strong> 112 / 101<br>
                    • <strong>Email:</strong> complaints@mangalurucity.gov.in
                </div>
            </div>
            """
        )

    st.markdown("### ❓ Frequently Asked Questions")
    with st.expander("How does CITYGUARD's AI determine complaint priority?"):
        st.write(
            "CITYGUARD implements a transparent, explainable additive scoring model:\n"
            "- **+60 points** for immediate physical danger (exposed live wires, collapsing culverts, open sinkholes).\n"
            "- **+20 points** for sensitive community settings (schools, hospitals, public parks).\n"
            "- **+20 points** for critical access disruptions (flooded roadways, impassable streets, total water supply cuts).\n"
            "Complaints scoring 60–100 are flagged as **High Priority** with emergency dispatch."
        )
    with st.expander("What happens when multiple citizens report the same issue?"):
        st.write(
            "CITYGUARD computes 384-dimensional semantic vectors using local Sentence Transformers. "
            "Complaints within 150 metres and 7 days with ≥ 0.80 similarity are linked as related items. "
            "Every citizen maintains their individual tracking token and receives updates when the shared problem is resolved."
        )
    with st.expander("How can I track the progress of my complaint?"):
        st.write(
            "Navigate to the **Track Complaint** tab and enter your unique 16-character tracking ID (e.g. `CIVIC-XXXX-XXXX`). "
            "You will see the assigned department, current status, and public milestones entered by field engineers."
        )


# -------------------------------------------------------------
# 4. ENTERPRISE FOOTER
# -------------------------------------------------------------
render_html(
    f"""
    <div class="cityguard-footer">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1.2rem; margin-bottom:1.5rem;">
            <div style="display:flex; align-items:center; gap:0.8rem;">
                {CITYGUARD_LOGO_SVG}
                <div>
                    <div style="font-family:'Outfit', sans-serif; font-size:1.3rem; font-weight:900; color:#FFFFFF;">CITYGUARD</div>
                    <div style="font-size:0.75rem; color:#94A3B8;">Mangaluru City Corporation • Smart Civic Action Portal</div>
                </div>
            </div>
            <div style="font-size:0.88rem; color:#3B82F6; font-style:italic;">
                "Building a Cleaner, Safer and Smarter Mangaluru."
            </div>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1rem; border-top:1px solid rgba(255,255,255,0.06); padding-top:1rem; font-size:0.8rem; color:#64748B;">
            <div>© 2026 Mangaluru City Corporation (MCC) & CITYGUARD. All rights reserved.</div>
            <div style="display:flex; gap:1.2rem;">
                <span>Privacy Policy</span>
                <span>Terms of Service</span>
                <span>MCC Ward Directory</span>
                <span>Open Data Portal</span>
            </div>
        </div>
    </div>
    """
)
