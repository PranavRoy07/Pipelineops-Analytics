"""
PipelineOps Transformation Module (Silver & Gold Layers)
Cleans, normalizes, deduplicates raw job postings, extracts tech skills,
normalizes salary benchmarks, and exports curated analytical tables.
"""

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import pandas as pd

logger = logging.getLogger("PipelineOps.Transform")

# Comprehensive Tech Skills Taxonomy for Data, Cloud, and Software Engineering
KNOWN_TECH_SKILLS = {
    "python": "Python",
    "sql": "SQL",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "aws": "AWS",
    "azure": "Azure",
    "gcp": "GCP",
    "airflow": "Airflow",
    "dbt": "dbt",
    "snowflake": "Snowflake",
    "spark": "Spark",
    "pyspark": "Spark",
    "kafka": "Kafka",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "terraform": "Terraform",
    "power bi": "Power BI",
    "powerbi": "Power BI",
    "tableau": "Tableau",
    "react": "React",
    "fastapi": "FastAPI",
    "django": "Django",
    "node": "Node.js",
    "git": "Git",
    "linux": "Linux",
    "ci/cd": "CI/CD",
    "pandas": "Pandas",
    "pytorch": "PyTorch",
    "databricks": "Databricks",
    "bigquery": "BigQuery",
    "redshift": "Redshift",
}

SALARY_BENCHMARKS = {
    "Junior": 85000,
    "Mid": 115000,
    "Senior": 145000,
    "Lead": 165000,
    "Staff": 185000,
}


