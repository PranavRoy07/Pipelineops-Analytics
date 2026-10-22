"""
PipelineOps Quick Verification Script
Runs all critical pipeline tests without pytest dependencies.
"""
import sys
import json
import tempfile
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

PASS = "PASS"
FAIL = "FAIL"
results = []

def run_test(name, fn):
    try:
        fn()
        results.append((PASS, name))
        print(f"  [{PASS}] {name}")
    except Exception as e:
        results.append((FAIL, name, str(e)))
        print(f"  [{FAIL}] {name}: {e}")

tmp = Path(tempfile.mkdtemp())
os.environ.pop("DATABASE_URL", None)

# -- Imports -------------------------------------------------------------------
from python.seed_history import generate_sample_job_records, seed_historical_bronze_layer
from python.transform import DataTransformer
from python.quality import DataQualityValidator
from python.stats_insight import StatisticalInsightEngine
from python.storage import DatabaseManager
from python.alerting import PipelineAlertManager

# -- Test 1: Seed History ------------------------------------------------------
print("\n=== TEST GROUP 1: Seed History ===")
records = generate_sample_job_records(count=20, day_offset=0)

def t1a():
    assert len(records) == 20
run_test("generate_sample_records returns 20 records", t1a)

def t1b():
    required = ['id','title','company_name','publication_date','tags','remote_status']
    for r in records:
        for f in required:
            assert f in r, f"Missing {f}"
run_test("records have all required fields", t1b)

def t1c():
    raw_dir = tmp / "raw_data"
    total = seed_historical_bronze_layer(raw_dir, days=5)
    assert total > 0
    files = list(raw_dir.rglob("*.json"))
    assert len(files) == 6
run_test("seed creates 6 daily Bronze partitions (5 days + today)", t1c)

def t1d():
    raw_dir = tmp / "raw_data"
    for jf in raw_dir.rglob("*.json"):
        data = json.loads(jf.read_text())
        assert "metadata" in data
        assert "raw_records" in data
        assert len(data["raw_records"]) > 0
run_test("Bronze partition files contain metadata and records", t1d)

# -- Test 2: Transformation ----------------------------------------------------
print("\n=== TEST GROUP 2: Transformation ===")
transformer = DataTransformer()
df_jobs, df_bridge = transformer.transform_records(records, run_id="test_run_001")

def t2a():
    import pandas as pd
    assert isinstance(df_jobs, pd.DataFrame)
    assert isinstance(df_bridge, pd.DataFrame)
run_test("transform returns two DataFrames", t2a)

def t2b():
    required = ['job_id','run_id','job_title','company_name','category',
                'seniority_level','remote_type','salary_min','salary_max','salary_avg','posted_at','ingested_at']
    for col in required:
        assert col in df_jobs.columns, f"Missing column: {col}"
run_test("transformed schema has all required columns", t2b)

def t2c():
    assert df_jobs["job_id"].nunique() == len(df_jobs)
run_test("job_ids are unique (no duplicates)", t2c)

def t2d():
    t = DataTransformer()
    assert t.detect_seniority("Senior Data Engineer") == "Senior"
    assert t.detect_seniority("Junior Python Developer") == "Junior"
    assert t.detect_seniority("Staff Software Architect") == "Staff"
    assert t.detect_seniority("Lead Data Scientist") == "Lead"
    assert t.detect_seniority("Data Engineer") == "Mid"
run_test("seniority detection accuracy", t2d)

def t2e():
    t = DataTransformer()
    assert t.detect_remote_status({"remote_status": "Fully Remote"}) == "Fully Remote"
    assert t.detect_remote_status({"remote_status": "Hybrid"}) == "Hybrid"
    assert t.detect_remote_status({"candidate_required_location": "Remote, Worldwide"}) == "Fully Remote"
run_test("remote status normalization", t2e)

def t2f():
    t = DataTransformer()
    rec = {"salary": "$90,000 - $130,000 USD"}
    s_min, s_max, s_avg, is_pred = t.parse_salary(rec, "Mid")
    assert abs(s_min - 90000.0) < 1
    assert abs(s_max - 130000.0) < 1
    assert abs(s_avg - 110000.0) < 1
    assert is_pred is False
run_test("salary parsing from string", t2f)

def t2g():
    t = DataTransformer()
    rec = {}  # no salary info
    s_min, s_max, s_avg, is_pred = t.parse_salary(rec, "Senior")
    assert is_pred is True
    assert abs(s_avg - 145000.0) < 1
run_test("salary benchmark fallback when missing", t2g)

def t2h():
    t = DataTransformer()
    skills = t.extract_skills(["Python", "AWS"], "We use PostgreSQL and Airflow in production.")
    assert "Python" in skills
    assert "AWS" in skills
    assert "PostgreSQL" in skills
    assert "Airflow" in skills
run_test("skill extraction from tags and description text", t2h)

# -- Test 3: Data Quality ------------------------------------------------------
print("\n=== TEST GROUP 3: Data Quality Gates ===")

