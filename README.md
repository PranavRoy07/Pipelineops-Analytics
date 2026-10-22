<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=venom&color=0:0B192C,45:2563EB,100:F97316&height=260&section=header&text=PipelineOps&fontSize=72&fontColor=FFFFFF&fontAlignY=38&desc=Tech%20Labor%20Market%20Intelligence&descAlignY=60&descSize=21&animation=twinkling" alt="PipelineOps animated header" width="100%" />
</p>

<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=700&size=20&duration=2600&pause=900&color=2563EB&center=true&vCenter=true&width=900&lines=Live+API+%E2%86%92+Bronze+%E2%86%92+Silver+%E2%86%92+Quality+Gates+%E2%86%92+Insights;Every+refresh+turns+job+listings+into+market+signals;172+jobs+%C2%B7+26+companies+%C2%B7+901+skill+links;9%2F9+quality+gates+passed+%E2%9C%85;Reliable+data.+Honest+analysis.+Confident+decisions." alt="Animated PipelineOps tagline" />

<br />

<a href="https://pipelineops-analytics-klmnopqr.streamlit.app/">
  <img src="https://img.shields.io/badge/%F0%9F%9A%80%20LIVE%20DEMO-Open%20the%20Dashboard-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Open the live PipelineOps dashboard" height="46" />
</a>

<br /><br />

<p>
  <img src="https://img.shields.io/badge/Python-Pipeline-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/SciPy-Statistics-8CAAE6?style=for-the-badge&logo=scipy&logoColor=white" alt="SciPy" />
  <img src="https://img.shields.io/badge/SQLite-Serving%20Layer-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite" />
  <img src="https://img.shields.io/badge/Power%20BI-Executive%20Report-F2C811?style=for-the-badge&logo=powerbi&logoColor=111827" alt="Power BI" />
  <img src="https://img.shields.io/badge/Streamlit-Live%20App-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit" />
</p>
<p>
  <img src="https://img.shields.io/badge/Airflow-DAG%20Ready-017CEE?style=for-the-badge&logo=apacheairflow&logoColor=white" alt="Airflow" />
  <img src="https://img.shields.io/badge/pytest-Tested-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white" alt="pytest" />
  <img src="https://img.shields.io/badge/Quality%20Gates-9%2F9%20Passed-16A34A?style=for-the-badge" alt="9 of 9 quality gates" />
  <img src="https://img.shields.io/badge/Last%20Verified-22%20Oct%202026-F97316?style=for-the-badge" alt="Last verified 22 October 2026" />
</p>

<p>
  <a href="#-live-demo"><b>Live demo</b></a> ·
  <a href="#-the-story"><b>Story</b></a> ·
  <a href="#-architecture"><b>Architecture</b></a> ·
  <a href="#-dashboard-gallery"><b>Gallery</b></a> ·
  <a href="#-run-it-locally"><b>Run locally</b></a> ·
  <a href="#-data-quality--statistics"><b>Quality</b></a> ·
  <a href="#-limitations--honest-caveats"><b>Caveats</b></a>
</p>

</div>

<p align="center">
  <img src="assets/pipeline-flow.svg" alt="Animated data flow: Ingest, Bronze, Transform, Quality Gates, Analyse, Dashboards" width="100%" />
</p>

> **PipelineOps** turns changing job-market listings into a repeatable analytics product: **ingest → preserve → transform → validate → analyse → present.**

---

## 🔴 Live Demo

<div align="center">

### 👉 [**pipelineops-analytics-klmnopqr.streamlit.app**](https://pipelineops-analytics-klmnopqr.streamlit.app/) 👈

<a href="https://pipelineops-analytics-klmnopqr.streamlit.app/">
  <img src="https://img.shields.io/badge/▶%20Launch%20PipelineOps%20Live-Streamlit%20Cloud-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Launch live dashboard" />
</a>

</div>

> [!TIP]
> Free Streamlit apps go to sleep when idle. If you see a "wake up" screen, click the button and give it about 30 seconds.

| Tab | What to try | Question it answers |
| --- | --- | --- |
| **Skill trends** | Compare week-over-week movers | Which skills are rising or falling? |
| **Compensation** | Filter by seniority and category | Which roles and skills pay the most? |
| **Companies** | Sort by posting volume and repost rate | Who is hiring, and who keeps reposting? |
| **Workplace mix** | Track remote / hybrid / on-site over time | How are workplace preferences shifting? |
| **Pipeline health** | Open run history and quality results | Can I trust this data? |

