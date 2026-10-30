# CivicAction: Prototype Limitations & Architectural Disclosures

CivicAction is an explainable civic complaint triage prototype built for a solo civic-impact hackathon. To ensure transparency, this document details what is authentic, what is rule-based, experimental defaults, and operational boundaries.

---

## 1. What Is Real vs. Rule-Based vs. Demo-Only

### Real Implementations
- **Relational Persistence**: Real SQLite database (`data/civicaction.db`) with `PRAGMA foreign_keys = ON;`, parameterized SQL, atomic transactions, and strict ISO UTC timestamps.
- **Geographic Distance**: Pure Python standard library implementation of the great-circle Haversine formula yielding distance in metres.
- **Semantic Embeddings**: Uses `sentence-transformers` (`all-MiniLM-L6-v2`) to encode complaint text into 384-dimensional dense vectors and computes exact cosine similarity.
- **Lifecycle & Audit Log**: Every submission, department assignment, priority override, and status change creates an immutable event in `status_events`.
- **Integrity Validation**: The database and application strictly reject status transitions to `Assigned`/`In progress` without an assigned department, and reject transition to `Resolved` without a public resolution note.
- **Citizen Privacy**: The citizen tracking view strictly filters out internal officer notes (`is_public = 0`) and never exposes tokens belonging to other citizens.

### Rule-Based Implementations
- **Categorization**: Transparent dictionary of domain keywords and phrases across 5 civic categories (`Road damage`, `Waste`, `Drainage / waterlogging`, `Streetlights / electrical`, `Water supply`). When keywords conflict or are absent, the system flags the report as `Other` with `needs_review = True`.
- **Extractive Summarization**: Pure sentence scoring based on indicator terms; selects the most salient issue sentence from the citizen's original text. It does not use generative AI or invent facts.
- **Priority Scoring**: Transparent additive policy (+60 for immediate physical hazard, +20 for sensitive setting, +20 for critical access disruption; capped at 100).
- **Negation Handling**: Conservative regular expressions identify phrases such as *"no hazard"*, *"not dangerous"*, and *"repaired, no hazard"*, preventing unwarranted high-priority scores and flagging uncertain cases for human triage.

### Demo-Only Elements
- **Municipal Geography**: Mapped to real municipal zones of Mangaluru, Karnataka (*Hampankatta*, *Kadri Hills*, *Lalbagh - Ladyhill*, *Kankanady - Pumpwell*, *Surathkal - Kulai*) with anchor coordinates.
- **No Third-Party Legacy ERP Integrations**: Official MCC back-office enterprise ERP or billing systems are simulated via the SQLite/Supabase data model.

---

## 2. Experimental Thresholds (Not Municipal Standards)

The duplicate detection parameters are experimental demonstration settings:
- **Cosine Similarity Threshold**: `0.80` (A score of 0.84 is a mathematical cosine similarity in vector space, **not** an 84% probability of duplication).
- **Geographic Proximity**: `150 metres` (Calculated via Haversine).
- **Temporal Window**: `7 days`.

These thresholds have not been empirically validated on longitudinal municipal datasets and must be calibrated to specific municipal operational densities before any production deployment.

---

## 3. Scope & Environmental Dependencies

1. **Basemap Dependency**:
   - The dashboard map component utilizes Streamlit's native map, which fetches OpenStreetMap basemap tiles over HTTPS.
   - If internet access is unavailable or tiles fail to load, the application provides an explicit on-screen disclosure; the priority triage queue, area grouping metrics, and operational briefs remain fully functional without the map.
2. **Embedding Model Download**:
   - Downloading `sentence-transformers/all-MiniLM-L6-v2` requires an initial network connection (~90MB). Once downloaded, all embeddings and inference execute strictly on local CPU.
   - If the model is offline or uninstalled, the application catches the exception gracefully, flags semantic duplicate detection as unavailable in the UI, and preserves the complaint without data loss.
3. **Language Limitations**:
   - The rule lexicon and MiniLM-L6 model are configured for English text. Submissions in other languages or regional dialects will fall back to `Other` with `needs_review = True`.
4. **Resolved Report Exclusion**:
   - Resolved complaints are excluded from active duplicate candidate suggestions in this MVP to prevent officers from linking active issues to closed work orders.

---

## 4. Human-in-the-Loop Requirement

CivicAction is an **assistive triage tool**, not an autonomous decision maker:
- Machine similarity suggestions are never merged or deleted automatically.
- Every duplicate relationship must be explicitly confirmed or rejected by a municipal officer.
- Priority overrides require a mandatory written justification recorded in the permanent audit trail.
