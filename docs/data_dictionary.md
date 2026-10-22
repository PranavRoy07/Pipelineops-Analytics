# PipelineOps Data Dictionary

Complete documentation for all engineered columns in the Bronze, Silver, and Gold data layers.

---

## Bronze Layer — `raw_data/YYYY-MM-DD/run_<timestamp>.json`

Each daily Bronze partition contains:

| Field | Type | Description |
|---|---|---|
| `metadata.run_id` | string | Unique pipeline execution identifier (`run_YYYYMMDD_HHMMSS`) |
| `metadata.source` | string | API source name (`remotive`, `remoteok`, or `historical_seed`) |
| `metadata.api_endpoint` | string | Full URL called for this ingestion |
| `metadata.http_status` | integer | HTTP response status code (200 = success) |
| `metadata.ingested_at` | ISO-8601 | UTC timestamp of ingestion |
| `metadata.record_count` | integer | Number of raw job records in this partition |
| `metadata.payload_hash_sha256` | string | SHA-256 hash of the raw records for immutability verification |
| `raw_records[]` | array | Unmodified job objects as received from the API |

---

## Silver Layer — `clean_data/fact_jobs.csv` & `fact_jobs.parquet`

Core fact table. One row = one unique job posting after deduplication.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `job_id` | string (PK) | No | MD5-derived unique identifier from `company + title`. Stable across reposts. |
| `run_id` | string (FK) | No | Pipeline run that first created this record. |
| `job_title` | string | No | Raw job title as scraped from API (max 255 chars). |
| `normalized_title` | string | No | Standardized role label: `Data Engineer`, `Machine Learning Engineer`, `Software Engineer`, `BI / Data Analyst`, `DevOps / DataOps Engineer`. |
| `company_name` | string | No | Employer company name. |
| `category` | string | No | Job category from API or inferred from title: `Data Engineering`, `Cloud Infrastructure`, `Machine Learning`, `Backend`, `Business Intelligence`. |
| `seniority_level` | string | No | Detected from title keywords: `Junior`, `Mid`, `Senior`, `Lead`, `Staff`. |
| `remote_type` | string | No | Normalized work modality: `Fully Remote`, `Hybrid`, `On-site`. |
| `location` | string | Yes | Location text from listing (may be `Remote, Worldwide`). |
| `salary_min` | float | Yes | Minimum salary in USD, parsed from listing or inferred from benchmark. |
| `salary_max` | float | Yes | Maximum salary in USD. |
| `salary_avg` | float | Yes | Average of `(salary_min + salary_max) / 2`. |
| `currency` | string | No | Currency code. Always `USD` after normalization. |
| `is_salary_predicted` | boolean | No | `True` if salary was not available in the listing and was estimated from seniority benchmark. |
| `job_url` | string | Yes | Direct URL to the original job posting. |
| `repost_status` | string | No | `original` for new listings; `repost` for detected duplicate posts from the same company. |
| `posted_at` | datetime | No | ISO-8601 UTC datetime of the original listing publication. |
| `ingested_at` | datetime | No | UTC datetime when this record was first processed by the pipeline. |

---

## Silver Layer — `clean_data/job_skills_bridge.csv`

Many-to-many bridge table linking jobs to normalized skills.

| Column | Type | Description |
|---|---|---|
| `job_id` | string (FK → fact_job_postings) | Parent job reference |
| `skill_name` | string | Normalized skill name from `KNOWN_TECH_SKILLS` taxonomy (e.g. `Python`, `AWS`, `dbt`, `Kubernetes`) |

**Skill Taxonomy:**
`Python`, `SQL`, `PostgreSQL`, `AWS`, `Azure`, `GCP`, `Airflow`, `dbt`, `Snowflake`, `Spark`, `Kafka`, `Docker`, `Kubernetes`, `Terraform`, `Power BI`, `Tableau`, `React`, `FastAPI`, `Django`, `Node.js`, `Git`, `Linux`, `CI/CD`, `Pandas`, `PyTorch`, `Databricks`, `BigQuery`, `Redshift`

---

## Gold Layer — SQLite / PostgreSQL Views

### `v_skill_trends_wow`
| Column | Description |
|---|---|
| `skill_name` | Tracked technology skill |
| `year_week` | ISO year-week string (`2026-W37`) |
| `current_week_mentions` | Count of jobs mentioning this skill this week |
| `previous_week_mentions` | Count from the prior week |
| `wow_growth_pct` | Week-over-week percentage change `((curr - prev) / prev) * 100` |

### `v_top_paying_roles_by_skill`
| Column | Description |
|---|---|
| `skill_name` | Technology skill filter |
| `role_category` | Role category grouping |
| `seniority_level` | Seniority tier |
| `sample_size` | Count of data points used for averages |
| `average_salary_usd` | Mean salary USD |
| `min_salary_usd` | Minimum observed salary |
| `max_salary_usd` | Maximum observed salary |

### `v_company_reposting_cadence`
| Column | Description |
|---|---|
| `company_name` | Employer |
| `total_postings` | All job postings count |
| `unique_roles_posted` | Count of distinct normalized role titles |
| `repost_count` | Number of detected re-posted jobs |
| `repost_ratio_pct` | Repost percentage `(reposts / total) * 100` |
| `active_span_days` | Days between first and last posting |
| `avg_days_between_postings` | Estimated cadence between posts |

### `v_remote_vs_onsite_shift`
| Column | Description |
|---|---|
| `posting_date` | Daily date bucket |
| `total_jobs_posted` | All postings that day |
| `remote_jobs` | Count of Fully Remote |
| `hybrid_jobs` | Count of Hybrid |
| `onsite_jobs` | Count of On-site |
| `remote_share_pct` | `(remote_jobs / total) * 100` |

---

## Quality Report — `clean_data/quality_report.json`

| Field | Description |
|---|---|
| `validated_at` | ISO-8601 UTC timestamp of quality gate run |
| `overall_status` | `PASSED` or `FAILED` |
| `quality_score_pct` | Percentage of checks that passed |
| `total_checks` | Number of gates evaluated |
| `passed_checks` | Count that passed |
| `failed_checks` | Count that failed |
| `checks[]` | Array of individual gate results with `check_name`, `passed`, `actual`, `expected`, `description` |

---

## Statistical Insights — `clean_data/statistical_insights.json`

| Field | Description |
|---|---|
| `headline_card` | One-line statistical summary for dashboard (e.g. `+0.042 daily listings trend (p=0.0012, R²=0.88)`) |
| `primary_skill_regression.slope` | Linear regression slope (listings/day) |
| `primary_skill_regression.p_value` | Statistical significance (p < 0.05 = significant) |
| `primary_skill_regression.r_squared` | Coefficient of determination (0–1; higher = better fit) |
| `primary_skill_regression.is_statistically_significant` | Boolean: `p < 0.05` |
| `salary_skill_correlation.slope` | Salary increase per additional skill tag (USD) |