---

## 📖 The story

Job-market information is only useful when it is current, reliable, and easy to explore. PipelineOps collects jobs from a live source, protects the original pull in a bronze layer, builds analysis-ready tables, blocks bad data with quality gates, produces a statistical insight, and delivers it in both **Power BI** and **Streamlit**.

| ❓ Question | 🎯 Decision supported |
| --- | --- |
| Which skills are trending up or down week over week? | Prioritise learning and hiring skills. |
| Which roles and skills pay the most? | Benchmark compensation and career paths. |
| Which companies post the most jobs and how often do they repost? | Identify active employers and repeat-posting behaviour. |
| How does remote, hybrid, and on-site demand change over time? | Track workplace preference shifts. |

### 📌 Latest verified run

Snapshot from the verified project output on **22 October 2026**. Re-run the pipeline to refresh.

<div align="center">

| 💼 Unique jobs | 🏢 Companies | 🔗 Skill-job links | ✅ Quality gates | 🏆 Quality score |
| :---: | :---: | :---: | :---: | :---: |
| **172** | **26** | **901** | **9 / 9** | **100%** |

| 🐍 Python demand trend | Slope | p-value | R² |
| :---: | :---: | :---: | :---: |
| Statistically significant decline | **-0.355 listings/day** | **0.0080** | **0.316** |

</div>

<details>
<summary><strong>🛠️ What makes this an engineering project, not just a dashboard?</strong></summary>

<br />

- The raw API response is retained before any transformation.
- Stages are explicit: ingestion → transformation → validation → statistical analysis → storage.
- A run history records timing, status, records processed, and quality outcome.
- The dashboard reads the cleaned analytical layer, never the raw source.
- One curated dataset powers both the Power BI report and the Streamlit app.

</details>

---

## 🏗️ Architecture

```mermaid
flowchart LR
    A["🌐 Remotive API\nLive job listings"] --> B["🥉 Raw layer\nJSON daily partitions"]
    B --> C["⚙️ Python transform\nClean · dedupe · enrich"]
    C --> D["✅ Quality gates\n9 automated checks"]
    D --> E["📈 Statistical analysis\nSciPy regression"]
    E --> F["🥈 Curated layer\nFact + bridge tables"]
    F --> G["🗄️ SQLite / optional S3"]
    G --> H["📊 Power BI\n4-page executive report"]
    G --> I["🖥️ Streamlit\nLive analytics app"]

    classDef source fill:#0EA5E9,stroke:#0369A1,color:#fff
    classDef process fill:#7C3AED,stroke:#5B21B6,color:#fff
    classDef quality fill:#16A34A,stroke:#166534,color:#fff
    classDef output fill:#F97316,stroke:#C2410C,color:#fff
    class A,B source
    class C,E,F,G process
    class D quality
    class H,I output
```

### 🔄 The pipeline, step by step

| Stage | What happens | Key output |
| --- | --- | --- |
| **01 · Ingest** | Calls the job API with retry, backoff, logging, and failure handling. | Untouched JSON in `raw_data/` |
| **02 · Preserve** | Keeps the bronze source partitioned by ingestion date. | Reproducible source history |
| **03 · Transform** | Standardises dates, salary, workplace type, skills, company details, and repost flags. | `fact_jobs.csv` + `job_skills_bridge.csv` |
| **04 · Validate** | Checks row count, uniqueness, nulls, schema, and salary bounds. | `quality_report.json` |
| **05 · Analyse** | Runs linear regression on job demand and salary/skill relationships. | `statistical_insights.json` |
| **06 · Serve** | Writes analytical data for Power BI and Streamlit. | SQLite tables and clean CSVs |
| **07 · Orchestrate** | Supports one-off, scheduled, and Airflow DAG execution. | Run history and alert-ready logs |

---

## 🖼️ Dashboard gallery

The Power BI report is a narrative: **market pulse → skills → compensation → employers and workplace mix**. Source report: [`powerbi/PipelineOPS.pbix`](powerbi/PipelineOPS.pbix).

<table>
<tr>
<td width="50%" valign="top">

#### 01 · Executive overview
<img src="assets/Overview.png" alt="Power BI executive overview page" width="100%" />

Market baseline: jobs tracked, average salary, remote share, company count, in-demand skills, and posting volume.

</td>
<td width="50%" valign="top">

