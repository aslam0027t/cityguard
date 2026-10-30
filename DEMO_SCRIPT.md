# CityGuard 🛡️: 5-Minute Hackathon Demonstration Script
### Mangaluru City Corporation (MCC) • Smart Civic Action

This walkthrough guides evaluators and judges through the complete citizen-to-officer-to-citizen lifecycle of CityGuard in 5 minutes across Mangaluru's municipal wards.

---

## Prerequisites
1. Ensure the virtual environment is activated and the Streamlit application is running:
   ```powershell
   .venv\Scripts\streamlit run app.py
   ```
2. In the sidebar under **Demonstration Controls**, click **🌱 Load Mangaluru Demo Data (40 Reports)** if not already seeded.

---

## Walkthrough Steps

### Step 1: Submit a New High-Hazard Citizen Complaint (1 Minute)
1. In the sidebar, select **Report an issue**.
2. In the **Mangaluru City Landmarks** panel on the right, click **Kadri North School Gate** (automatically populates Area `Kadri Hills` and Coordinates: `12.8945`, `74.8619`).
3. Enter the following realistic complaint description:
   ```text
   A deep open crater in the road has exposed a broken culvert right in front of the school gate. Two children nearly fell in this morning. Immediate danger!
   ```
4. Select Category: **Road damage**.
5. Click **Submit Complaint to CityGuard**.
6. **Key Highlights to Observe**:
   - The green confirmation card displays an official tracking token (e.g. `CIVIC-XXXX-XXXX`). **Copy or note this token.**
   - **Rule-based Category**: Correctly identified as `Road damage` with matched evidence keywords (`crater`, `road`).
   - **Extractive Summary**: Accurately extracts the primary hazard sentence without hallucination.
   - **Explainable Priority**: Assigned **High (80/100)**:
     - Immediate Physical Hazard (+60 pts)
     - Sensitive Community Setting - School (+20 pts)
   - **Semantic Duplicate Warning**: Highlights nearby existing complaints in Kadri Hills within 150m.

---

### Step 2: Officer Dashboard & Area Action Brief (1.5 Minutes)
1. In the sidebar, select **Officer dashboard**.
2. Point out the clear disclaimer: *“Demo officer view — authentication is not implemented.”*
3. **Inspect the KPI Metrics**:
   - Total Reports: 41
   - High-Priority Open: Prominently tracked in red
   - Needs Review: Flagged complaints requiring human verification
4. **Inspect the Area-Level Grouping & Action Brief**:
   - Select **Maple Riverside** from the area dropdown.
   - Observe the computed brief:
     > *Operational Brief: Maple Riverside currently has 8 active submissions (representing 6 unique issue clusters). There is a notable concentration of 4 drainage / waterlogging reports. Recommend dispatching a coordinated Drainage field inspection team to resolve these concurrently.*
   - Note that confirmed duplicate clusters are counted once in the unique issue metric, preventing distorted resource allocation.
5. **Inspect the Map & Queue**:
   - Filter by Priority: **High**.
   - Observe the table sorted by effective priority (High to Low, then oldest first).

---

### Step 3: Triage, Duplicate Linking & Status Transition (1.5 Minutes)
1. Scroll down to the **Officer Triage & Review Console**.
2. Select the report just submitted in Step 1 (or Report #1).
3. **Review Semantic Duplicates**:
   - In the right-hand column under **Semantic Duplicate Review**, inspect the suggested nearby report (e.g. Report #4 or #2).
   - Click **Confirm Link**. Notice that the duplicate relationship is confirmed and logged in the audit trail without destructive merging.
4. **Assign Department**:
   - Select Department: **Roads**.
5. **Update Workflow Status**:
   - Select Status: **In progress**.
   - Note: Try setting to *Resolved* without a note to demonstrate the validation guard.
   - Select Status: **In progress**, add note: *"Road maintenance crew dispatched with asphalt patch vehicle."*
   - Ensure *Make note visible to citizen* is checked.
   - Click **Update Workflow**.
6. The report updates immediately and writes an immutable entry into `status_events`.

---

### Step 4: Citizen Progress Tracking (1 Minute)
1. In the sidebar, select **Track my report**.
2. Paste the tracking token saved from Step 1.
3. Click **Check Status**.
4. **Key Highlights to Observe**:
   - Status badge shows **In progress** in purple.
   - Assigned Department displays **Roads**.
   - **Coordinated Response Notice**: Informs the citizen that their report has been linked with a confirmed related report for joint resolution.
   - **Public Progress Timeline**: Shows the chronological sequence of events:
     - 1. Complaint submitted and recorded.
     - 2. Assigned to Roads department.
     - 3. Status updated to In progress with the crew dispatch note.
   - **Privacy Guarantee**: Any internal officer notes are strictly hidden from this public view.
