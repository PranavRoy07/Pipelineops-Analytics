"""
PipelineOps Apache Airflow DAG
Production DAG defining task dependencies, retries, and failure alerts for Airflow deployments.
"""

from datetime import datetime, timedelta
import sys
from pathlib import Path

# Airflow imports with safe fallback for static analysis
try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    from airflow.operators.bash import BashOperator
except ImportError:
    # Dummy classes for environments without Airflow installed
    class DAG:
        def __init__(self, *args, **kwargs): pass
    class PythonOperator:
        def __init__(self, *args, **kwargs): pass
    class BashOperator:
        def __init__(self, *args, **kwargs): pass


default_args = {
    "owner": "data_engineering",
    "depends_on_past": False,
    "email": ["alerts@pipelineops.local"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=3),
}


def airflow_ingest_bronze(**context):
    """Airflow task: Ingest live job data to Bronze layer."""
    from python.orchestrator import PipelineOrchestrator
    orchestrator = PipelineOrchestrator()
    meta = orchestrator.ingestor.ingest_live_jobs()
    context["ti"].xcom_push(key="raw_file_path", value=meta.get("raw_file_path"))
    context["ti"].xcom_push(key="record_count", value=meta.get("record_count"))
    return meta


def airflow_transform_data(**context):
    """Airflow task: Transform raw data into Silver/Gold fact and bridge datasets."""
    from python.orchestrator import PipelineOrchestrator
    orchestrator = PipelineOrchestrator()
    run_id = context.get("run_id", f"run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
    df_jobs, df_bridge = orchestrator.transformer.process_all_bronze_partitions(run_id=run_id)
    return {"jobs_count": len(df_jobs), "skills_count": len(df_bridge)}


def airflow_quality_checks(**context):
    """Airflow task: Run automated quality gates."""
    import pandas as pd
    from python.orchestrator import PipelineOrchestrator
    orchestrator = PipelineOrchestrator()
    clean_csv = Path(__file__).resolve().parent.parent / "clean_data" / "fact_jobs.csv"
    if clean_csv.exists():
        df_jobs = pd.read_csv(clean_csv)
        passed, report = orchestrator.validator.validate(df_jobs)
        if not passed:
            raise ValueError(f"Data quality checks failed: {report['failed_checks']} checks failed.")
        return report
    raise FileNotFoundError("Clean dataset not found for quality validation.")


def airflow_compute_stats(**context):
    """Airflow task: Compute scipy.stats.linregress statistical insights."""
    import pandas as pd
    from python.orchestrator import PipelineOrchestrator
    orchestrator = PipelineOrchestrator()
    clean_dir = Path(__file__).resolve().parent.parent / "clean_data"
    df_jobs = pd.read_csv(clean_dir / "fact_jobs.csv")
    df_bridge = pd.read_csv(clean_dir / "job_skills_bridge.csv")
    return orchestrator.stats_engine.generate_all_insights(df_jobs, df_bridge)


def airflow_load_warehouse(**context):
    """Airflow task: Batch load clean data into PostgreSQL or SQLite warehouse."""
    import pandas as pd
    from python.orchestrator import PipelineOrchestrator
    orchestrator = PipelineOrchestrator()
    clean_dir = Path(__file__).resolve().parent.parent / "clean_data"
    df_jobs = pd.read_csv(clean_dir / "fact_jobs.csv")
    df_bridge = pd.read_csv(clean_dir / "job_skills_bridge.csv")
    orchestrator.db_mgr.init_database()
    loaded = orchestrator.db_mgr.load_clean_data(df_jobs, df_bridge)
    return {"loaded_records": loaded}


# Define the DAG
with DAG(
    dag_id="pipelineops_daily_orchestration",
    default_args=default_args,
    description="Daily Orchestrated Analytics Pipeline: Ingest -> Transform -> Quality -> Stats -> Warehouse",
    schedule_interval="0 3 * * *", # Daily at 03:00 UTC
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["pipelineops", "data-engineering", "job-analytics"],
) as dag:

    task_ingest = PythonOperator(
        task_id="ingest_raw_bronze",
        python_callable=airflow_ingest_bronze,
        provide_context=True,
    )

    task_transform = PythonOperator(
        task_id="transform_silver_gold",
        python_callable=airflow_transform_data,
        provide_context=True,
    )

    task_quality = PythonOperator(
        task_id="validate_data_quality",
        python_callable=airflow_quality_checks,
        provide_context=True,
    )

    task_stats = PythonOperator(
        task_id="compute_statistical_insights",
        python_callable=airflow_compute_stats,
        provide_context=True,
    )

    task_load = PythonOperator(
        task_id="load_warehouse_and_views",
        python_callable=airflow_load_warehouse,
        provide_context=True,
    )

    # Chain tasks sequentially
    task_ingest >> task_transform >> task_quality >> task_stats >> task_load