#### 02 · Skill demand & growth
<img src="assets/Trends.png" alt="Power BI skill demand and growth trajectory page" width="100%" />

Week-over-week skill changes, top-five daily demand pattern, and skill concentration.

</td>
</tr>
<tr>
<td width="50%" valign="top">

#### 03 · Compensation benchmarks
<img src="assets/intelligence.png" alt="Power BI compensation intelligence page" width="100%" />

Salary by seniority, best-paying skills, category and workplace comparisons, high-paying roles.

</td>
<td width="50%" valign="top">

#### 04 · Hiring cadence & remote shift
<img src="assets/company%26%20workplace.png" alt="Power BI company hiring cadence and remote work shift page" width="100%" />

High-volume employers, reposting rate, posting cadence, and remote/hybrid/on-site mix over time.

</td>
</tr>
</table>

> [!NOTE]
> **Power BI refresh:** open the `.pbix`, then **Home → Refresh** before presenting so it uses the latest curated CSVs.

---

## 🧬 Data model

```mermaid
erDiagram
    FACT_JOBS ||--o{ JOB_SKILLS_BRIDGE : "has skills"
    FACT_JOBS }o--|| DIM_COMPANIES : "posted by"
    JOB_SKILLS_BRIDGE }o--|| DIM_SKILLS : "references"
    PIPELINE_RUNS ||--o{ RAW_JOB_INGESTIONS : "records"

    FACT_JOBS {
        string job_id PK
        string job_title
        string company_name
        string category
        string seniority_level
        string remote_type
        decimal salary_avg
        boolean is_salary_predicted
        datetime posted_at
        string post_status
    }
    JOB_SKILLS_BRIDGE {
        string job_id FK
        string skill_name FK
    }
    DIM_COMPANIES {
        string company_name PK
    }
    DIM_SKILLS {
        string skill_name PK
    }
```

| Layer | Main asset | Why it exists |
| --- | --- | --- |
| 🥉 **Bronze** | `raw_data/` | Immutable source pulls; no transformation applied. |
| 🥈 **Silver** | `clean_data/fact_jobs.csv` | One cleaned row per job listing. |
| 🥈 **Silver** | `clean_data/job_skills_bridge.csv` | Many-to-many job-to-skill relationship for correct skill measures. |
| 🗄️ **Serving** | `clean_data/pipelineops.db` | Persistent storage for dashboards and run metadata. |
| 📊 **Presentation** | `powerbi/` and `dashboard/` | Executive reporting and self-service exploration. |

---

## 📁 Repository map

```text
pipelineops/
├── assets/                  # Dashboard screenshots + animated pipeline SVG
├── aws/                     # Optional S3/IAM deployment artefacts
├── clean_data/              # Curated CSVs, quality report, statistical insights
├── dags/                    # Airflow DAG definition
├── dashboard/               # Streamlit application
├── docs/                    # Data dictionary, insights, resume bullet
├── powerbi/                 # PipelineOPS.pbix, DAX library, dashboard blueprint
├── python/                  # Ingestion, transform, quality, storage, scheduler
├── raw_data/                # Untouched bronze API pulls
├── sql/                     # Database schema and analytical views
├── tests/                   # Automated pipeline tests
├── config.yaml              # Runtime configuration
├── requirements.txt         # Python dependencies
└── README.md                # You are here
```

---

## ⚡ Run it locally

<details open>
<summary><strong>1 · Prepare Python and configuration</strong></summary>

```powershell
git clone <your-repository-url>
cd pipelineops
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` only if you change storage, cloud, or alert settings. Keep secrets out of source control.

</details>

<details open>
<summary><strong>2 · Build the first historical dataset</strong></summary>

```powershell
python python/orchestrator.py --seed --seed-days 30
```

Produces historical trend data in addition to the live pull, then runs transform, quality, statistics, and storage.

</details>

<details>
<summary><strong>3 · Run the dashboard</strong></summary>

```powershell
streamlit run dashboard/app.py
```

</details>

<details>
<summary><strong>4 · Run checks before sharing</strong></summary>

```powershell
pytest tests/test_pipeline.py -v
```

</details>

<details>
<summary><strong>5 · Schedule it</strong></summary>

```powershell
python python/scheduler.py --run-once                      # run once now
python python/scheduler.py --interval-hours 24             # refresh daily
python python/scheduler.py --interval-seconds 60           # quick local test
```

</details>

