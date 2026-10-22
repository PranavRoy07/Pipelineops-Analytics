# PipelineOps — build-ready Power BI dashboard blueprint

## Data inputs and model

Load only the clean layer, never `raw_data`:

| Power BI query name | File | Grain | Required types |
|---|---|---|---|
| `fact_jobs` | `clean_data/fact_jobs.csv` | one unique job posting | `posted_at`, `ingested_at`: Date/Time; salaries: decimal; `is_salary_predicted`: True/False |
| `job_skills_bridge` | `clean_data/job_skills_bridge.csv` | one job-skill pair | both fields: text |
| `quality_report` (optional) | `clean_data/quality_report.json` | one data-quality run | expand `checks` only for a hidden health detail page |

The current sample has 171 jobs, 897 skill tags, 25 companies and 23 skills across 18 Aug–30 Sep 2026. Trend measures must therefore be anchored to the latest loaded date, not `TODAY()`.

Create the `Posted Date` calculated column and `Date` table in `dax_measures.dax`; mark `Date[Date]` as the date table and sort `Date[Month]` by `Date[Month No]`.

| From | To | Cardinality | Filter direction |
|---|---|---:|---|
| `Date[Date]` | `fact_jobs[Posted Date]` | 1:* | Single |
| `fact_jobs[job_id]` | `job_skills_bridge[job_id]` | 1:* | Both |

The bidirectional job-skill relationship is deliberate: selecting a skill must filter jobs, pay, company, and workplace. Do not create relationships on company, category, or date between these two imports.

## Report-wide design

- Canvas: **16:9, custom 1280 × 720 px**; gutter 16 px; snap-to-grid on.
- Background `#F8FAFC`, visual fill `#FFFFFF`, border `#E2E8F0` at 1 px, 8 px radius.
- Navy `#0B192C`, orange `#F97316`, green `#10B981`, red `#EF4444`, slate `#64748B`.
- Font Segoe UI: title 24 px, visual title 14 px, KPI 28 px, label 10–11 px. Turn visual headers off.
- Header on every page: title at **X32 Y26 W780 H28**, `[Data Window Label]` at **X1000 Y28 W240 H24**, divider **X16 Y72 W1248 H1**.
- Put measures in a dedicated Measures table and organize folders: Core, Skills, Compensation, Company, Workplace.

## Page 1 — Executive overview

Use it to establish scale, compensation, workplace mix and statistical evidence.

| Visual | X | Y | W | H | Fields / configuration |
|---|---:|---:|---:|---:|---|
| KPI Jobs tracked | 16 | 96 | 288 | 92 | Card `[Total Jobs]`; subtitle “unique cleaned postings” |
| KPI Avg salary | 320 | 96 | 288 | 92 | Card `[Avg Salary USD]`; `$#,0` |
| KPI Remote share | 624 | 96 | 288 | 92 | Card `[Remote Ratio]`; `0.0%` |
| KPI Companies | 928 | 96 | 336 | 92 | Card `[Unique Companies]` |
| Insight banner | 16 | 204 | 1248 | 72 | Text: “Python demand: −0.517 listings/day (p=0.0033, R²=0.39). Statistically significant downward trend.” Source: `statistical_insights.json`; orange left edge. |
| Top skills | 16 | 292 | 592 | 196 | Clustered bar: Y skill, X `[Total Jobs]`; Top 10; navy; sort descending. |
| Workplace mix | 624 | 292 | 300 | 196 | Donut: Legend remote type, Values `[Total Jobs]`; Remote navy, Hybrid orange, On-site slate; show count + %. |
| Daily posting volume | 940 | 292 | 324 | 196 | Area: X `Date[Date]` continuous; Y `[Total Jobs]`; navy, 25% transparency. |
| Recent opportunities | 16 | 504 | 1248 | 200 | Table: title, company, category, seniority, remote type, salary avg, posted date; Top 10, newest first. |

Add a `category` dropdown at **X1000 Y76 W264 H32**. A hidden report-level date filter is enough for this overview.

## Page 2 — Skill demand trends (Q1)