def make_validator(report_subdir="quality"):
    v = DataQualityValidator.__new__(DataQualityValidator)
    v.config = {}
    v.min_records = 5
    v.max_drop_ratio = 0.5
    v.max_null_pct = {"job_id":0,"job_title":0,"company_name":0,"posted_at":0,"remote_type":0}
    v.report_path = tmp / report_subdir / "quality_report.json"
    v.report_path.parent.mkdir(parents=True, exist_ok=True)
    return v

def t3a():
    v = make_validator("q1")
    passed, report = v.validate(df_jobs)
    assert passed is True
    assert report["quality_score_pct"] == 100.0
run_test("quality PASSES on clean data (100%)", t3a)

def t3b():
    import pandas as pd
    v = make_validator("q2")
    bad_df = df_jobs.copy()
    bad_df["job_title"] = None
    passed, _ = v.validate(bad_df)
    assert passed is False
run_test("null injection causes quality FAILURE", t3b)

def t3c():
    import pandas as pd
    v = make_validator("q3")
    dup_df = pd.concat([df_jobs, df_jobs.head(5)], ignore_index=True)
    passed, _ = v.validate(dup_df)
    assert passed is False
run_test("duplicate IDs cause quality FAILURE", t3c)

def t3d():
    v = make_validator("q4")
    v.validate(df_jobs)
    assert v.report_path.exists()
    saved = json.loads(v.report_path.read_text())
    assert "overall_status" in saved
    assert "checks" in saved
run_test("quality report is saved to disk as JSON", t3d)

# -- Test 4: Statistical Insights ----------------------------------------------
print("\n=== TEST GROUP 4: Statistical Insights ===")

def make_stats_engine():
    e = StatisticalInsightEngine.__new__(StatisticalInsightEngine)
    e.config = {}
    e.clean_data_dir = tmp / "stats"
    e.insights_path = tmp / "stats" / "statistical_insights.json"
    e.clean_data_dir.mkdir(parents=True, exist_ok=True)
    return e

def t4a():
    engine = make_stats_engine()
    insight = engine.compute_skill_trend_regression(df_jobs, df_bridge, "Python")
    required = ["slope", "intercept", "r_value", "p_value", "std_err", "r_squared",
                "is_statistically_significant", "headline"]
    for key in required:
        assert key in insight, f"Missing key: {key}"
run_test("linregress returns all expected keys", t4a)

def t4b():
    engine = make_stats_engine()
    insight = engine.compute_skill_trend_regression(df_jobs, df_bridge, "AWS")
    assert isinstance(insight["slope"], float)
    assert isinstance(insight["p_value"], float)
    assert isinstance(insight["r_squared"], float)
run_test("linregress returns numeric slope, p_value, r_squared", t4b)

def t4c():
    engine = make_stats_engine()
    result = engine.compute_salary_by_skill_count_regression(df_jobs, df_bridge)
    assert "slope" in result
    assert "p_value" in result
    assert "headline" in result
run_test("salary-skill regression returns required fields", t4c)

# -- Test 5: Storage -----------------------------------------------------------
print("\n=== TEST GROUP 5: Storage Layer ===")

def t5a():
    db_cfg = {"storage": {"default_sqlite_path": str(tmp / "test_storage.db")}}
    db = DatabaseManager(config=db_cfg)
    db.sqlite_path = tmp / "test_storage.db"
    db.is_postgres = False
    db.init_database()
    assert (tmp / "test_storage.db").exists()
run_test("SQLite database initializes without error", t5a)

def t5b():
    db_cfg = {"storage": {"default_sqlite_path": str(tmp / "test_audit.db")}}
    db = DatabaseManager(config=db_cfg)
    db.sqlite_path = tmp / "test_audit.db"
    db.is_postgres = False
    db.init_database()
    db.record_pipeline_run_start("test_run_001", stage="TEST")
    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM pipeline_runs WHERE run_id=?", ("test_run_001",))
        count = cur.fetchone()[0]
    assert count == 1
run_test("pipeline run is recorded in audit table", t5b)

# -- Test 6: Alerting ----------------------------------------------------------
print("\n=== TEST GROUP 6: Alerting ===")

def t6a():
    mgr = PipelineAlertManager(config={"alerting": {"enabled": False}})
    result = mgr.notify_failure("run_001", "TEST_STAGE", "Test error")
    assert result.get("status") == "skipped"
run_test("alerting skips when disabled flag is set", t6a)

def t6b():
    mgr = PipelineAlertManager(config={"alerting": {"enabled": True, "channel": "console",
                                                      "notify_on_failure": True, "webhook_url": ""}})
    result = mgr.notify_failure("run_test", "TRANSFORM", "Test error in transform stage")
    assert "console" in result
run_test("console alert dispatches without exception", t6b)

# -- Summary -------------------------------------------------------------------
print("\n" + "="*50)
passed = sum(1 for r in results if r[0] == PASS)
total  = len(results)
print(f"RESULTS: {passed}/{total} tests PASSED")
if passed < total:
    print("\nFailed tests:")
    for r in results:
        if r[0] == FAIL:
            print(f"  FAIL: {r[1]}: {r[2]}")
    sys.exit(1)
else:
    print("ALL TESTS PASSED!")
    sys.exit(0)
