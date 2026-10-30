# CITYGUARD 🛡️: Official Presentation & Demonstration Script
### Mangaluru City Corporation (MCC) • Smart Civic Action Portal
**Official Tagline:** *"Building a Cleaner, Safer and Smarter Mangaluru."*

---

## Executive Overview (30-Second Elevator Pitch)
> "Judges and evaluators, this is **CITYGUARD** — the Smart Civic Issue Reporting and Management Platform designed for **Mangaluru City Corporation (MCC)**.
> 
> Cities face thousands of scattered complaints every month across WhatsApp, social media, and call centers. Municipal crews get flooded with duplicate reports, high-risk emergencies get buried in backlogs, and citizens lose trust because they cannot track progress.
> 
> CITYGUARD solves this with an enterprise-grade civic platform powered by **explainable, local AI**:
> 1. It mathematically scores urgency without hallucination (+60 hazard, +20 school/hospital setting, +20 access blockage).
> 2. It detects semantic duplicates within 150 metres using local Sentence Transformers without deleting citizen tokens.
> 3. It generates Ward-Level Action Briefs that convert scattered complaints into coordinated crew dispatches."

---

## Demonstration Setup (Before Starting)
1. Ensure the application is running:
   ```powershell
   .venv\Scripts\streamlit run app.py
   ```
2. Open `http://localhost:8501` in your browser.
3. In the sidebar under **Demonstration Controls**, click **🌱 Load Mangaluru Data (40 Records)** to ensure all 5 Mangaluru municipal wards are populated with realistic complaints.

---

## 5-Minute Spoken Walkthrough Script

| Time | Section | Screen / Tab | What to Do (Actions) | What to Say (Spoken Script) |
| :--- | :--- | :--- | :--- | :--- |
| **0:00 - 0:45** | **1. Brand Identity & Live KPI Bar** | `🏠 Home` | Scroll through the Home view. Point to the shield + pin logo, MCC subhead, WhatsApp button, and the 5 KPI metric cards. | *"Welcome to CITYGUARD. Notice our modern dark navy enterprise design (#0B1220 canvas with #16243A cards) built for municipal trust. At the top, we have our official MCC brand identity, emergency WhatsApp Helpline, and our live municipal performance overview. These metrics aren't hardcoded — they calculate live from our database: total grievances, resolved cases, active dispatches, and our current resolution efficiency."* |
| **0:45 - 2:00** | **2. Citizen Reporting & Explainable AI** | `📝 Report Issue` | Click **📝 Report Issue** tab.<br><br>Click **Kadri North School Gate** in the right panel.<br><br>Point out the auto-filled coordinates (`12.8945, 74.8619`) and description.<br><br>Click **Submit Complaint to CITYGUARD**. | *"Now let's step into the shoes of a citizen in Mangaluru reporting a hazard. We've included Mangaluru landmark presets like Kadri School Gate, Lalbagh MCC Head Office, and Hampankatta Market. Clicking 'Kadri North School Gate' automatically locks in verified GPS coordinates.<br><br>When we submit, watch what happens in real-time — our local AI engine analyzes the complaint instantly. Notice the transparent AI receipt below:<br>• **Rule-Based Classification**: Matched 'Road damage' with keyword evidence tokens ('crater', 'sinkhole').<br>• **Extractive Summary**: Extracts the key issue without LLM hallucinations.<br>• **Explainable Priority**: Scored 80/100 (High Priority) because it detected an immediate physical hazard (+60 points) right in front of a school (+20 points).<br>• **Duplicate Intelligence**: It immediately flagged existing nearby reports within 150m in Kadri Hills.<br>• **Citizen Tracking Token**: Generates an official 16-character ID like `CIVIC-XXXX-XXXX`."* |
| **2:00 - 2:45** | **3. Citizen Tracking & Privacy Guarantee** | `🔍 Track Complaint` | Click **🔍 Track Complaint** tab.<br><br>Paste the tracking token from the previous step.<br><br>Click **🔎 Look Up Status**. | *"As a citizen, I don't need an account or complex login. I simply enter my unique tracking token. Immediately, I see the assigned department, current status badge, and an immutable public timeline.<br><br>Crucially, CITYGUARD enforces an enterprise **Citizen Privacy Guarantee**: internal engineering notes, contractor budgets, and citizen phone numbers are strictly scrubbed from this view — only verified public milestones are shown."* |
| **2:45 - 4:00** | **4. Live Dashboard, Clustering & Officer Triage** | `📊 Live Dashboard` | Click **📊 Live Dashboard** tab.<br><br>Select **Kadri Hills** from the Ward dropdown.<br><br>Show the Operational Brief.<br><br>Toggle **Officer / Admin Triage Drawer** in the sidebar. | *"Now let's switch to the perspective of an MCC Municipal Ward Officer on the Live Dashboard.<br><br>Notice the **Area-Level Operational Brief**: rather than presenting a chaotic list of 40 raw complaints, CITYGUARD uses graph clustering to group nearby duplicates. It tells the officer: 'Kadri Hills has 8 raw submissions, but they represent only 3 unique physical problems.' This prevents duplicate spam from distorting city budgets.<br><br>In the Officer Triage Drawer, engineers can review evidence, confirm duplicate links without deleting citizen tracking tokens, assign the responsible department (like Roads or MESCOM), and execute status transitions guarded by strict workflow rules."* |
| **4:00 - 4:45** | **5. Architecture & Technical Strength** | `ℹ️ About Us` | Click **ℹ️ About Us** tab.<br><br>Show covered wards and technical architecture details. | *"Under the hood, CITYGUARD is built with reliability and data sovereignty in mind:<br>• **Zero Paid Cloud API Dependencies**: Our semantic embeddings use a local `all-MiniLM-L6-v2` Sentence Transformer running directly on CPU.<br>• **Edge + Cloud Hybrid Architecture**: Fast local SQLite for instant triage, paired with full Supabase PostgreSQL cloud sync for municipal backups.<br>• **Automated Test Rigor**: 28 automated unit, regression, and end-to-end integration tests passing with 100% coverage."* |
| **4:45 - 5:00** | **6. Closing & Call to Action** | Back to `🏠 Home` | Return to Home view. | *"CITYGUARD bridges Mangaluru's citizens and municipal teams with transparency, speed, and explainable intelligence. It makes triage faster, prioritizes life-threatening danger first, and keeps every citizen informed.<br><br>Thank you, and we'd love to answer any questions!"* |

