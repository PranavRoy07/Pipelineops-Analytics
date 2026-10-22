"""
PipelineOps Storage Module
Manages PostgreSQL and SQLite database connections, schema migrations,
audit tracking, and batch loading of normalized dimensional tables.
"""

import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

logger = logging.getLogger("PipelineOps.Storage")


class DatabaseManager:
    """Intelligent dual-engine storage manager supporting PostgreSQL and SQLite."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        storage_cfg = self.config.get("storage", {})

        # Priority: 1. Env DATABASE_URL (Postgres) -> 2. SQLite local file
        self.db_url = os.getenv("DATABASE_URL", "").strip()
        self.is_postgres = self.db_url.startswith("postgresql://") or self.db_url.startswith("postgres://")

        if self.is_postgres:
            self.engine_type = "PostgreSQL"
            logger.info("DatabaseManager initialized using PostgreSQL.")
        else:
            self.engine_type = "SQLite"
            raw_path = storage_cfg.get("default_sqlite_path", "clean_data/pipelineops.db")
            # Resolve relative to project root
            base_dir = Path(__file__).resolve().parent.parent
            self.sqlite_path = base_dir / raw_path
            self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"DatabaseManager initialized using SQLite: {self.sqlite_path}")

    def get_connection(self):
        """Returns a database connection object."""
        if self.is_postgres:
            import psycopg2
            return psycopg2.connect(self.db_url)
        else:
            conn = sqlite3.connect(str(self.sqlite_path))
            conn.row_factory = sqlite3.Row
            return conn

    def init_database(self, sql_dir: Optional[Path] = None) -> None:
        """Applies DDL schema and analytical views."""
        base_dir = Path(__file__).resolve().parent.parent
        sql_dir = sql_dir or (base_dir / "sql")

        schema_file = sql_dir / "schema.sql"
        views_file = sql_dir / "views.sql"

        logger.info(f"Initializing database ({self.engine_type})...")
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Execute schema DDL
            if schema_file.exists():
                with open(schema_file, "r", encoding="utf-8") as f:
                    schema_sql = f.read()
                if self.is_postgres:
                    # Minor dialect adjustment if needed
                    schema_sql = schema_sql.replace("JULIANDAY", "EXTRACT(EPOCH FROM")
                for statement in schema_sql.split(";"):
                    stmt = statement.strip()
                    if stmt:
                        cursor.execute(stmt)
                logger.info("Schema DDL applied successfully.")

            # Execute Views
            if views_file.exists():
                with open(views_file, "r", encoding="utf-8") as f:
                    views_sql = f.read()
                for statement in views_sql.split(";"):
                    stmt = statement.strip()
                    if stmt:
                        try:
                            cursor.execute(stmt)
                        except Exception as e:
                            logger.warning(f"Note applying view statement: {e}")
                logger.info("Analytical views created successfully.")

            conn.commit()

    def record_pipeline_run_start(self, run_id: str, stage: str = "INGESTION") -> None:
        """Records initial pipeline run execution in audit table."""
        now = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO pipeline_runs 
                (run_id, pipeline_name, status, stage, started_at)
                VALUES (?, ?, ?, ?, ?)
                """ if not self.is_postgres else """
                INSERT INTO pipeline_runs 
                (run_id, pipeline_name, status, stage, started_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (run_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    stage = EXCLUDED.stage;
                """,
                (run_id, "pipelineops", "RUNNING", stage, now)
            )
            conn.commit()

    def record_pipeline_run_finish(
        self,
        run_id: str,
        status: str,
        stage: str,
        duration_seconds: float,
        records_ingested: int,
        records_transformed: int,
        quality_passed: bool,
        error_message: Optional[str] = None
    ) -> None:
        """Updates pipeline run completion status in audit table."""
        now = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE pipeline_runs SET
                    status = ?,
                    stage = ?,
                    completed_at = ?,
                    duration_seconds = ?,
                    records_ingested = ?,
                    records_transformed = ?,
                    quality_passed = ?,
                    error_message = ?
                WHERE run_id = ?
                """ if not self.is_postgres else """
                UPDATE pipeline_runs SET
                    status = %s,
                    stage = %s,
                    completed_at = %s,
                    duration_seconds = %s,
                    records_ingested = %s,
                    records_transformed = %s,
                    quality_passed = %s,
                    error_message = %s
                WHERE run_id = %s
                """,
                (status, stage, now, duration_seconds, records_ingested,
                 records_transformed, quality_passed, error_message, run_id)
            )
            conn.commit()

    def record_raw_ingestion(
        self,
        ingestion_id: str,
        run_id: str,
        source: str,
        api_endpoint: str,
        http_status: int,
        raw_file_path: str,
        raw_record_count: int,
        payload_hash: Optional[str] = None
    ) -> None:
        """Records a Bronze ingestion batch in raw_job_ingestions."""
        now = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO raw_job_ingestions
                (ingestion_id, run_id, source, api_endpoint, http_status, 
                 raw_file_path, payload_hash_sha256, raw_record_count, ingested_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """ if not self.is_postgres else """
                INSERT INTO raw_job_ingestions
                (ingestion_id, run_id, source, api_endpoint, http_status, 
                 raw_file_path, payload_hash_sha256, raw_record_count, ingested_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ingestion_id) DO NOTHING;
                """,
                (ingestion_id, run_id, source, api_endpoint, http_status,
                 raw_file_path, payload_hash, raw_record_count, now)
            )
            conn.commit()

    def load_clean_data(self, df_jobs: pd.DataFrame, df_skills_bridge: pd.DataFrame) -> int:
        """Batch loads Silver/Gold transformed records and bridge table."""
        if df_jobs.empty:
            logger.warning("No records to load into fact_job_postings.")
            return 0

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Upsert Companies
            companies = df_jobs[["company_name", "location"]].drop_duplicates().to_dict(orient="records")
            for comp in companies:
                c_id = f"comp_{abs(hash(comp['company_name'])) % 10000000}"
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO dim_companies (company_id, company_name, primary_location)
                    VALUES (?, ?, ?)
                    """ if not self.is_postgres else """
                    INSERT INTO dim_companies (company_id, company_name, primary_location)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (company_name) DO NOTHING;
                    """,
                    (c_id, comp["company_name"], comp.get("location"))
                )

            # 2. Upsert Fact Job Postings
            job_tuples = [
                (
                    row["job_id"], row["run_id"], row["job_title"], row.get("normalized_title", row["job_title"]),
                    row["company_name"], row.get("category", "Tech"), row.get("seniority_level", "Mid"),
                    row.get("remote_type", "Fully Remote"), row.get("location"),
                    row.get("salary_min"), row.get("salary_max"), row.get("salary_avg"),
                    row.get("currency", "USD"), row.get("is_salary_predicted", False),
                    row.get("job_url", ""), row.get("repost_status", "original"),
                    row["posted_at"], row["ingested_at"]
                )
                for _, row in df_jobs.iterrows()
            ]

            insert_fact_sql = (
                """
                INSERT OR REPLACE INTO fact_job_postings
                (job_id, run_id, job_title, normalized_title, company_name, category,
                 seniority_level, remote_type, location, salary_min, salary_max,
                 salary_avg, currency, is_salary_predicted, job_url, repost_status,
                 posted_at, ingested_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """ if not self.is_postgres else """
                INSERT INTO fact_job_postings
                (job_id, run_id, job_title, normalized_title, company_name, category,
                 seniority_level, remote_type, location, salary_min, salary_max,
                 salary_avg, currency, is_salary_predicted, job_url, repost_status,
                 posted_at, ingested_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (job_id) DO UPDATE SET
                    salary_avg = EXCLUDED.salary_avg,
                    repost_status = EXCLUDED.repost_status;
                """
            )
            cursor.executemany(insert_fact_sql, job_tuples)

            # 3. Upsert Skills Bridge
            if not df_skills_bridge.empty:
                bridge_tuples = list(zip(df_skills_bridge["job_id"], df_skills_bridge["skill_name"]))
                insert_bridge_sql = (
                    """
                    INSERT OR IGNORE INTO job_skills_bridge (job_id, skill_name)
                    VALUES (?, ?)
                    """ if not self.is_postgres else """
                    INSERT INTO job_skills_bridge (job_id, skill_name)
                    VALUES (%s, %s)
                    ON CONFLICT (job_id, skill_name) DO NOTHING;
                    """
                )
                cursor.executemany(insert_bridge_sql, bridge_tuples)

            conn.commit()
            logger.info(f"Loaded {len(job_tuples)} fact jobs and {len(df_skills_bridge)} skill links into {self.engine_type}.")
            return len(job_tuples)

    def query_df(self, query: str) -> pd.DataFrame:
        """Executes a SELECT query and returns pandas DataFrame."""
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn)
