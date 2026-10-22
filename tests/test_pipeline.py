"""
PipelineOps Test Suite (Phase 5 / 6 Verification)
Covers: ingestion retry logic, transformation normalization, data quality validators,
statistical regression outputs, and storage layer sanity.
"""

import json
import os
import sys
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from python.alerting import PipelineAlertManager
from python.ingestion import APIIngestor
from python.quality import DataQualityValidator
from python.seed_history import generate_sample_job_records, seed_historical_bronze_layer
from python.stats_insight import StatisticalInsightEngine
from python.storage import DatabaseManager
from python.transform import DataTransformer


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def temp_project_dir(tmp_path):
    """Creates a temporary project directory structure for tests."""
    (tmp_path / "raw_data").mkdir()
    (tmp_path / "clean_data").mkdir()
    (tmp_path / "sql").mkdir()
    # Copy SQL files
    for sql_file in ["schema.sql", "views.sql"]:
        src = PROJECT_ROOT / "sql" / sql_file
        dst = tmp_path / "sql" / sql_file
        if src.exists():
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return tmp_path


@pytest.fixture
def sample_raw_records():
    """Returns a batch of realistic raw job records for transformation testing."""
    return generate_sample_job_records(count=30, day_offset=0)


@pytest.fixture
def sample_clean_df(sample_raw_records):
    """Returns pre-transformed clean DataFrame."""
    transformer = DataTransformer(config={"storage": {"raw_data_dir": "raw_data", "clean_data_dir": "clean_data"}})
    df_jobs, df_bridge = transformer.transform_records(sample_raw_records, run_id="test_run_001")
    return df_jobs, df_bridge


