"""
PipelineOps Master Orchestrator
Chains Phase 1-5 steps into a robust, observable data pipeline execution:
Ingest (Bronze) -> Transform (Silver/Gold) -> Quality Gates -> SciPy Stats -> DB Load -> Alerting.
"""

import argparse
import logging
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

# Support both direct script execution and package imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

try:
    from python.alerting import PipelineAlertManager
    from python.ingestion import APIIngestor
    from python.quality import DataQualityValidator
    from python.s3_uploader import S3LakeStorage
    from python.seed_history import seed_historical_bronze_layer
    from python.stats_insight import StatisticalInsightEngine
    from python.storage import DatabaseManager
    from python.transform import DataTransformer
except ImportError:
    from alerting import PipelineAlertManager
    from ingestion import APIIngestor
    from quality import DataQualityValidator
    from s3_uploader import S3LakeStorage
    from seed_history import seed_historical_bronze_layer
    from stats_insight import StatisticalInsightEngine
    from storage import DatabaseManager
    from transform import DataTransformer


logger = logging.getLogger("PipelineOps.Orchestrator")


def load_config() -> Dict[str, Any]:
    """Loads configuration from config.yaml."""
    base_dir = Path(__file__).resolve().parent.parent
    cfg_file = base_dir / "config.yaml"
    if cfg_file.exists():
        with open(cfg_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


class PipelineOrchestrator:
    """End-to-end master orchestrator coordinating all pipeline stages."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or load_config()
        self.alert_mgr = PipelineAlertManager(self.config)
        self.db_mgr = DatabaseManager(self.config)
        self.ingestor = APIIngestor(self.config)
        self.transformer = DataTransformer(self.config)
        self.validator = DataQualityValidator(self.config)
        self.stats_engine = StatisticalInsightEngine(self.config)
        self.s3_storage = S3LakeStorage(self.config)

    def run_pipeline(
        self,
        seed_history: bool = False,
        seed_days: int = 30,
        run_live: bool = True
    ) -> Dict[str, Any]:
        """Executes the end-to-end analytics pipeline."""
        start_time = time.time()
        now = datetime.now(timezone.utc)
        run_id = f"run_{now.strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"==> Starting PipelineOps Execution: {run_id}")
        current_stage = "INITIALIZATION"

        try:
            # 1. Initialize Database DDL and Views
            current_stage = "DB_INITIALIZATION"
            self.db_mgr.init_database()
            self.db_mgr.record_pipeline_run_start(run_id, stage=current_stage)

            # 2. Historical Seeding (if requested or if raw directory is empty)
            base_dir = Path(__file__).resolve().parent.parent
            raw_dir = base_dir / self.config.get("storage", {}).get("raw_data_dir", "raw_data")
            has_raw_data = any(raw_dir.rglob("*.json"))

            if seed_history or not has_raw_data:
                current_stage = "HISTORICAL_SEEDING"
                logger.info("Initializing multi-week historical Bronze partitions...")
                seed_historical_bronze_layer(raw_dir, days=seed_days)

            # 3. Live API Ingestion (Bronze Layer)
            records_ingested = 0
            if run_live:
                current_stage = "API_INGESTION"
                logger.info("Executing Phase 2: Live API Ingestion...")
                ingest_meta = self.ingestor.ingest_live_jobs(run_id=run_id)
                records_ingested = ingest_meta.get("record_count", 0)

                # Record Bronze audit entry
                self.db_mgr.record_raw_ingestion(
                    ingestion_id=f"ingest_{run_id}",
                    run_id=run_id,
                    source=ingest_meta.get("source", "remotive"),
                    api_endpoint=self.config.get("api", {}).get("endpoints", {}).get("remotive", ""),
                    http_status=ingest_meta.get("http_status", 200),
                    raw_file_path=ingest_meta.get("raw_file_path", ""),
                    raw_record_count=records_ingested,
                )

                # Optional S3 Bronze archive
                if self.s3_storage.enabled and ingest_meta.get("raw_file_path"):
                    self.s3_storage.sync_bronze_file(ingest_meta["raw_file_path"])

            # 4. Phase 5: Transform to Silver & Gold Datasets
            current_stage = "TRANSFORMATION"
            logger.info("Executing Phase 5: Transformation and Normalization...")
            df_jobs, df_bridge = self.transformer.process_all_bronze_partitions(run_id=run_id)
            records_transformed = len(df_jobs)

            # 5. Phase 5: Automated Data Quality Gates
            current_stage = "QUALITY_GATES"
            logger.info("Executing Phase 5: Data Quality validation...")
            quality_passed, q_report = self.validator.validate(df_jobs)
            if not quality_passed:
                logger.warning("Quality gates raised warnings or failures. Review quality_report.json.")

            # 6. Phase 5: Statistical Linear Regressions (scipy.stats.linregress)
            current_stage = "STATISTICAL_MODELING"
            logger.info("Executing Phase 5: Statistical Trend Analysis with SciPy...")
            stats_report = self.stats_engine.generate_all_insights(df_jobs, df_bridge)

            # 7. Phase 3: Relational Warehouse Loading
            current_stage = "WAREHOUSE_LOAD"
            logger.info("Executing Phase 3: Loading Clean Data into Relational Warehouse...")
            loaded_count = self.db_mgr.load_clean_data(df_jobs, df_bridge)

            # Optional S3 Silver archive
            if self.s3_storage.enabled:
                clean_parquet = str(base_dir / "clean_data" / "fact_jobs.parquet")
                clean_csv = str(base_dir / "clean_data" / "fact_jobs.csv")
                self.s3_storage.sync_silver_dataset(clean_parquet, clean_csv)

            # 8. Record Successful Pipeline Run
            duration = time.time() - start_time
            current_stage = "COMPLETED"
            self.db_mgr.record_pipeline_run_finish(
                run_id=run_id,
                status="SUCCESS",
                stage=current_stage,
                duration_seconds=duration,
                records_ingested=records_ingested,
                records_transformed=records_transformed,
                quality_passed=quality_passed,
                error_message=None
            )

            # Alert dispatcher (success notification)
            self.alert_mgr.notify_success(
                run_id=run_id,
                records_ingested=records_ingested,
                records_transformed=records_transformed,
                duration_seconds=duration,
                quality_score=q_report.get("quality_score_pct", 100.0)
            )

            logger.info(
                f"[SUCCESS] PipelineOps run '{run_id}' completed successfully in {duration:.2f}s! "
                f"Transformed {records_transformed:,} jobs | Quality Score: {q_report.get('quality_score_pct')}%"
            )

            return {
                "status": "SUCCESS",
                "run_id": run_id,
                "duration_seconds": round(duration, 2),
                "records_ingested": records_ingested,
                "records_transformed": records_transformed,
                "quality_passed": quality_passed,
                "headline_insight": stats_report.get("headline_card"),
            }

        except Exception as e:
            duration = time.time() - start_time
            tb = traceback.format_exc()
            logger.error(f"[ERROR] PipelineOps run '{run_id}' FAILED at stage '{current_stage}': {e}\n{tb}")

            # Record run failure in DB
            try:
                self.db_mgr.record_pipeline_run_finish(
                    run_id=run_id,
                    status="FAILED",
                    stage=current_stage,
                    duration_seconds=duration,
                    records_ingested=0,
                    records_transformed=0,
                    quality_passed=False,
                    error_message=str(e)
                )
            except Exception as db_err:
                logger.error(f"Could not record failure status to database: {db_err}")

            # Dispatch Failure Alert immediately
            self.alert_mgr.notify_failure(
                run_id=run_id,
                stage=current_stage,
                error_message=str(e),
                traceback_str=tb,
                duration_seconds=duration
            )

            raise


def main():
    parser = argparse.ArgumentParser(description="PipelineOps Master Orchestrator")
    parser.add_argument("--seed", action="store_true", help="Force multi-week historical seed data generation")
    parser.add_argument("--seed-days", type=int, default=30, help="Number of historical days to seed (default: 30)")
    parser.add_argument("--no-live", action="store_true", help="Skip live API call and only process existing partitions")
    args = parser.parse_args()

    orchestrator = PipelineOrchestrator()
    orchestrator.run_pipeline(
        seed_history=args.seed,
        seed_days=args.seed_days,
        run_live=not args.no_live
    )


if __name__ == "__main__":
    main()