| Visual | X | Y | W | H | Fields / configuration |
|---|---:|---:|---:|---:|---|
| Skill slicer | 16 | 88 | 300 | 44 | Dropdown skill, search enabled |
| Seniority slicer | 332 | 88 | 240 | 44 | Dropdown seniority |
| Date slicer | 588 | 88 | 420 | 44 | Between `Date[Date]` |
| Baseline note | 1024 | 94 | 240 | 32 | “Trend baseline: latest loaded date” |
| Growth ranking | 16 | 152 | 500 | 260 | Bar: Y skill, X `[WoW Skill Growth]`; Top 10 by current 7-day mentions; colour by `[WoW Growth Colour]`; 0.0%. |
| Skill demand over time | 532 | 152 | 732 | 260 | Line: X date; Y `[Skill Mentions]`; legend skill; visual Top 5 skills by mentions. |
| Emerging/declining | 16 | 428 | 620 | 276 | Table: skill, current 7D, previous 7D, WoW growth; conditional icons; sort growth descending. |
| Skill concentration | 652 | 428 | 612 | 276 | Treemap: Group skill, Values `[Total Jobs]`; Top 12. This is defensible with the available CSVs; a skill-pair heatmap is not. |

## Page 3 — Compensation intelligence (Q2)

Salary includes estimates. Put `is_salary_predicted` in the filter pane and use `[Predicted Salary Share]` in a tooltip.

| Visual | X | Y | W | H | Fields / configuration |
|---|---:|---:|---:|---:|---|
| KPI Top paid skill | 16 | 96 | 400 | 84 | Card `[Top Paid Skill]`, tooltip `[Avg Salary USD]` |
| KPI Senior premium | 432 | 96 | 400 | 84 | Card `[Senior Salary Premium]`, `+$#,0;-$#,0` |
| KPI Remote premium | 848 | 96 | 416 | 84 | Card `[Remote Salary Premium]`, fully remote vs on-site |
| Salary by seniority | 16 | 200 | 500 | 240 | Column: X seniority, Y avg salary; sort descending; `$0K`. |
| Highest-paying skills | 532 | 200 | 732 | 240 | Bar: Y skill, X avg salary; Top 12 by total jobs, then sort salary descending. |
| Category × workplace | 16 | 456 | 620 | 248 | Matrix: Rows category; Columns remote type; Values avg salary and total jobs. |
| Opportunity detail | 652 | 456 | 612 | 248 | Table: title, company, seniority, salary, predicted flag, location. Do not add bridge skills here, as that duplicates job rows. |

## Page 4 — Company activity and workplace shift (Q3 + Q4)

| Visual | X | Y | W | H | Fields / configuration |
|---|---:|---:|---:|---:|---|
| KPI Top hiring company | 16 | 96 | 400 | 84 | Card `[Top Hiring Company]` |
| KPI Repost ratio | 432 | 96 | 400 | 84 | Card `[Repost Ratio]`, 0.0% |
| KPI Posting cadence | 848 | 96 | 416 | 84 | Card `[Company Posting Cadence Days]`; “days between posts” |
| Company hiring volume | 16 | 200 | 592 | 240 | Stacked bar: Y company, X total jobs, Legend repost status; Top 10; original navy/repost orange. |
| Workplace mix by week | 624 | 200 | 640 | 240 | 100% stacked column: X week start; Legend remote type; Y total jobs. |
| Company activity | 16 | 456 | 592 | 248 | Matrix rows company; total jobs, repost jobs, repost ratio, posting cadence; Top 15. |
| Remote ratio trend | 624 | 456 | 640 | 248 | Line: X week start; Y remote ratio; 0%; navy line with markers. |

## Build and test order

1. Load the two CSVs, set types and relationships, then create the Date objects and measures from `dax_measures.dax`.
2. Build Page 1 first. Its cards should reconcile to **171 jobs**, **25 companies**, and **93 remote / 49 hybrid / 29 on-site** before styling the other pages.
3. Copy the common header, then build Pages 2–4 from the exact coordinates above.
4. Test a Python selection, a date selection and a company-bar click. Jobs, salary and workplace visuals should cross-filter, while `[Total Jobs]` stays de-duplicated through `DISTINCTCOUNT(job_id)`.
5. Before publishing, add alt text, hide technical IDs, parameterize the source file path, and schedule refresh only when a gateway or database endpoint can reach the clean layer.

Keep `quality_report.json` on an optional hidden detail page/tooltip. The four main pages should stay focused on the roadmap’s business questions while the 9/9 quality result remains audit evidence.
