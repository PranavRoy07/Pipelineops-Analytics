-- ====================================================================
-- PipelineOps DDL Schema
-- Compatible with PostgreSQL and SQLite
-- ====================================================================

-- 1. Pipeline Execution Audit Log
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id VARCHAR(64) PRIMARY KEY,
    pipeline_name VARCHAR(64) NOT NULL,
    status VARCHAR(20) NOT NULL, -- SUCCESS, FAILED, RUNNING
    stage VARCHAR(32) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_seconds NUMERIC(10, 2),
    records_ingested INTEGER DEFAULT 0,
    records_transformed INTEGER DEFAULT 0,
    quality_passed BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Raw Ingestions Audit Table (Bronze Layer)
CREATE TABLE IF NOT EXISTS raw_job_ingestions (
    ingestion_id VARCHAR(64) PRIMARY KEY,
    run_id VARCHAR(64) NOT NULL,
    source VARCHAR(64) NOT NULL,
    api_endpoint TEXT NOT NULL,
    http_status INTEGER NOT NULL,
    raw_file_path TEXT NOT NULL,
    payload_hash_sha256 VARCHAR(64),
    raw_record_count INTEGER NOT NULL,
    ingested_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Dimension: Companies
CREATE TABLE IF NOT EXISTS dim_companies (
    company_id VARCHAR(64) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL UNIQUE,
    industry VARCHAR(128),
    primary_location VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Dimension: Skills
CREATE TABLE IF NOT EXISTS dim_skills (
    skill_id VARCHAR(64) PRIMARY KEY,
    skill_name VARCHAR(64) NOT NULL UNIQUE,
    skill_category VARCHAR(64) -- e.g. Programming, Database, Cloud, Orchestration
);

-- 5. Fact Table: Normalized Job Postings (Silver / Gold Layer)
CREATE TABLE IF NOT EXISTS fact_job_postings (
    job_id VARCHAR(64) PRIMARY KEY,
    run_id VARCHAR(64) NOT NULL,
    job_title VARCHAR(255) NOT NULL,
    normalized_title VARCHAR(255),
    company_name VARCHAR(255) NOT NULL,
    category VARCHAR(128),
    seniority_level VARCHAR(32), -- Junior, Mid, Senior, Lead, Staff, Unknown
    remote_type VARCHAR(32) NOT NULL, -- Fully Remote, Hybrid, On-site
    location VARCHAR(255),
    salary_min NUMERIC(12, 2),
    salary_max NUMERIC(12, 2),
    salary_avg NUMERIC(12, 2),
    currency VARCHAR(10) DEFAULT 'USD',
    is_salary_predicted BOOLEAN DEFAULT FALSE,
    job_url TEXT,
    repost_status VARCHAR(32) DEFAULT 'original',
    posted_at TIMESTAMP NOT NULL,
    ingested_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for high-performance analytical queries
CREATE INDEX IF NOT EXISTS idx_fact_jobs_posted_at ON fact_job_postings (posted_at);
CREATE INDEX IF NOT EXISTS idx_fact_jobs_company ON fact_job_postings (company_name);
CREATE INDEX IF NOT EXISTS idx_fact_jobs_remote ON fact_job_postings (remote_type);
CREATE INDEX IF NOT EXISTS idx_fact_jobs_salary_avg ON fact_job_postings (salary_avg);
CREATE INDEX IF NOT EXISTS idx_fact_jobs_category ON fact_job_postings (category);

-- 6. Bridge Table: Fact Jobs to Dimension Skills (Many-to-Many)
CREATE TABLE IF NOT EXISTS job_skills_bridge (
    job_id VARCHAR(64) NOT NULL,
    skill_name VARCHAR(64) NOT NULL,
    PRIMARY KEY (job_id, skill_name)
);

CREATE INDEX IF NOT EXISTS idx_bridge_skill_name ON job_skills_bridge (skill_name);
CREATE INDEX IF NOT EXISTS idx_bridge_job_id ON job_skills_bridge (job_id);