class DataTransformer:
    """Transforms raw Bronze job payloads into clean Silver & Gold dimensional tables."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        storage_cfg = self.config.get("storage", {})
        base_dir = Path(__file__).resolve().parent.parent
        self.raw_data_dir = base_dir / storage_cfg.get("raw_data_dir", "raw_data")
        self.clean_data_dir = base_dir / storage_cfg.get("clean_data_dir", "clean_data")
        self.clean_data_dir.mkdir(parents=True, exist_ok=True)

    def extract_skills(self, tags: List[str], text_content: str) -> List[str]:
        """Extracts and normalizes tech skills from tags and job description text."""
        detected = set()

        # Check explicit tags first
        for tag in tags:
            tag_clean = str(tag).strip().lower()
            if tag_clean in KNOWN_TECH_SKILLS:
                detected.add(KNOWN_TECH_SKILLS[tag_clean])

        # Regex scan description text for known skills
        lower_text = f" {text_content.lower()} "
        for pattern, normalized_name in KNOWN_TECH_SKILLS.items():
            # Match word boundary
            escaped_pat = re.escape(pattern)
            if re.search(r"\b" + escaped_pat + r"\b", lower_text):
                detected.add(normalized_name)

        return sorted(list(detected))

    def detect_seniority(self, title: str) -> str:
        """Determines seniority level from job title."""
        t = title.lower()
        if any(w in t for w in ["staff", "principal", "director", "head of", "vp"]):
            return "Staff"
        elif any(w in t for w in ["lead", "architect", "tech lead"]):
            return "Lead"
        elif any(w in t for w in ["sr.", "sr ", "senior"]):
            return "Senior"
        elif any(w in t for w in ["jr.", "jr ", "junior", "associate", "intern"]):
            return "Junior"
        return "Mid"

    def detect_remote_status(self, record: Dict[str, Any]) -> str:
        """Normalizes remote status to 'Fully Remote', 'Hybrid', or 'On-site'."""
        if "remote_status" in record and record["remote_status"]:
            st = str(record["remote_status"]).lower()
            if "hybrid" in st:
                return "Hybrid"
            elif "remote" in st:
                return "Fully Remote"
            elif "on-site" in st or "onsite" in st or "office" in st:
                return "On-site"

        location = str(record.get("candidate_required_location", "")).lower()
        title = str(record.get("title", "")).lower()
        desc = str(record.get("description", "")).lower()

        combined = f"{location} {title} {desc[:200]}"
        if "hybrid" in combined:
            return "Hybrid"
        elif "remote" in combined or "anywhere" in combined or "worldwide" in combined:
            return "Fully Remote"
        return "On-site"

    def parse_salary(self, record: Dict[str, Any], seniority: str) -> Tuple[float, float, float, bool]:
        """
        Extracts minimum, maximum, and average salary.
        Falls back to benchmark if missing, setting is_predicted flag.
        """
        # 1. Direct fields if numeric
        s_min = record.get("salary_min")
        s_max = record.get("salary_max")
        if isinstance(s_min, (int, float)) and isinstance(s_max, (int, float)) and s_min > 0 and s_max > 0:
            return float(s_min), float(s_max), float((s_min + s_max) / 2.0), False

        # 2. String parsing from 'salary' field
        salary_str = str(record.get("salary", ""))
        numbers = re.findall(r"\$?\s*([0-9]{2,3}(?:,[0-9]{3})*|\b[0-9]{2,3}k\b)", salary_str.lower())
        if len(numbers) >= 2:
            try:
                def clean_num(n_str):
                    n_str = n_str.replace("$", "").replace(",", "")
                    if "k" in n_str:
                        return float(n_str.replace("k", "")) * 1000
                    return float(n_str)

                parsed_min = clean_num(numbers[0])
                parsed_max = clean_num(numbers[1])
                if 20000 <= parsed_min <= 500000 and parsed_max >= parsed_min:
                    return parsed_min, parsed_max, (parsed_min + parsed_max) / 2.0, False
            except Exception:
                pass

        # 3. Benchmark estimate based on seniority
        base = SALARY_BENCHMARKS.get(seniority, 115000)
        return float(base * 0.9), float(base * 1.15), float(base), True

    def clean_html(self, raw_html: str) -> str:
        """Removes HTML tags from job descriptions."""
        cleanr = re.compile("<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});")
        return re.sub(cleanr, " ", raw_html or "").strip()

    def transform_records(self, raw_records: List[Dict[str, Any]], run_id: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Transforms a batch of raw records into Fact and Bridge DataFrames."""
        cleaned_jobs = []
        bridge_records = []
        seen_job_hashes = set()

        for rec in raw_records:
            title = str(rec.get("title", "Untitled Role")).strip()
            company = str(rec.get("company_name", "Unknown Employer")).strip()
            if not title or not company:
                continue

            # Deduplication key across runs
            content_sig = f"{company.lower()}_{title.lower()}"
            job_id = str(rec.get("id") or rec.get("job_id") or hashlib.md5(content_sig.encode()).hexdigest()[:12])

            # Deduplicate inside the batch
            if content_sig in seen_job_hashes:
                continue
            seen_job_hashes.add(content_sig)

            # Date normalization
            raw_date = rec.get("publication_date") or rec.get("date")
            try:
                if raw_date:
                    dt = pd.to_datetime(raw_date, utc=True)
                else:
                    dt = datetime.now(timezone.utc)
                posted_at = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                posted_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

            seniority = self.detect_seniority(title)
            remote_type = self.detect_remote_status(rec)
            s_min, s_max, s_avg, is_predicted = self.parse_salary(rec, seniority)

            desc = self.clean_html(rec.get("description", ""))
            tags = rec.get("tags", [])
            skills = self.extract_skills(tags, f"{title} {desc}")

            repost_status = rec.get("repost_status", "original")

            cleaned_jobs.append({
                "job_id": job_id,
                "run_id": run_id,
                "job_title": title,
                "normalized_title": self._normalize_role_title(title),
                "company_name": company,
                "category": rec.get("category", "Data & Engineering"),
                "seniority_level": seniority,
                "remote_type": remote_type,
                "location": str(rec.get("candidate_required_location", "Worldwide")),
                "salary_min": s_min,
                "salary_max": s_max,
                "salary_avg": s_avg,
                "currency": "USD",
                "is_salary_predicted": is_predicted,
                "job_url": str(rec.get("url", "")),
                "repost_status": repost_status,
                "posted_at": posted_at,
                "ingested_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            })

            for s in skills:
                bridge_records.append({
                    "job_id": job_id,
                    "skill_name": s
                })

        df_jobs = pd.DataFrame(cleaned_jobs)
        df_bridge = pd.DataFrame(bridge_records)

        return df_jobs, df_bridge

    def _normalize_role_title(self, title: str) -> str:
        t = title.lower()
        if "data engineer" in t:
            return "Data Engineer"
        elif "analytics engineer" in t:
            return "Analytics Engineer"
        elif "data architect" in t:
            return "Data Architect"
        elif "ml engineer" in t or "machine learning" in t:
            return "Machine Learning Engineer"
        elif "backend" in t or "software engineer" in t:
            return "Software Engineer"
        elif "data analyst" in t or "bi developer" in t:
            return "BI / Data Analyst"
        elif "devops" in t or "platform" in t:
            return "DevOps / DataOps Engineer"
        return title[:50]

    def process_all_bronze_partitions(self, run_id: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Scans all Bronze JSON files in raw_data/ and creates complete clean datasets."""
        all_raw_records = []

        for json_path in self.raw_data_dir.rglob("*.json"):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    records = content.get("raw_records", [])
                    all_raw_records.extend(records)
            except Exception as e:
                logger.warning(f"Error reading bronze file {json_path}: {e}")

        logger.info(f"Loaded {len(all_raw_records)} raw records from Bronze partitions. Transforming...")
        df_jobs, df_bridge = self.transform_records(all_raw_records, run_id)

        # Save to clean_data layer
        csv_path = self.clean_data_dir / "fact_jobs.csv"
        parquet_path = self.clean_data_dir / "fact_jobs.parquet"
        bridge_csv_path = self.clean_data_dir / "job_skills_bridge.csv"

        df_jobs.to_csv(csv_path, index=False)
        df_jobs.to_parquet(parquet_path, index=False)
        df_bridge.to_csv(bridge_csv_path, index=False)

        logger.info(f"Clean datasets saved: {len(df_jobs)} jobs -> {parquet_path} & {csv_path}")
        return df_jobs, df_bridge
