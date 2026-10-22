# PipelineOps — Orchestrated Analytics Pipeline

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://pipelineops-analytics-klmnopqr.streamlit.app/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Data Quality](https://img.shields.io/badge/Data%20Quality-100%25%20Passed-brightgreen.svg)]()
[![Power BI](https://img.shields.io/badge/Power%20BI-4%20Dashboard%20Pages-F2C811.svg)](powerbi/PipelineOPS.pbix)

🌐 **Live Production Dashboard:** [https://pipelineops-analytics-klmnopqr.streamlit.app/](https://pipelineops-analytics-klmnopqr.streamlit.app/)

> An end-to-end production data engineering pipeline ingesting live job-market data via REST API on a daily schedule, storing raw and transformed layers in SQLite/PostgreSQL, running 9 automated data-quality checks, computing statistically significant trend analysis (scipy.stats.linregress), and delivering an interactive Streamlit + Power BI dashboard.

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [Business Questions](#business-questions)
4. [Quick Start (5 minutes)](#quick-start)
5. [Running the Pipeline](#running-the-pipeline)
6. [Running the Dashboard](#running-the-dashboard)
7. [Running Tests](#running-tests)
8. [Phase-by-Phase Guide](#phase-by-phase-guide)
9. [Data Quality Gates](#data-quality-gates)
10. [Statistical Analysis](#statistical-analysis)
11. [Power BI Integration](#power-bi-integration)
12. [Resume Bullet](#resume-bullet)

---

## Architecture Overview

```
Remotive / RemoteOK API
         │
         ▼ (Phase 2: Exponential backoff retry)
┌─────────────────────┐
│   Bronze Layer       │  raw_data/YYYY-MM-DD/run_<ts>.json
│   (Immutable Pulls)  │  Untouched raw JSON, partitioned daily
└─────────────────────┘
         │
         ▼ (Phase 5: Pandas Transform + Skill Extraction)
┌─────────────────────┐
│   Silver / Gold      │  clean_data/fact_jobs.parquet + .csv
│   (Dimensional Model)│  clean_data/job_skills_bridge.csv
└─────────────────────┘
         │
         ├──► SQLite / PostgreSQL  (fact tables + analytical views)
         ├──► Data Quality Report  (clean_data/quality_report.json)
         ├──► Statistical Insights (clean_data/statistical_insights.json)
         └──► AWS S3               (optional Bronze + Silver archival)
                    │
                    ▼ (Phase 6: Dashboard)
         ┌──────────────────┐   ┌──────────────┐
         │ Streamlit App    │   │  Power BI    │
         │ (dashboard/app.py)│   │  (powerbi/)  │
         └──────────────────┘   └──────────────┘
```

**Orchestration:** APScheduler (daily 03:00 UTC) with Apache Airflow DAG fallback  
**Alerting:** Slack/Discord webhook · SMTP email · Console — no silent failures

---

## Project Structure

```
pipelineops/
├── raw_data/                   ← Immutable Bronze partitions (YYYY-MM-DD/)
├── clean_data/                 ← Silver/Gold datasets + reports + DB
│   ├── fact_jobs.csv
│   ├── fact_jobs.parquet
│   ├── job_skills_bridge.csv
│   ├── pipelineops.db          ← SQLite warehouse
│   ├── quality_report.json
│   └── statistical_insights.json
├── sql/
│   ├── schema.sql              ← DDL (PostgreSQL & SQLite)
│   └── views.sql               ← 4 business-question analytical views
├── python/
│   ├── ingestion.py            ← Phase 2: API pull + Bronze storage
│   ├── seed_history.py         ← 30-day realistic historical generator
│   ├── transform.py            ← Phase 5: Pandas ETL + skill extraction
│   ├── quality.py              ← Phase 5: 9 automated quality gates
│   ├── stats_insight.py        ← Phase 5: scipy.stats.linregress
│   ├── storage.py              ← Phase 3: PostgreSQL / SQLite layer
│   ├── s3_uploader.py          ← Phase 3: AWS S3 Bronze/Silver archival
│   ├── alerting.py             ← Phase 4: Slack/Email/Console alerts
│   ├── orchestrator.py         ← Phase 4: Master pipeline chain
│   └── scheduler.py            ← Phase 4: APScheduler daily runner
├── dags/
│   └── pipelineops_dag.py      ← Phase 4: Apache Airflow DAG
├── dashboard/
│   └── app.py                  ← Phase 6: Streamlit interactive dashboard
├── powerbi/
│   ├── schema_guide.md         ← Power BI connection + setup guide
│   └── dax_measures.dax        ← Ready-to-import DAX measures
├── aws/
│   └── iam_least_privilege_policy.json  ← S3 IAM policy with AES-256
├── docs/
│   ├── data_dictionary.md      ← Full field-level documentation
│   ├── insights.md             ← 5 numbers-first analytical bullets
│   └── resume_bullet.md        ← TL-ready resume + LinkedIn copy
├── tests/
│   └── test_pipeline.py        ← pytest test suite (7 test classes)
├── config.yaml                 ← Centralized configuration
├── .env.example                ← Environment variable template
└── requirements.txt            ← Python dependencies
```

---

## Business Questions

| # | Question | SQL View | Dashboard Tab |
|---|---|---|---|
| Q1 | Which skills are trending up in demand week over week? | `v_skill_trends_wow` | Skill Trends WoW |
| Q2 | Which roles pay the most for your current skill set? | `v_top_paying_roles_by_skill` | Top Paying Roles |
| Q3 | Which companies post the most listings, and how often do they repost? | `v_company_reposting_cadence` | Company Reposts |
| Q4 | How does remote vs on-site demand shift over time? | `v_remote_vs_onsite_shift` | Remote Shift |

---

## Quick Start

### Prerequisites
- Python 3.9+
- Windows, macOS, or Linux

### 1. Install Dependencies
```bash
cd pipelineops
pip install -r requirements.txt
```

### 2. Run the Full Pipeline (with 30-day historical seed)
```bash
python python/orchestrator.py --seed --seed-days 30
```

This single command will:
- Create SQLite database and all tables/views
- Generate 30 days of realistic historical Bronze partitions
- Pull live jobs from Remotive API (with retry)
- Transform and normalize all data (Pandas)
- Run all 9 data quality gates
- Compute scipy.stats.linregress statistical insights
- Load the current curated job listings into the warehouse

### 3. Launch the Dashboard
```bash
streamlit run dashboard/app.py
```

- **Local:** Open `http://localhost:8501` in your browser.
- **Live Deployed App:** Visit [https://pipelineops-analytics-klmnopqr.streamlit.app/](https://pipelineops-analytics-klmnopqr.streamlit.app/)

---

## Running the Pipeline

### Single one-off run
```bash
python python/orchestrator.py
```

### Seed historical data only (no live API call)
```bash
python python/orchestrator.py --seed --seed-days 30 --no-live
```

### Daily scheduled run (APScheduler)
```bash
python python/scheduler.py --interval-hours 24
```

### Quick test run every 60 seconds
```bash
python python/scheduler.py --interval-seconds 60
```

### Single scheduled run and exit
```bash
python python/scheduler.py --run-once
```

---

## Running the Dashboard

```bash
streamlit run dashboard/app.py
```

**Dashboard tabs:**
- **Q1 Skill Trends** — Weekly skill demand line chart + rising skills leaderboard
- **Q2 Highest Paying Roles** — Salary box plots, category bars, skill×seniority heatmap
- **Q3 Company Reposts** — Hiring company bar chart + repost rate scatter
- **Q4 Remote Shift** — Daily stacked area + weekly remote ratio trend
- **Pipeline Health** — Quality scorecard + SciPy regression report + run history

---

## Running Tests

```bash
pytest tests/test_pipeline.py -v
```

Covers:
- Seed history generation and Bronze partition structure
- Ingestion retry logic (mocked HTTP) and raw payload preservation
- Transformation: schema, deduplication, seniority, salary parsing, skills extraction
- Data quality: pass/fail gates, null injection, duplicate detection, report persistence
- Statistical insights: linregress output keys and numeric types
- Storage: SQLite initialization, pipeline run audit recording
- Alerting: disabled flag respect, console dispatch

---

## Phase-by-Phase Guide

### Phase 1 — Scope & Source
Data source: [Remotive API](https://remotive.com/api/remote-jobs) — real job listings refreshed daily. 4 business questions are documented in [docs/insights.md](docs/insights.md).

### Phase 2 — Ingestion (Bronze)
`python/ingestion.py` — HTTP client with:
- 3 retries with exponential backoff (factor 2x) + random jitter
- Immutable daily partition storage: `raw_data/YYYY-MM-DD/run_<ts>.json`
- SHA-256 payload hash stored in metadata for immutability verification

### Phase 3 — Storage
`python/storage.py` — Auto-detects `DATABASE_URL` env var:
- **PostgreSQL** if `DATABASE_URL=postgresql://...`
- **SQLite** fallback: `clean_data/pipelineops.db` (zero-config, works immediately)

Set up PostgreSQL:
```bash
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pipelineops
```

AWS S3 (optional):
```bash
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
```
Then set `s3.enabled: true` in `config.yaml`.

### Phase 4 — Orchestration & Alerting
`python/scheduler.py` — APScheduler with native fallback.

Slack alerting: Add webhook URL to `config.yaml`:
```yaml
alerting:
  channel: webhook
  webhook_url: https://hooks.slack.com/services/your/webhook/here
```

Apache Airflow: Copy `dags/pipelineops_dag.py` to your Airflow DAGs folder.

### Phase 5 — Transform & Quality
`python/transform.py` — 40+ skill taxonomy extraction, salary normalization, seniority detection.  
`python/quality.py` — 9 automated gates emit `clean_data/quality_report.json`.  
`python/stats_insight.py` — `scipy.stats.linregress` Python demand trend.

### Phase 6 — Dashboard
`dashboard/app.py` — Full Streamlit app answering Q1–Q4.  
`powerbi/` — DAX measures + step-by-step PBI setup guide.

---

## Data Quality Gates

| Gate | Check | Failure Threshold |
|---|---|---|
| `row_count_threshold` | Minimum ingested records | < 10 records |
| `row_count_drop_sanity` | Drop vs prior run | > 50% drop |
| `primary_key_uniqueness` | No duplicate `job_id` | Any duplicate |
| `null_check_job_id` | No nulls in `job_id` | Any null |
| `null_check_job_title` | No nulls in `job_title` | Any null |
| `null_check_company_name` | No nulls in `company_name` | Any null |
| `null_check_posted_at` | No nulls in `posted_at` | Any null |
| `schema_drift_detection` | All expected columns present | Any missing column |
| `salary_value_bounds` | Salary in [$15k, $600k] | Any out-of-range value |

---

## Statistical Analysis

Using `scipy.stats.linregress` on daily Python job posting frequency over the 30-day window:

```python
from scipy import stats
slope, intercept, r_value, p_value, std_err = stats.linregress(day_index, daily_mention_count)
# slope:   -0.3551 (listings/day)
# p_value: 0.0080  (< 0.05 → statistically significant)
# R²:      0.316   (31.6% of variance explained)
```

**Latest interpretation:** Python postings show a statistically significant downward trend of 0.355 listings per day (p = 0.0080). This describes the observed sample; it does not claim a cause for the change.

---

## Power BI Integration

See [powerbi/schema_guide.md](powerbi/schema_guide.md) for step-by-step connection guide.  
Import DAX measures from [powerbi/dax_measures.dax](powerbi/dax_measures.dax).

Open the completed report: [powerbi/PipelineOPS.pbix](powerbi/PipelineOPS.pbix).

### Power BI Dashboard Pages

**1. Executive Overview**

![PipelineOps Power BI executive overview](assets/Overview.png)

**2. Skill Demand & Growth Trajectory**

![PipelineOps Power BI skills trends](assets/Trends.png)

**3. Compensation Benchmarks & Highest-Paying Skills**

![PipelineOps Power BI compensation intelligence](assets/intelligence.png)

**4. Company Hiring Cadence & Remote Work Shift**

![PipelineOps Power BI company and workplace analysis](assets/company%26%20workplace.png)

---

## Resume Bullet

> Built an orchestrated data pipeline ingesting live job-market data via API on a daily schedule (APScheduler / Apache Airflow); stored raw and transformed layers in PostgreSQL / SQLite following Bronze→Silver→Gold medallion architecture; added 9 automated data-quality checks; delivered a Power BI + Streamlit dashboard with reproducible scipy.stats.linregress trend analysis.

See [docs/resume_bullet.md](docs/resume_bullet.md) for full LinkedIn copy and interview talking points.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Data Transform | Pandas, NumPy |
| Statistical Analysis | SciPy (stats.linregress) |
| Storage | SQLite (default) / PostgreSQL |
| ORM / SQL | SQLAlchemy + raw SQL |
| Orchestration | APScheduler + Apache Airflow |
| Cloud Storage | AWS S3 (boto3, IAM least-privilege) |
| Dashboard | Streamlit + Plotly |
| BI Tool | Power BI (DAX measures included) |
| Testing | pytest (7 test classes, 22+ test cases) |
| Configuration | YAML + python-dotenv |
