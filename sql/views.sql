-- ====================================================================
-- PipelineOps Analytical Views
-- Answering the 4 Core Business Questions
-- ====================================================================

-- --------------------------------------------------------------------
-- Q1: Which skills are trending up in demand week over week?
-- --------------------------------------------------------------------
DROP VIEW IF EXISTS v_skill_trends_wow;
CREATE VIEW v_skill_trends_wow AS
WITH weekly_skill_counts AS (
    SELECT
        b.skill_name,
        -- Compatible with SQLite and PostgreSQL
        strftime('%Y-W%W', f.posted_at) AS year_week,
        COUNT(DISTINCT f.job_id) AS skill_demand_count
    FROM job_skills_bridge b
    JOIN fact_job_postings f ON b.job_id = f.job_id
    GROUP BY b.skill_name, strftime('%Y-W%W', f.posted_at)
),
weekly_lagged AS (
    SELECT
        skill_name,
        year_week,
        skill_demand_count,
        LAG(skill_demand_count, 1) OVER (
            PARTITION BY skill_name 
            ORDER BY year_week ASC
        ) AS prev_week_count
    FROM weekly_skill_counts
)
SELECT
    skill_name,
    year_week,
    skill_demand_count AS current_week_mentions,
    COALESCE(prev_week_count, 0) AS previous_week_mentions,
    ROUND(
        CASE
            WHEN prev_week_count IS NULL OR prev_week_count = 0 THEN 0.0
            ELSE ((skill_demand_count - prev_week_count) * 100.0 / prev_week_count)
        END, 2
    ) AS wow_growth_pct
FROM weekly_lagged
ORDER BY year_week DESC, wow_growth_pct DESC;


-- --------------------------------------------------------------------
-- Q2: Which roles pay the most for your current skill set?
-- --------------------------------------------------------------------
DROP VIEW IF EXISTS v_top_paying_roles_by_skill;
CREATE VIEW v_top_paying_roles_by_skill AS
SELECT
    b.skill_name,
    f.category AS role_category,
    f.seniority_level,
    COUNT(f.job_id) AS sample_size,
    ROUND(AVG(f.salary_avg), 0) AS average_salary_usd,
    ROUND(MIN(f.salary_min), 0) AS min_salary_usd,
    ROUND(MAX(f.salary_max), 0) AS max_salary_usd
FROM job_skills_bridge b
JOIN fact_job_postings f ON b.job_id = f.job_id
WHERE f.salary_avg IS NOT NULL AND f.salary_avg > 0
GROUP BY b.skill_name, f.category, f.seniority_level
HAVING COUNT(f.job_id) >= 2
ORDER BY average_salary_usd DESC;


-- --------------------------------------------------------------------
-- Q3: Which companies post the most listings, and how often do they repost?
-- --------------------------------------------------------------------
DROP VIEW IF EXISTS v_company_reposting_cadence;
CREATE VIEW v_company_reposting_cadence AS
SELECT
    company_name,
    COUNT(job_id) AS total_postings,
    COUNT(DISTINCT normalized_title) AS unique_roles_posted,
    SUM(CASE WHEN repost_status = 'repost' THEN 1 ELSE 0 END) AS repost_count,
    ROUND(
        (SUM(CASE WHEN repost_status = 'repost' THEN 1 ELSE 0 END) * 100.0 / COUNT(job_id)), 1
    ) AS repost_ratio_pct,
    ROUND(
        JULIANDAY(MAX(posted_at)) - JULIANDAY(MIN(posted_at)), 1
    ) AS active_span_days,
    ROUND(
        (JULIANDAY(MAX(posted_at)) - JULIANDAY(MIN(posted_at))) / NULLIF(COUNT(job_id) - 1, 0), 1
    ) AS avg_days_between_postings
FROM fact_job_postings
GROUP BY company_name
ORDER BY total_postings DESC;


-- --------------------------------------------------------------------
-- Q4: How does remote vs on-site demand shift over time?
-- --------------------------------------------------------------------
DROP VIEW IF EXISTS v_remote_vs_onsite_shift;
CREATE VIEW v_remote_vs_onsite_shift AS
SELECT
    strftime('%Y-%m-%d', posted_at) AS posting_date,
    COUNT(job_id) AS total_jobs_posted,
    SUM(CASE WHEN remote_type = 'Fully Remote' THEN 1 ELSE 0 END) AS remote_jobs,
    SUM(CASE WHEN remote_type = 'Hybrid' THEN 1 ELSE 0 END) AS hybrid_jobs,
    SUM(CASE WHEN remote_type = 'On-site' THEN 1 ELSE 0 END) AS onsite_jobs,
    ROUND(
        (SUM(CASE WHEN remote_type = 'Fully Remote' THEN 1 ELSE 0 END) * 100.0 / COUNT(job_id)), 1
    ) AS remote_share_pct
FROM fact_job_postings
GROUP BY strftime('%Y-%m-%d', posted_at)
ORDER BY posting_date ASC;