---

## Anticipated Questions & Strong Answers (Q&A Cheat Sheet)

### Q1: "How do you prevent the AI from making up or hallucinating priorities?"
> **Answer:** "CITYGUARD explicitly avoids generative LLM hallucination for core triage. We use a **deterministic, additive mathematical scoring engine**:
> - **+60 points** for verified danger patterns (exposed live wires, open manholes, collapsing culverts).
> - **+20 points** for sensitive community settings (schools, hospitals, transit terminals).
> - **+20 points** for total access blockage (flooded roads, impassable bridges).
> Every single point is backed by an auditable reason token. If there are conflicting signals or no keywords match, the system flags the report as `Needs Review` for human officer verification."

### Q2: "What happens when 10 different citizens report the exact same pothole?"
> **Answer:** "Traditional portals either create 10 separate work orders (wasting municipal crew time) or delete 9 of them (leaving citizens with broken tracking links).
> CITYGUARD computes 384-dimensional semantic embeddings using Sentence Transformers. Any complaints within **150 metres** and **7 days** with **≥ 0.80 cosine similarity** are flagged as duplicates. When the officer confirms the link, all 10 citizens keep their individual tracking tokens, and when the crew patches the pothole, all 10 citizens receive simultaneous progress notifications."

### Q3: "Can this scale beyond Mangaluru?"
> **Answer:** "Yes. The ward coordinates and landmark presets are stored cleanly in [config.py](file:///c:/Users/TUF/OneDrive/Documents/promptwar/config.py). Adding another municipal corporation (like Udupi, Mysuru, or Bengaluru) simply requires adding their ward boundary coordinates. Furthermore, the Supabase schema is fully cloud-native PostgreSQL ready."

### Q4: "Does this require internet or expensive cloud GPU servers?"
> **Answer:** "No. The entire AI pipeline runs locally on standard CPU hardware using lightweight Sentence Transformers and rule-based keyword tokens. It works 100% offline on a municipal edge server."