<details>
<summary><strong>Useful run variants</strong></summary>

```powershell
python python/orchestrator.py --no-live                    # reprocess existing raw partitions
python python/orchestrator.py --seed --seed-days 60        # more historical seed data
```

</details>

---

## 🛡️ Data quality & statistics

### Automated quality gates

The pipeline does not silently hand bad data to the dashboard.

| Gate | Protection |
| --- | --- |
| Row-count threshold | Detects unexpectedly small pulls. |
| Primary-key uniqueness | Prevents duplicate job IDs. |
| Required-field null checks | Requires job ID, title, company, posted date, and workplace type. |
| Schema validation | Detects missing or unexpected structural changes. |
| Salary-range validation | Flags compensation outside configured realistic bounds. |

### Statistical insight

The analysis uses `scipy.stats.linregress` instead of reading a trend off a chart. The latest verified output shows a **downward Python-listing trend of 0.355 listings/day** (**p = 0.0080**, **R² = 0.316**), presented as a qualified, reproducible finding, not a causal conclusion.

---

## ⚠️ Limitations & honest caveats

- **Single source:** data comes from one job API, so it reflects that board's listings, not the whole market.
- **Small sample:** 172 listings across 26 companies is enough for a demonstration, not for market-wide claims.
- **Short window:** the trend regression uses a limited date range; treat it as indicative and re-run as history grows.
- **Correlation, not causation:** a falling Python listing count does not mean Python demand is falling market-wide.
- **Predicted salaries:** rows flagged `is_salary_predicted` are estimates, not posted figures.

---

## 🧭 Analytics experiences

| Experience | Best for | Location |
| --- | --- | --- |
| 📊 **Power BI** | Executive storytelling and presentation-ready reporting | [`powerbi/PipelineOPS.pbix`](powerbi/PipelineOPS.pbix) |
| 🖥️ **Streamlit (live)** | Interactive investigation and pipeline health | [Open the live dashboard](https://pipelineops-analytics-klmnopqr.streamlit.app/) · [`dashboard/app.py`](dashboard/app.py) |
| 📘 **Data dictionary** | Field definitions and engineered columns | [`docs/data_dictionary.md`](docs/data_dictionary.md) |
| 🧮 **DAX library** | Rebuilding or reviewing Power BI measures | [`powerbi/dax_measures.dax`](powerbi/dax_measures.dax) |
| 🗺️ **Dashboard blueprint** | Visual-by-visual build specification | [`powerbi/dashboard_blueprint.md`](powerbi/dashboard_blueprint.md) |

---

## ⚙️ Configuration, storage & deployment

- **API:** Remotive job API, configured in `config.yaml`.
- **Storage:** SQLite by default; the storage layer can use a configured database connection.
- **Cloud:** optional S3 support in `python/s3_uploader.py`, with assets in `aws/`.
- **Orchestration:** lightweight local scheduler or the Airflow DAG in `dags/`.
- **Observability:** runs, record counts, duration, stage status, and quality result are persisted.
- **Alerts:** configuration-driven; add approved email or webhook settings before enabling.
- **Hosting:** the Streamlit app is deployed on [Streamlit Community Cloud](https://pipelineops-analytics-klmnopqr.streamlit.app/).

---

## 📚 Project documentation

| Document | What it helps you explain |
| --- | --- |
| [`docs/insights.md`](docs/insights.md) | Numbers-first findings from the current dataset. |
| [`docs/data_dictionary.md`](docs/data_dictionary.md) | How raw and engineered fields should be interpreted. |
| [`docs/resume_bullet.md`](docs/resume_bullet.md) | A concise resume-ready project statement. |
| [`sql/schema.sql`](sql/schema.sql) | Relational design, keys, and storage schema. |
| [`dags/pipelineops_dag.py`](dags/pipelineops_dag.py) | Airflow orchestration design. |

---

<div align="center">

### Built to make a changing job market explainable.

**PipelineOps = reliable ingestion + traceable data quality + honest analysis + clear decisions.**

<a href="https://pipelineops-analytics-klmnopqr.streamlit.app/">
  <img src="https://img.shields.io/badge/▶%20See%20it%20live-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="See it live" />
</a>

<sub>Refresh the pipeline. Refresh Power BI. Tell the next market story.</sub>

</div>

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:F97316,55:2563EB,100:0B192C&height=120&section=footer&animation=twinkling" alt="Animated footer" width="100%" />
</p>
