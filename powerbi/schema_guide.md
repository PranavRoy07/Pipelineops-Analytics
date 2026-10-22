# Power BI Setup Guide for PipelineOps

## Overview

This guide explains how to connect Power BI Desktop to the PipelineOps data warehouse and build the 4-question analytical model.

## Step 1: Connect to SQLite (Zero-Config) or PostgreSQL

### Option A: CSV / Parquet Files (Quickest Demo)
1. Open **Power BI Desktop**
2. Click `Get Data → Text/CSV`
3. Navigate to `clean_data/fact_jobs.csv` → Load
4. Repeat for `clean_data/job_skills_bridge.csv`

### Option B: SQLite Database
1. In Power BI Desktop: `Get Data → More... → ODBC`
2. Select the SQLite ODBC driver (install if needed: https://www.ch-werner.de/sqliteodbc/)
3. Connection string: `Driver={SQLite3 ODBC Driver};Database=C:\path\to\pipelineops\clean_data\pipelineops.db`
4. Select tables: `fact_job_postings`, `job_skills_bridge`, `dim_companies`, `pipeline_runs`

### Option C: PostgreSQL (Production)
1. `Get Data → PostgreSQL`
2. Server: `localhost`, Database: `pipelineops`
3. Load: `fact_job_postings`, `job_skills_bridge`, `dim_companies`, `pipeline_runs`
4. Switch to DirectQuery mode for real-time pipeline refreshes

---

## Step 2: Star Schema Relationship Setup

In Power BI's **Model View**, establish these relationships:

| From Table | From Column | To Table | To Column | Cardinality |
|---|---|---|---|---|
| `job_skills_bridge` | `job_id` | `fact_job_postings` | `job_id` | Many-to-One |
| `dim_companies` | `company_name` | `fact_job_postings` | `company_name` | One-to-Many |
| `pipeline_runs` | `run_id` | `fact_job_postings` | `run_id` | One-to-Many |

---

## Step 3: Import DAX Measures

Open a new **Measures Table** and copy-paste from `dax_measures.dax`. Key measures:

- `Avg Salary USD` — Average salary across filtered jobs
- `Remote Ratio %` — % of Fully Remote postings
- `WoW Skill Growth %` — Week-over-week growth for selected skill
- `Repost Frequency Days` — Average cadence between company reposts

---

## Step 4: Build the 4 Report Pages

### Page 1 — Q1: Skill Trends WoW
- **Line Chart**: X-axis = `posted_at` (Week), Y-axis = Count of `job_id`, Legend = `skill_name` (from bridge)
- **Bar Chart**: Top 10 skills sorted by `WoW Skill Growth %`
- **Slicer**: Skill Name filter

### Page 2 — Q2: Highest Paying Roles
- **Box Plot or Clustered Bar**: `seniority_level` vs `Avg Salary USD`
- **Table**: Role Category, Avg Salary, Skill, Sample Size
- **Slicer**: Skill filter (Python, AWS, SQL etc.)

### Page 3 — Q3: Company Reposting
- **Stacked Bar**: Company Name vs Total Postings, broken by `repost_status`
- **KPI Card**: Top hiring company this week
- **Table**: Company, Total Posts, Unique Roles, Repost %

### Page 4 — Q4: Remote Shift Over Time
- **Area Chart**: Date vs Count, segmented by `remote_type`
- **Pie/Donut Chart**: Current distribution (Fully Remote / Hybrid / On-site)
- **Line Chart**: Weekly remote ratio trend

---

## Step 5: Add Statistical Headline Card

1. Add a new **Card Visual**
2. Create a **Text Box** with the headline from `clean_data/statistical_insights.json`
3. Example: `-1.21 daily listings trend (p=0.0011, R²=0.54)`
4. Format with font size 20, bold, with context explanation beneath

---

## Refresh Schedule

- Set **Scheduled Refresh** to match the APScheduler interval (daily 03:00 UTC)
- Or configure **DirectQuery** to PostgreSQL for real-time dashboard updates
