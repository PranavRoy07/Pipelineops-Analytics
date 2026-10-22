# PipelineOps — Resume & LinkedIn Bullets

## Primary Resume Bullet (Full Version)

> Built an orchestrated data pipeline ingesting live job-market data via API on a daily schedule (APScheduler / Apache Airflow); stored raw and transformed layers in PostgreSQL / SQLite following a Bronze→Silver→Gold medallion architecture; added 9 automated data-quality checks (null, deduplication, schema drift, row-count bounds); delivered a Power BI + Streamlit dashboard with scipy.stats.linregress trend analysis producing statistically significant findings (p < 0.01, R² = 0.54).

---

## Short Bullet (for tighter resume real estate)

> Orchestrated daily analytics pipeline (Python · Airflow · PostgreSQL · Power BI); Bronze/Silver/Gold medallion storage; 9 automated quality gates; scipy linear regression trend cards.

---

## LinkedIn Project Description

**PipelineOps — Orchestrated Job Market Analytics Pipeline**

End-to-end production data engineering project covering 6 phases of the modern analytics stack:

- **Phase 1–2 (Ingestion):** Python script hitting Remotive / RemoteOK REST APIs with exponential backoff retries, jittered timeout logic, and structured logging on every run. Bronze layer stores unmodified raw JSON partitions under `raw_data/YYYY-MM-DD/`.
- **Phase 3 (Storage):** Dual-engine storage supporting **PostgreSQL** (production) and **SQLite** (local zero-config). Star schema with fact and dimension tables, foreign key relationships, and analytical views (WoW skill trends, salary by skill, company reposting, remote shift).
- **Phase 4 (Orchestration):** Daily schedule via **APScheduler** with an **Apache Airflow DAG** ready for enterprise deployment. Multi-channel failure alerting (Slack webhook, SMTP email, console logs) — no silent 3 AM failures.
- **Phase 5 (Transform & Quality):** Pandas ETL: salary normalization, skill extraction (40+ tech skills taxonomy), seniority detection, deduplication. **9 automated quality gates:** null checks, duplicate detection, row-count sanity, schema drift, value bounds. **scipy.stats.linregress** regression analysis: slope, p-value, R², significance test.
- **Phase 6 (Dashboard):** Interactive **Streamlit** web app answering 4 business questions with Plotly charts, plus **Power BI** integration with ready-to-import DAX measures.

**Tech Stack:** Python 3.12 · Pandas · SciPy · SQLAlchemy · SQLite/PostgreSQL · APScheduler · Apache Airflow · Streamlit · Plotly · AWS S3 (IAM least-privilege) · Power BI · pytest

---

## Interview Talking Points

1. **Architecture decision:** Why Bronze/Silver/Gold medallion? Separation of concerns — a failed transform never corrupts the raw audit trail. Every run is idempotent.

2. **Quality gate design:** I treat the quality validator like a contract. If the schema drifts or row count drops 50%+ from baseline, the pipeline halts and fires an alert before bad data hits the dashboard.

3. **Statistical credibility:** The scipy linregress result isn't just a chart — it's a defensible statistical claim. p = 0.0011 means there's a 0.11% chance the Python demand trend is random noise. The R² = 0.54 tells us 54% of daily variation is explained by the time trend alone.

4. **Dual-engine flexibility:** I built the storage layer to auto-detect PostgreSQL via `DATABASE_URL` env var and fall back to SQLite. Same DDL, same ORM layer, zero code changes. The TL can clone this and run it immediately without spinning up a database server.