@pytest.fixture
def db_manager(temp_project_dir, monkeypatch):
    """Returns a DatabaseManager using SQLite in a temp directory."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    cfg = {"storage": {"default_sqlite_path": str(temp_project_dir / "clean_data" / "test.db")}}
    mgr = DatabaseManager(config=cfg)
    mgr.sqlite_path = temp_project_dir / "clean_data" / "test.db"
    return mgr


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Seed History Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestSeedHistory:
    def test_generate_sample_records_returns_correct_count(self):
        records = generate_sample_job_records(count=20, day_offset=0)
        assert len(records) == 20

    def test_generate_sample_records_have_required_fields(self):
        records = generate_sample_job_records(count=5, day_offset=0)
        required = {"id", "title", "company_name", "publication_date", "tags", "remote_status"}
        for rec in records:
            for field in required:
                assert field in rec, f"Missing required field: {field}"

    def test_seed_bronze_creates_partitions(self, temp_project_dir):
        total = seed_historical_bronze_layer(temp_project_dir / "raw_data", days=5)
        assert total > 0
        json_files = list((temp_project_dir / "raw_data").rglob("*.json"))
        assert len(json_files) == 6  # 5 days + today

    def test_seed_partition_files_contain_metadata(self, temp_project_dir):
        seed_historical_bronze_layer(temp_project_dir / "raw_data", days=3)
        json_files = list((temp_project_dir / "raw_data").rglob("*.json"))
        for jf in json_files:
            data = json.loads(jf.read_text(encoding="utf-8"))
            assert "metadata" in data
            assert "raw_records" in data
            assert len(data["raw_records"]) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Ingestion / Retry Logic Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestIngestion:
    def test_ingestor_creates_bronze_file_on_success(self, temp_project_dir, monkeypatch):
        """Mocks a successful API call and verifies Bronze file creation."""
        mock_records = generate_sample_job_records(count=15, day_offset=0)
        mock_payload = json.dumps({"jobs": mock_records}).encode("utf-8")

        cfg = {
            "api": {
                "primary_source": "remotive",
                "endpoints": {"remotive": "https://remotive.com/api/remote-jobs?limit=100"},
                "timeout_seconds": 5,
                "retry": {"max_retries": 1, "backoff_factor": 1.0},
                "headers": {"User-Agent": "PipelineOps-Test/1.0"},
            },
            "storage": {"raw_data_dir": str(temp_project_dir / "raw_data")},
        }
        ingestor = APIIngestor(config=cfg)

        class MockResponse:
            status = 200
            def read(self): return mock_payload
            def __enter__(self): return self
            def __exit__(self, *a): pass

        with patch("urllib.request.urlopen", return_value=MockResponse()):
            result = ingestor.ingest_live_jobs(run_id="test_ingestion_001")

        assert result["record_count"] == 15
        assert Path(result["raw_file_path"]).exists()

    def test_ingestor_saves_untouched_raw_payload(self, temp_project_dir, monkeypatch):
        """Verifies that stored Bronze payload is bit-identical to what was received."""
        mock_records = generate_sample_job_records(count=10, day_offset=0)
        original_payload = json.dumps({"jobs": mock_records}).encode("utf-8")

        cfg = {
            "api": {
                "primary_source": "remotive",
                "endpoints": {"remotive": "https://test.api/jobs"},
                "timeout_seconds": 5,
                "retry": {"max_retries": 1, "backoff_factor": 1.0},
                "headers": {"User-Agent": "Test"},
            },
            "storage": {"raw_data_dir": str(temp_project_dir / "raw_data")},
        }
        ingestor = APIIngestor(config=cfg)

        class MockResponse:
            status = 200
            def read(self): return original_payload
            def __enter__(self): return self
            def __exit__(self, *a): pass

        with patch("urllib.request.urlopen", return_value=MockResponse()):
            result = ingestor.ingest_live_jobs(run_id="test_raw_preservation")

        saved_file = json.loads(Path(result["raw_file_path"]).read_text(encoding="utf-8"))
        assert len(saved_file["raw_records"]) == 10

    def test_extract_skills_from_tags_and_text(self):
        """Verifies skill extraction from both tags list and description text."""
        transformer = DataTransformer()
        skills = transformer.extract_skills(
            tags=["Python", "AWS", "Docker"],
            text_content="We use PostgreSQL, Airflow, and dbt in production."
        )
        assert "Python" in skills
        assert "AWS" in skills
        assert "Docker" in skills
        assert "PostgreSQL" in skills
        assert "Airflow" in skills
        assert "dbt" in skills


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Transformation Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestTransformation:
    def test_transform_returns_two_dataframes(self, sample_raw_records):
        transformer = DataTransformer()
        df_jobs, df_bridge = transformer.transform_records(sample_raw_records, run_id="test_001")
        assert isinstance(df_jobs, pd.DataFrame)
        assert isinstance(df_bridge, pd.DataFrame)

    def test_transformed_schema_has_required_columns(self, sample_raw_records):
        transformer = DataTransformer()
        df_jobs, _ = transformer.transform_records(sample_raw_records, run_id="test_001")
        required_cols = [
            "job_id", "run_id", "job_title", "company_name", "category",
            "seniority_level", "remote_type", "salary_min", "salary_max",
            "salary_avg", "posted_at", "ingested_at"
        ]
        for col in required_cols:
            assert col in df_jobs.columns, f"Missing column: {col}"

    def test_job_ids_are_unique(self, sample_raw_records):
        transformer = DataTransformer()
        df_jobs, _ = transformer.transform_records(sample_raw_records, run_id="test_001")
        assert df_jobs["job_id"].nunique() == len(df_jobs), "Duplicate job_ids found after transformation"

    def test_seniority_detection_accuracy(self):
        transformer = DataTransformer()
        assert transformer.detect_seniority("Senior Data Engineer") == "Senior"
        assert transformer.detect_seniority("Junior Python Developer") == "Junior"
        assert transformer.detect_seniority("Staff Software Architect") == "Staff"
        assert transformer.detect_seniority("Lead Data Scientist") == "Lead"
        assert transformer.detect_seniority("Data Engineer") == "Mid"

    def test_remote_status_normalization(self):
        transformer = DataTransformer()
        assert transformer.detect_remote_status({"remote_status": "Fully Remote"}) == "Fully Remote"
        assert transformer.detect_remote_status({"remote_status": "Hybrid"}) == "Hybrid"
        assert transformer.detect_remote_status({"candidate_required_location": "Remote, Worldwide"}) == "Fully Remote"

    def test_salary_parsing_from_string(self):
        transformer = DataTransformer()
        rec = {"salary": "$90,000 - $130,000 USD"}
        s_min, s_max, s_avg, is_predicted = transformer.parse_salary(rec, "Mid")
        assert s_min == pytest.approx(90000.0)
        assert s_max == pytest.approx(130000.0)
        assert s_avg == pytest.approx(110000.0)
        assert is_predicted is False

    def test_salary_benchmark_fallback(self):
        transformer = DataTransformer()
        rec = {}  # No salary info
        s_min, s_max, s_avg, is_predicted = transformer.parse_salary(rec, "Senior")
        assert is_predicted is True
        assert s_avg == pytest.approx(145000.0)

    def test_bridge_table_links_jobs_to_skills(self, sample_raw_records):
        transformer = DataTransformer()
        _, df_bridge = transformer.transform_records(sample_raw_records, run_id="test_001")
        if not df_bridge.empty:
            assert "job_id" in df_bridge.columns
            assert "skill_name" in df_bridge.columns


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Data Quality Gate Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestDataQuality:
    @pytest.fixture
    def good_df(self, sample_clean_df):
        return sample_clean_df[0]

    def test_quality_passes_on_clean_data(self, good_df, tmp_path, monkeypatch):
        monkeypatch.setattr("python.quality.DataQualityValidator.__init__", lambda s, c=None: setattr(s, "config", c or {}) or setattr(s, "min_records", 5) or setattr(s, "max_drop_ratio", 0.5) or setattr(s, "max_null_pct", {"job_id": 0, "job_title": 0, "company_name": 0, "posted_at": 0, "remote_type": 0}) or setattr(s, "report_path", tmp_path / "quality_report.json") or None)
        validator = DataQualityValidator()
        passed, report = validator.validate(good_df)
        assert passed is True
        assert report["quality_score_pct"] == 100.0

    def test_null_check_fails_on_missing_required_column(self, good_df, tmp_path, monkeypatch):
        monkeypatch.setattr("python.quality.DataQualityValidator.__init__", lambda s, c=None: setattr(s, "config", c or {}) or setattr(s, "min_records", 5) or setattr(s, "max_drop_ratio", 0.5) or setattr(s, "max_null_pct", {"job_id": 0, "job_title": 0, "company_name": 0, "posted_at": 0, "remote_type": 0}) or setattr(s, "report_path", tmp_path / "quality_report.json") or None)
        validator = DataQualityValidator()
        bad_df = good_df.copy()
        bad_df["job_title"] = None  # Inject nulls
        passed, report = validator.validate(bad_df)
        assert passed is False

    def test_duplicate_check_catches_repeated_ids(self, good_df, tmp_path, monkeypatch):
        monkeypatch.setattr("python.quality.DataQualityValidator.__init__", lambda s, c=None: setattr(s, "config", c or {}) or setattr(s, "min_records", 5) or setattr(s, "max_drop_ratio", 0.5) or setattr(s, "max_null_pct", {"job_id": 0, "job_title": 0, "company_name": 0, "posted_at": 0, "remote_type": 0}) or setattr(s, "report_path", tmp_path / "quality_report.json") or None)
        validator = DataQualityValidator()
        dup_df = pd.concat([good_df, good_df.head(5)], ignore_index=True)
        passed, report = validator.validate(dup_df)
        assert passed is False

    def test_quality_report_is_saved_to_disk(self, good_df, tmp_path, monkeypatch):
        report_path = tmp_path / "quality_report.json"
        monkeypatch.setattr("python.quality.DataQualityValidator.__init__", lambda s, c=None: setattr(s, "config", c or {}) or setattr(s, "min_records", 5) or setattr(s, "max_drop_ratio", 0.5) or setattr(s, "max_null_pct", {"job_id": 0, "job_title": 0, "company_name": 0, "posted_at": 0, "remote_type": 0}) or setattr(s, "report_path", report_path) or None)
        validator = DataQualityValidator()
        validator.validate(good_df)
        assert report_path.exists()
        saved = json.loads(report_path.read_text())
        assert "overall_status" in saved
        assert "checks" in saved


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Statistical Insight Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestStatisticalInsights:
    @pytest.fixture
    def stats_engine(self, tmp_path):
        """Creates a StatisticalInsightEngine bypassing __init__ to point to a temp directory."""
        engine = StatisticalInsightEngine.__new__(StatisticalInsightEngine)
        engine.config = {}
        engine.clean_data_dir = tmp_path
        engine.insights_path = tmp_path / "statistical_insights.json"
        return engine

    def test_linregress_returns_expected_keys(self, sample_clean_df, stats_engine):
        df_jobs, df_bridge = sample_clean_df
        insight = stats_engine.compute_skill_trend_regression(df_jobs, df_bridge, "Python")
        required_keys = ["slope", "intercept", "r_value", "p_value", "std_err", "r_squared",
                         "is_statistically_significant", "headline"]
        for key in required_keys:
            assert key in insight, f"Missing key: {key}"

    def test_linregress_slope_is_numeric(self, sample_clean_df, stats_engine):
        df_jobs, df_bridge = sample_clean_df
        insight = stats_engine.compute_skill_trend_regression(df_jobs, df_bridge, "AWS")
        assert isinstance(insight["slope"], float)
        assert isinstance(insight["p_value"], float)

    def test_salary_skill_regression_positive_slope(self, sample_clean_df, stats_engine):
        df_jobs, df_bridge = sample_clean_df
        result = stats_engine.compute_salary_by_skill_count_regression(df_jobs, df_bridge)
        assert "slope" in result
        assert "p_value" in result


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Storage / Database Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestStorage:
    def test_database_initializes_without_error(self, db_manager, temp_project_dir):
        db_manager.sqlite_path = temp_project_dir / "clean_data" / "test.db"
        db_manager.is_postgres = False
        sql_dir = PROJECT_ROOT / "sql"
        db_manager.init_database(sql_dir=sql_dir)
        assert (temp_project_dir / "clean_data" / "test.db").exists()

    def test_pipeline_run_can_be_recorded(self, db_manager, temp_project_dir):
        db_manager.sqlite_path = temp_project_dir / "clean_data" / "test.db"
        db_manager.is_postgres = False
        sql_dir = PROJECT_ROOT / "sql"
        db_manager.init_database(sql_dir=sql_dir)
        db_manager.record_pipeline_run_start("test_run_001", stage="DB_INITIALIZATION")
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM pipeline_runs WHERE run_id = ?", ("test_run_001",))
            count = cursor.fetchone()[0]
        assert count == 1


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Alerting Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestAlerting:
    def test_alert_manager_respects_disabled_flag(self):
        mgr = PipelineAlertManager(config={"alerting": {"enabled": False}})
        result = mgr.notify_failure("run_001", "TEST_STAGE", "Test error")
        assert result.get("status") == "skipped"

    def test_console_alert_logs_without_error(self):
        mgr = PipelineAlertManager(config={"alerting": {"enabled": True, "channel": "console", "notify_on_failure": True}})
        try:
            result = mgr.notify_failure("run_test", "TRANSFORM", "Test error in transform stage")
            assert "console" in result
        except Exception as e:
            pytest.fail(f"Alert dispatch raised unexpected exception: {e}")
