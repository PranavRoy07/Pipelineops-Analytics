"""
PipelineOps Data Quality Module (Phase 5)
Executes automated data quality gates: null checks, duplicate detection,
row-count sanity thresholds, schema-drift detection, and value bounds validation.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

logger = logging.getLogger("PipelineOps.Quality")

EXPECTED_SCHEMA = {
    "job_id": "object",
    "run_id": "object",
    "job_title": "object",
    "company_name": "object",
    "category": "object",
    "seniority_level": "object",
    "remote_type": "object",
    "salary_min": "float64",
    "salary_max": "float64",
    "salary_avg": "float64",
    "posted_at": "object",
}


class DataQualityValidator:
    """Production quality gate ensuring data integrity before loading into warehouse/dashboard."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        q_cfg = self.config.get("quality_gates", {})
        self.min_records = q_cfg.get("min_record_threshold", 10)
        self.max_drop_ratio = q_cfg.get("max_allowed_drop_ratio", 0.50)
        self.max_null_pct = q_cfg.get("max_null_pct", {
            "job_id": 0.0,
            "job_title": 0.0,
            "company_name": 0.0,
            "posted_at": 0.0,
            "remote_type": 0.0
        })
        base_dir = Path(__file__).resolve().parent.parent
        self.report_path = base_dir / "clean_data" / "quality_report.json"

    def validate(self, df_jobs: pd.DataFrame, previous_count: Optional[int] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Runs all quality gates on the transformed dataset.
        Returns (passed_bool, detailed_report_dict).
        """
        logger.info(f"Running Data Quality validation on {len(df_jobs)} records...")
        checks = []
        now_str = datetime.now(timezone.utc).isoformat()

        # 1. Row Count Sanity Check
        row_count = len(df_jobs)
        passed_min_rows = row_count >= self.min_records
        checks.append({
            "check_name": "row_count_threshold",
            "passed": passed_min_rows,
            "actual": row_count,
            "expected": f">= {self.min_records}",
            "description": f"Verifies dataset has at least {self.min_records} records."
        })

        # 2. Drop Ratio Check (against previous run)
        if previous_count and previous_count > 0:
            drop_ratio = (previous_count - row_count) / float(previous_count)
            passed_drop = drop_ratio <= self.max_drop_ratio
            checks.append({
                "check_name": "row_count_drop_sanity",
                "passed": passed_drop,
                "actual": f"{drop_ratio * 100:.1f}% drop",
                "expected": f"<= {self.max_drop_ratio * 100:.1f}% drop",
                "description": "Flags abnormal data ingestion drop compared to prior baseline."
            })

        # 3. Duplicate Primary Key Check
        if not df_jobs.empty and "job_id" in df_jobs.columns:
            dupes = int(df_jobs["job_id"].duplicated().sum())
            passed_dupes = (dupes == 0)
            checks.append({
                "check_name": "primary_key_uniqueness",
                "passed": passed_dupes,
                "actual": f"{dupes} duplicates",
                "expected": "0 duplicates",
                "description": "Verifies all job_id primary keys are strictly unique."
            })

        # 4. Critical Column Null Checks
        for col, max_allowed in self.max_null_pct.items():
            if col in df_jobs.columns:
                null_count = int(df_jobs[col].isnull().sum())
                null_pct = round((null_count / max(row_count, 1)) * 100.0, 2)
                passed_null = (null_pct <= max_allowed)
                checks.append({
                    "check_name": f"null_check_{col}",
                    "passed": passed_null,
                    "actual": f"{null_pct}% null ({null_count} rows)",
                    "expected": f"<= {max_allowed}% null",
                    "description": f"Ensures mandatory field '{col}' contains no missing values."
                })
            else:
                checks.append({
                    "check_name": f"null_check_{col}",
                    "passed": False,
                    "actual": "Column missing",
                    "expected": f"Column '{col}' present",
                    "description": f"Mandatory column '{col}' missing from schema."
                })

        # 5. Schema Drift Detection
        missing_cols = [c for c in EXPECTED_SCHEMA if c not in df_jobs.columns]
        passed_schema = len(missing_cols) == 0
        checks.append({
            "check_name": "schema_drift_detection",
            "passed": passed_schema,
            "actual": f"Missing: {missing_cols}" if missing_cols else "All standard columns present",
            "expected": "Zero missing expected schema columns",
            "description": "Validates schema drift against baseline contracts."
        })

        # 6. Value Bounds Check (Salaries)
        if "salary_avg" in df_jobs.columns and not df_jobs.empty:
            salaries = df_jobs["salary_avg"].dropna()
            out_of_bounds = int(((salaries < 15000) | (salaries > 600000)).sum())
            passed_bounds = (out_of_bounds == 0)
            checks.append({
                "check_name": "salary_value_bounds",
                "passed": passed_bounds,
                "actual": f"{out_of_bounds} out-of-range rows",
                "expected": "0 rows outside [$15k, $600k]",
                "description": "Ensures salary calculations fall within realistic economic ranges."
            })

        # Summarize Results
        total_checks = len(checks)
        passed_count = sum(1 for c in checks if c["passed"])
        overall_passed = (passed_count == total_checks)
        quality_score = round((passed_count / total_checks) * 100.0, 1)

        report = {
            "validated_at": now_str,
            "overall_status": "PASSED" if overall_passed else "FAILED",
            "quality_score_pct": quality_score,
            "total_checks": total_checks,
            "passed_checks": passed_count,
            "failed_checks": total_checks - passed_count,
            "record_count_evaluated": row_count,
            "checks": checks
        }

        # Persist report
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        if overall_passed:
            logger.info(f"[PASS] Data Quality PASSED ({quality_score}% | {passed_count}/{total_checks} checks passed).")
        else:
            logger.warning(f"[FAIL] Data Quality FAILED ({quality_score}% | {total_checks - passed_count} checks failed).")

        return overall_passed, report
