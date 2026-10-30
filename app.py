"""
CivicAction: Explainable Civic Issue Triage & Intelligence
Streamlit Web Application
Provides three cohesive views:
1. Report an issue (Citizen submission with immediate explainable feedback)
2. Officer dashboard (Area-level briefs, triage, workflow updates, and duplicate linking)
3. Track my report (Citizen token lookup with public audit trail)
"""

import json
from datetime import datetime, timezone
import pandas as pd
import streamlit as st

import config
import database as db
import ai_pipeline as ai
import seed_data

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="CivicAction | Civic Issue Intelligence",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling for Clean Civic-Service Interface
st.markdown(
    """
    <style>
    /* Civic Action Clean Theme */
    .stApp {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    .civic-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%);
        color: white;
        padding: 1.2rem 1.5rem;
        border-radius: 8px;
        margin-bottom: 1.2rem;
    }
    .civic-header h1 {
        color: #f8fafc;
        margin: 0;
        font-size: 1.6rem;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    .civic-header p {
        color: #94a3b8;
        margin: 0.3rem 0 0 0;
        font-size: 0.9rem;
    }
    .disclaimer-banner {
        background-color: #fef3c7;
        color: #92400e;
        border-left: 4px solid #f59e0b;
        padding: 0.6rem 1rem;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: 500;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 0.8rem 1rem;
        text-align: center;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #0f172a;
    }
    .metric-label {
        font-size: 0.75rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .badge-high {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 2px 8px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-medium {
        background-color: #fef3c7;
        color: #92400e;
        padding: 2px 8px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-low {
        background-color: #dcfce7;
        color: #166534;
        padding: 2px 8px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .action-brief {
        background-color: #eff6ff;
        border: 1px solid #bfdbfe;
        border-radius: 6px;
        padding: 0.8rem 1rem;
        color: #1e3a8a;
        margin-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Database Idempotently
db.init_db()


# Cached Embedding Model (Using Streamlit Resource Caching)
@st.cache_resource(show_spinner=False)
def load_cached_model():
    """Load and cache SentenceTransformer instance safely."""
    return ai.get_embedding_model(config.DEFAULT_EMBEDDING_MODEL)


# -------------------------------------------------------------
# SIDEBAR NAVIGATION & SYSTEM SETTINGS
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🏛️ CivicAction")
    st.caption("Explainable Civic Issue Triage")

    nav_selection = st.radio(
        "Navigation",
        ["Report an issue", "Officer dashboard", "Track my report"],
        index=0,
    )

    st.markdown("---")
    st.markdown("#### ⚙️ Demo Controls")

    # Seed Data Button
    if st.button("🌱 Load Synthetic Demo Data (40 Reports)"):
        with st.spinner("Seeding synthetic complaints..."):
            count = seed_data.seed_database(force_reseed=False)
            if count > 0:
                st.success(f"Added {count} synthetic reports.")
                st.rerun()
            else:
                st.info("Demo data already loaded (40 reports present).")

    # Safe Confirmed Reset
    with st.expander("⚠️ Database Reset"):
        st.write("Reset database to empty state for testing clean submissions.")
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
        import supabase_client
        if supabase_client.is_supabase_configured():
            st.success("🟢 Supabase configured in .env")
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
            st.caption("Backend: Local SQLite (`data/civicaction.db`)")
            st.info("💡 To connect Supabase:\n1. Open `.env`\n2. Set `SUPABASE_URL` & `SUPABASE_KEY`\n3. Execute `supabase_schema.sql` in your Supabase SQL Editor.")

    st.markdown("---")
    st.caption("CivicAction v1.0 • Built for Solo Civic Hackathon")


# -------------------------------------------------------------
# SCREEN 1: REPORT AN ISSUE (CITIZEN VIEW)
# -------------------------------------------------------------
if nav_selection == "Report an issue":
    st.markdown(
        """
        <div class="civic-header">
            <h1>Report a Civic Issue</h1>
            <p>Submit your complaint for immediate, explainable triage and municipal response.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_form, col_presets = st.columns([2, 1], gap="medium")

    with col_presets:
        st.markdown("#### 📍 Demo Quick Presets")
        st.caption("Click a preset location to populate coordinates:")
        for preset in config.SAMPLE_COORDINATES:
            if st.button(preset["label"], key=f"btn_preset_{preset['label']}", use_container_width=True):
                st.session_state["form_area"] = preset["area"]
                st.session_state["form_lat"] = preset["lat"]
                st.session_state["form_lon"] = preset["lon"]
                st.rerun()

    with col_form:
        # Form values with session state fallbacks
        default_area = st.session_state.get("form_area", list(config.DEMO_AREAS.keys())[0])
        default_lat = st.session_state.get("form_lat", config.DEMO_AREAS[default_area]["lat"])
        default_lon = st.session_state.get("form_lon", config.DEMO_AREAS[default_area]["lon"])

        with st.form("citizen_report_form", clear_on_submit=False):
            st.markdown("##### Describe the Issue")
            complaint_text = st.text_area(
                "Complaint Description",
                placeholder="Describe what happened, exact location details, and whether it poses an immediate hazard...",
                height=130,
                help=f"Minimum {config.MIN_DESCRIPTION_LENGTH} characters, maximum {config.MAX_DESCRIPTION_LENGTH} characters.",
            )

            col_cat, col_area = st.columns(2)
            with col_cat:
                citizen_category = st.selectbox("Category", config.CATEGORIES)
            with col_area:
                selected_area = st.selectbox(
                    "Demo Area",
                    list(config.DEMO_AREAS.keys()),
                    index=list(config.DEMO_AREAS.keys()).index(default_area) if default_area in config.DEMO_AREAS else 0,
                )

            st.markdown("##### Location Coordinates (Fictional Demo)")
            col_lat, col_lon = st.columns(2)
            with col_lat:
                lat_input = st.number_input(
                    "Latitude",
                    min_value=-90.0,
                    max_value=90.0,
                    value=float(default_lat),
                    format="%.5f",
                )
            with col_lon:
                lon_input = st.number_input(
                    "Longitude",
                    min_value=-180.0,
                    max_value=180.0,
                    value=float(default_lon),
                    format="%.5f",
                )

            st.caption("ℹ️ Labeled fictional coordinates are used for demonstration. No real citizen location is collected.")

            submit_button = st.form_submit_button("Submit Complaint", type="primary", use_container_width=True)

        if submit_button:
            # Inline Validation
            clean_text = complaint_text.strip()
            if len(clean_text) < config.MIN_DESCRIPTION_LENGTH:
                st.error(f"Please provide a meaningful complaint description (minimum {config.MIN_DESCRIPTION_LENGTH} characters).")
            elif len(clean_text) > config.MAX_DESCRIPTION_LENGTH:
                st.error(f"Complaint description is too long (maximum {config.MAX_DESCRIPTION_LENGTH} characters).")
            else:
                # Prevent accidental double submit on rerun
                submission_key = f"{clean_text}_{lat_input}_{lon_input}"
                if st.session_state.get("last_submission_key") == submission_key:
                    st.info("This report was already submitted.")
                else:
                    with st.spinner("Recording and analyzing report..."):
                        # 1. Fetch existing reports for duplicate context
                        existing = db.get_all_reports()
                        model = load_cached_model()

                        # 2. Run Analysis Pipeline
                        analysis = ai.analyze_complaint(
                            description=clean_text,
                            citizen_category=citizen_category,
                            latitude=lat_input,
                            longitude=lon_input,
                            area=selected_area,
                            existing_reports=existing,
                            model=model,
                        )

                        # 3. Persist Report in Database
                        tracking_token = db.generate_tracking_token()
                        report_payload = {
                            "tracking_token": tracking_token,
                            "description": clean_text,
                            "citizen_category": citizen_category,
                            "predicted_category": analysis["predicted_category"],
                            "category_evidence": analysis["category_evidence"],
                            "extractive_summary": analysis["extractive_summary"],
                            "latitude": lat_input,
                            "longitude": lon_input,
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

                        report_id = db.insert_report(report_payload)

                        # Record duplicate candidate links if any found
                        for dup in analysis.get("duplicate_candidates", []):
                            db.record_duplicate_candidate(
                                source_id=report_id,
                                candidate_id=dup["candidate_id"],
                                similarity=dup["similarity_score"],
                                distance_meters=dup["distance_meters"],
                                review_state="suggested",
                            )

                        st.session_state["last_submission_key"] = submission_key
                        st.session_state["latest_submitted_token"] = tracking_token
                        st.session_state["latest_analysis"] = analysis
                        st.session_state["latest_report"] = report_payload

    # Display Immediate Explainable Feedback Card
    if "latest_submitted_token" in st.session_state:
        token = st.session_state["latest_submitted_token"]
        analysis = st.session_state.get("latest_analysis", {})
        rep = st.session_state.get("latest_report", {})

        st.markdown("---")
        st.success("✅ **Report Successfully Registered!**")

        st.markdown(
            f"""
            <div style="background:#f0fdf4; border:1px solid #86efac; border-radius:8px; padding:1.2rem; margin-bottom:1rem;">
                <div style="font-size:0.85rem; color:#15803d; font-weight:600;">OFFICIAL TRACKING TOKEN</div>
                <div style="font-size:1.8rem; font-weight:800; color:#166534; font-family:monospace; letter-spacing:0.05em;">{token}</div>
                <div style="font-size:0.85rem; color:#475569; margin-top:0.3rem;">
                    Save this token to monitor response progress under <strong>Track my report</strong>.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        res_col1, res_col2 = st.columns(2)

        with res_col1:
            st.markdown("##### 🔍 Categorization & Summary")
            st.write(f"**Extractive Summary:** {rep.get('extractive_summary', '')}")
            st.write(f"**Citizen Category:** `{rep.get('citizen_category')}`")
            pred_cat = rep.get("predicted_category")
            st.write(f"**Rule-based Category:** `{pred_cat}`")

            evidence = analysis.get("category_evidence", [])
            if evidence:
                st.caption(f"Matched keyword evidence: {', '.join(evidence)}")
            else:
                st.caption("No strong keyword matches; flagged for officer review.")

        with res_col2:
            st.markdown("##### ⚡ Explainable Priority")
            p_score = rep.get("priority_score", 0)
            p_label = rep.get("priority_label", "Low")
            badge_class = f"badge-{p_label.lower()}"

            st.markdown(
                f"**Assigned Priority:** <span class='{badge_class}'>{p_label} ({p_score}/100)</span>",
                unsafe_allow_html=True,
            )

            factors = analysis.get("priority_reasons", [])
            if factors:
                st.markdown("**Applied Policy Factors:**")
                for f in factors:
                    st.write(f"- **{f.get('factor')}** (+{f.get('points', 0)} pts): {f.get('explanation')}")
            else:
                st.write("- Standard baseline priority (no high hazard indicators detected).")

            st.caption("Prototype demonstration rules; not official municipal standards.")

        # Show Duplicate Warnings if suggested
        duplicates = analysis.get("duplicate_candidates", [])
        if duplicates:
            st.markdown("##### 🔗 Possible Related Reports Nearby")
            st.info(
                f"We noticed {len(duplicates)} similar report(s) nearby within 150m. "
                "Your complaint has been saved as an independent record and will be reviewed together by municipal staff."
            )
            for d in duplicates[:3]:
                st.write(
                    f"- **#{d['candidate_id']}** (`{d['candidate_token']}`): *{d['summary']}* "
                    f"— Distance: {d['distance_meters']}m | Similarity: {d['similarity_score']:.2f}"
                )


# -------------------------------------------------------------
# SCREEN 2: OFFICER DASHBOARD
# -------------------------------------------------------------
elif nav_selection == "Officer dashboard":
    st.markdown(
        """
        <div class="civic-header">
            <h1>Municipal Officer Triage Dashboard</h1>
            <p>Monitor real-time incoming complaints, review area clusters, assign departments, and track resolutions.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="disclaimer-banner">
            ⚠️ <strong>Demo officer view — authentication is not implemented.</strong>
            This view simulates the internal triage console for public service administrators.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Fetch All Stored Reports
    all_reports = db.get_all_reports()

    if not all_reports:
        st.info("No reports currently in the database. Use **Load Synthetic Demo Data** in the sidebar or submit a new report.")
    else:
        df = pd.DataFrame(all_reports)

        # -----------------------------------------------------
        # 1. SUMMARY METRICS (KPIs)
        # -----------------------------------------------------
        total_reports = len(df)
        open_reports = len(df[df["workflow_status"] != "Resolved"])
        high_priority_open = len(df[(df["workflow_status"] != "Resolved") & (df["effective_priority"] >= 60)])
        unassigned_reports = len(df[(df["workflow_status"] != "Resolved") & (df["assigned_department"].isna() | (df["assigned_department"] == ""))])
        resolved_reports = len(df[df["workflow_status"] == "Resolved"])
        needs_review_count = len(df[df["needs_review"] == 1])

        kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5, kpi_col6 = st.columns(6)
        with kpi_col1:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{total_reports}</div><div class='metric-label'>Total Reports</div></div>", unsafe_allow_html=True)
        with kpi_col2:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{open_reports}</div><div class='metric-label'>Open Reports</div></div>", unsafe_allow_html=True)
        with kpi_col3:
            st.markdown(f"<div class='metric-card'><div class='metric-value' style='color:#dc2626;'>{high_priority_open}</div><div class='metric-label'>High-Priority Open</div></div>", unsafe_allow_html=True)
        with kpi_col4:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{unassigned_reports}</div><div class='metric-label'>Unassigned</div></div>", unsafe_allow_html=True)
        with kpi_col5:
            st.markdown(f"<div class='metric-card'><div class='metric-value' style='color:#16a34a;'>{resolved_reports}</div><div class='metric-label'>Resolved</div></div>", unsafe_allow_html=True)
        with kpi_col6:
            st.markdown(f"<div class='metric-card'><div class='metric-value' style='color:#d97706;'>{needs_review_count}</div><div class='metric-label'>Needs Review</div></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # -----------------------------------------------------
        # 2. AREA-LEVEL GROUPING & ACTION BRIEF
        # -----------------------------------------------------
        st.markdown("### 📊 Area-level grouping and action brief")

        area_selected = st.selectbox(
            "Select Demo Area to Inspect",
            ["All Areas"] + list(config.DEMO_AREAS.keys()),
            index=0,
        )

        active_df = df[df["workflow_status"] != "Resolved"]
        if area_selected != "All Areas":
            area_active_df = active_df[active_df["area"] == area_selected]
        else:
            area_active_df = active_df

        # Calculate Confirmed Unique Groups vs Raw Submissions
        area_sub_count = len(area_active_df)
        area_cats = area_active_df["predicted_category"].value_counts()
        top_cat = area_cats.index[0] if not area_cats.empty else "None"
        top_cat_count = area_cats.iloc[0] if not area_cats.empty else 0
        area_high_p = len(area_active_df[area_active_df["effective_priority"] >= 60])

        # Confirmed unique issue count calculation
        # Count each confirmed duplicate group once for reviewed-issue metric
        confirmed_pairs = db.get_db_connection()
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT source_report_id, candidate_report_id FROM duplicate_relationships WHERE review_state = 'confirmed';")
            pairs = cursor.fetchall()
            # Simple connected components count
            adj = {}
            for p in pairs:
                s, c = p[0], p[1]
                adj.setdefault(s, set()).add(c)
                adj.setdefault(c, set()).add(s)

        # Count reviewed unique issue groups
        active_ids = set(area_active_df["id"].tolist())
        visited = set()
        unique_groups = 0
        for aid in active_ids:
            if aid not in visited:
                unique_groups += 1
                # Mark cluster
                q = [aid]
                visited.add(aid)
                while q:
                    curr = q.pop(0)
                    for neighbor in adj.get(curr, []):
                        if neighbor in active_ids and neighbor not in visited:
                            visited.add(neighbor)
                            q.append(neighbor)

        # Render Template-based Action Brief
        target_name = area_selected if area_selected != "All Areas" else "Across all areas"
        brief_text = (
            f"**Operational Brief:** {target_name} currently has **{area_sub_count} active submissions** "
            f"(representing **{unique_groups} unique issue clusters**). "
        )
        if top_cat != "None" and top_cat_count > 1:
            brief_text += f"There is a notable concentration of **{top_cat_count} {top_cat.lower()}** reports. "
            brief_text += f"Recommend dispatching a coordinated **{top_cat}** field inspection team to resolve these concurrently."
        else:
            brief_text += "Submissions are evenly distributed across categories without a single dominant cluster."

        st.markdown(f"<div class='action-brief'>{brief_text}</div>", unsafe_allow_html=True)

        with st.expander(f"Supporting Reports for {target_name} ({area_sub_count} active)"):
            if not area_active_df.empty:
                st.dataframe(
                    area_active_df[[
                        "id", "tracking_token", "area", "predicted_category",
                        "effective_priority", "priority_label", "workflow_status", "assigned_department"
                    ]],
                    use_container_width=True,
                )
            else:
                st.write("No active complaints in this area.")

        st.markdown("---")

        # -----------------------------------------------------
        # 3. FILTERS & MAP VIEW
        # -----------------------------------------------------
        st.markdown("### 🗺️ Incident Map & Triage Table")

        filt_col1, filt_col2, filt_col3, filt_col4 = st.columns(4)
        with filt_col1:
            filter_status = st.selectbox("Status Filter", ["All"] + config.WORKFLOW_STATUSES)
        with filt_col2:
            filter_prio = st.selectbox("Priority Filter", ["All", "High", "Medium", "Low"])
        with filt_col3:
            filter_cat = st.selectbox("Category Filter", ["All"] + config.CATEGORIES)
        with filt_col4:
            search_query = st.text_input("Search (Token / Text)", "")

        filtered_df = df.copy()
        if filter_status != "All":
            filtered_df = filtered_df[filtered_df["workflow_status"] == filter_status]
        if filter_prio != "All":
            filtered_df = filtered_df[filtered_df["priority_label"] == filter_prio]
        if filter_cat != "All":
            filtered_df = filtered_df[filtered_df["predicted_category"] == filter_cat]
        if area_selected != "All Areas":
            filtered_df = filtered_df[filtered_df["area"] == area_selected]
        if search_query.strip():
            sq = search_query.strip().lower()
            filtered_df = filtered_df[
                filtered_df["tracking_token"].str.lower().str.contains(sq)
                | filtered_df["description"].str.lower().str.contains(sq)
                | filtered_df["extractive_summary"].str.lower().str.contains(sq)
            ]

        # Location Map with graceful fallback disclosure
        st.caption("Incident Geographic Distribution:")
        if not filtered_df.empty:
            map_data = filtered_df[["latitude", "longitude"]].rename(columns={"latitude": "lat", "longitude": "lon"})
            st.map(map_data, zoom=12)
            st.caption("ℹ️ Map tiles depend on an external basemap provider. If offline, table data and triage below remain fully operational.")
        else:
            st.info("No reports match current filters.")

        # Data Table Sorted by Effective Priority Descending, then Created At Ascending
        st.markdown("##### Filtered Reports Queue")
        display_columns = [
            "id", "tracking_token", "area", "predicted_category",
            "effective_priority", "priority_label", "workflow_status",
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
                    st.write(f"**Area:** {rep['area']} ({rep['latitude']:.4f}, {rep['longitude']:.4f})")
                    st.write(f"**Citizen Category:** `{rep['citizen_category']}`")
                    st.write(f"**Predicted Category:** `{rep['predicted_category']}` (Rule-based)")
                    
                    try:
                        ev_list = json.loads(rep["category_evidence"])
                        if ev_list:
                            st.caption(f"Category Evidence: {', '.join(ev_list)}")
                    except Exception:
                        pass

                    st.write(f"**Extractive Summary:** {rep['extractive_summary']}")
                    st.text_area("Full Description", rep["description"], height=90, disabled=True)

                    # Priority Breakdown
                    st.markdown("##### ⚖️ Priority Breakdown")
                    eff_score = rep["priority_override_score"] if rep["priority_override_score"] is not None else rep["priority_score"]
                    eff_label = rep["priority_override_label"] or rep["priority_label"]
                    badge_class = f"badge-{eff_label.lower()}"
                    st.markdown(
                        f"Current Priority: <span class='{badge_class}'>{eff_label} ({eff_score}/100)</span>",
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
                            override_reason = st.text_input("Mandatory Reason for Override", placeholder="e.g. Verified high hazard during site inspection")
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
                                with btn_c2:
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
                            pub_badge = "🌐 Public" if ev["is_public"] else "🔒 Internal"
                            st.write(f"**[{ev['created_at'][:19]}]** `{ev['event_type']}` ({pub_badge}): {ev['note']}")


# -------------------------------------------------------------
# SCREEN 3: TRACK MY REPORT (CITIZEN VIEW)
# -------------------------------------------------------------
elif nav_selection == "Track my report":
    st.markdown(
        """
        <div class="civic-header">
            <h1>Track Your Report</h1>
            <p>Enter your unique tracking token to view real-time progress and official municipal updates.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    token_input = st.text_input(
        "Enter Tracking Token",
        placeholder="e.g. CIVIC-XXXX-XXXX",
        help="Tokens are generated upon complaint submission.",
    ).strip().upper()

    col_btn, _ = st.columns([1, 4])
    with col_btn:
        btn_refresh = st.button("Check Status", type="primary", use_container_width=True)

    if token_input:
        report = db.get_report_by_token(token_input)
        if not report:
            st.error(f"No report found matching token `{token_input}`. Please verify your tracking code.")
        else:
            st.markdown("---")
            # Citizen Report Card
            status = report["workflow_status"]
            status_colors = {
                "Submitted": "#64748b",
                "Reviewed": "#0284c7",
                "Assigned": "#d97706",
                "In progress": "#7c3aed",
                "Resolved": "#16a34a",
            }
            color = status_colors.get(status, "#64748b")

            st.markdown(
                f"""
                <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:1.5rem; margin-bottom:1.5rem; box-shadow:0 1px 3px rgba(0,0,0,0.05);">
                    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #f1f5f9; padding-bottom:1rem; margin-bottom:1rem;">
                        <div>
                            <span style="font-size:0.8rem; color:#64748b; font-weight:600; text-transform:uppercase;">Tracking Token</span>
                            <div style="font-size:1.6rem; font-weight:800; color:#0f172a; font-family:monospace;">{report['tracking_token']}</div>
                        </div>
                        <div style="background:{color}; color:white; padding:0.4rem 1.2rem; border-radius:20px; font-weight:700; font-size:1rem;">
                            {status}
                        </div>
                    </div>
                    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:1rem; font-size:0.9rem;">
                        <div><strong>Assigned Department:</strong> {report['assigned_department'] or 'Pending Review'}</div>
                        <div><strong>Area:</strong> {report['area']}</div>
                        <div><strong>Category:</strong> {report['citizen_category']}</div>
                        <div><strong>Submitted Date:</strong> {report['created_at'][:10]} {report['created_at'][11:16]} UTC</div>
                    </div>
                    <div style="margin-top:1rem; padding:0.8rem; background:#f8fafc; border-radius:6px; font-size:0.9rem;">
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
                        f"`{cr['tracking_token']}`. Municipal field teams are coordinating a unified inspection."
                    )

            # Public Progress Timeline (Chronological, strictly filtering out internal notes)
            st.markdown("### 📋 Public Progress Timeline")
            events = db.get_report_events(report["id"], public_only=True)

            if not events:
                st.write("No progress events recorded yet.")
            else:
                for idx, ev in enumerate(events):
                    icon = "✅" if ev["event_type"] == "created" else ("🔧" if ev["event_type"] == "assigned" else "📢")
                    st.markdown(
                        f"""
                        <div style="border-left: 3px solid #3b82f6; padding-left: 1rem; margin-left: 0.5rem; margin-bottom: 1rem;">
                            <div style="font-size:0.8rem; color:#64748b;">{ev['created_at'][:10]} {ev['created_at'][11:16]} UTC</div>
                            <div style="font-weight:600; color:#1e293b; margin:0.1rem 0;">{icon} {ev['event_type'].replace('_', ' ').title()}</div>
                            <div style="color:#475569; font-size:0.9rem;">{ev['note']}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            st.caption("🔒 Privacy Guarantee: Only public service progress notes are displayed. Internal officer notes are excluded.")
            st.caption("ℹ️ Demo Notice: Token-based lookup is provided for demonstration purposes. Full identity authentication is not implemented.")
