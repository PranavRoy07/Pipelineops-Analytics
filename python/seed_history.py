"""
PipelineOps Historical Data Seeder
Generates realistic multi-week historical raw pulls partitioned into raw_data/YYYY-MM-DD/.
Provides rich data for Week-over-Week trend analysis (Q1), Repost Cadence (Q3),
Remote vs On-site shift (Q4), and SciPy linear regressions.
"""

import hashlib
import json
import logging
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("PipelineOps.SeedHistory")

ROLES = [
    {"title": "Senior Data Engineer", "category": "Data Engineering", "base_salary": 145000, "skills": ["Python", "SQL", "Airflow", "PostgreSQL", "AWS", "Spark"]},
    {"title": "Data Engineer", "category": "Data Engineering", "base_salary": 115000, "skills": ["Python", "SQL", "dbt", "Snowflake", "Docker"]},
    {"title": "Junior Data Engineer", "category": "Data Engineering", "base_salary": 85000, "skills": ["Python", "SQL", "PostgreSQL", "Git"]},
    {"title": "Analytics Engineer", "category": "Analytics Engineering", "base_salary": 120000, "skills": ["SQL", "dbt", "Snowflake", "Power BI", "Python"]},
    {"title": "Staff Data Architect", "category": "Data Engineering", "base_salary": 185000, "skills": ["AWS", "Spark", "Kafka", "PostgreSQL", "Python", "Kubernetes"]},
    {"title": "Data Platform Engineer", "category": "DevOps / DataOps", "base_salary": 138000, "skills": ["Kubernetes", "Docker", "Terraform", "AWS", "Python"]},
    {"title": "Backend Software Engineer", "category": "Backend", "base_salary": 130000, "skills": ["Python", "Docker", "PostgreSQL", "FastAPI", "AWS"]},
    {"title": "Machine Learning Engineer", "category": "Machine Learning", "base_salary": 155000, "skills": ["Python", "PyTorch", "Docker", "AWS", "SQL"]},
    {"title": "BI Developer / Analyst", "category": "Business Intelligence", "base_salary": 95000, "skills": ["Power BI", "SQL", "Tableau", "Excel"]},
    {"title": "Cloud Data Specialist", "category": "Cloud Infrastructure", "base_salary": 140000, "skills": ["AWS", "Azure", "Terraform", "SQL", "Python"]},
]

COMPANIES = [
    {"name": "Stripe", "repost_tendency": 0.35, "remote_pref": "Fully Remote"},
    {"name": "Shopify", "repost_tendency": 0.40, "remote_pref": "Fully Remote"},
    {"name": "Datadog", "repost_tendency": 0.25, "remote_pref": "Hybrid"},
    {"name": "GitLab", "repost_tendency": 0.20, "remote_pref": "Fully Remote"},
    {"name": "Snowflake", "repost_tendency": 0.30, "remote_pref": "Hybrid"},
    {"name": "Capital One", "repost_tendency": 0.50, "remote_pref": "Hybrid"},
    {"name": "Spotify", "repost_tendency": 0.15, "remote_pref": "Fully Remote"},
    {"name": "Netflix", "repost_tendency": 0.10, "remote_pref": "On-site"},
    {"name": "Airbnb", "repost_tendency": 0.20, "remote_pref": "Fully Remote"},
    {"name": "Coinbase", "repost_tendency": 0.30, "remote_pref": "Fully Remote"},
    {"name": "Amazon AWS", "repost_tendency": 0.60, "remote_pref": "Hybrid"},
    {"name": "Brex", "repost_tendency": 0.25, "remote_pref": "Fully Remote"},
    {"name": "DoorDash", "repost_tendency": 0.35, "remote_pref": "Hybrid"},
    {"name": "Monzo Bank", "repost_tendency": 0.15, "remote_pref": "Fully Remote"},
    {"name": "Elastic", "repost_tendency": 0.20, "remote_pref": "Fully Remote"},
]

LOCATIONS = ["Remote, US", "Remote, Worldwide", "San Francisco, CA", "New York, NY", "London, UK", "Austin, TX", "Seattle, WA", "Remote, EU"]


def generate_sample_job_records(count: int = 35, day_offset: int = 0) -> List[Dict[str, Any]]:
    """Generates realistic job records with natural weekly trends and salary variance."""
    base_date = datetime.now(timezone.utc) - timedelta(days=day_offset)
    records = []

    # Trend modifier: Python, SQL, and AWS trend upwards over the 30-day window
    # As day_offset decreases (getting closer to today), demand for modern skills increases
    trend_factor = 1.0 + ((30 - day_offset) / 30.0) * 0.45

    for i in range(count):
        role_info = random.choice(ROLES)
        company_info = random.choice(COMPANIES)

        # Repost logic (Q3): repeat specific jobs every 7-14 days
        is_repost = random.random() < company_info["repost_tendency"]
        repost_tag = "repost" if is_repost else "original"

        # Unique or recurring ID
        base_id_seed = f"{company_info['name']}_{role_info['title']}"
        if is_repost:
            job_id = f"job_{hashlib.md5(base_id_seed.encode()).hexdigest()[:8]}"
        else:
            job_id = f"job_{hashlib.md5(f'{base_id_seed}_{day_offset}_{i}'.encode()).hexdigest()[:8]}"

        # Salary with standard deviation
        salary_jitter = random.gauss(0, 12000)
        salary_avg = max(55000, int(role_info["base_salary"] + salary_jitter))
        salary_min = int(salary_avg * 0.90)
        salary_max = int(salary_avg * 1.15)

        # Remote type shift (Q4)
        remote_prob = random.random()
        if company_info["remote_pref"] == "Fully Remote":
            remote_type = "Fully Remote" if remote_prob > 0.10 else "Hybrid"
        elif company_info["remote_pref"] == "Hybrid":
            remote_type = "Hybrid" if remote_prob > 0.30 else "On-site"
        else:
            remote_type = "On-site" if remote_prob > 0.40 else "Hybrid"

        # Skills list with trend weighting
        skills = list(role_info["skills"])
        if random.random() < 0.65 * trend_factor and "Python" not in skills:
            skills.append("Python")
        if random.random() < 0.55 * trend_factor and "SQL" not in skills:
            skills.append("SQL")
        if random.random() < 0.40 * trend_factor and "AWS" not in skills:
            skills.append("AWS")
        if random.random() < 0.35 and "Docker" not in skills:
            skills.append("Docker")

        posting_time = base_date - timedelta(hours=random.randint(1, 23), minutes=random.randint(0, 59))

        records.append({
            "id": job_id,
            "title": role_info["title"],
            "company_name": company_info["name"],
            "category": role_info["category"],
            "tags": skills,
            "job_type": "full_time",
            "publication_date": posting_time.isoformat(),
            "candidate_required_location": random.choice(LOCATIONS),
            "salary": f"${salary_min:,} - ${salary_max:,} USD",
            "salary_min": salary_min,
            "salary_max": salary_max,
            "description": f"<p>Exciting opportunity for a {role_info['title']} at {company_info['name']}. "
                           f"Required skills: {', '.join(skills)}. Remote policy: {remote_type}.</p>",
            "url": f"https://pipelineops.jobs/{company_info['name'].lower()}/{job_id}",
            "remote_status": remote_type,
            "repost_status": repost_tag,
        })

    return records


def seed_historical_bronze_layer(raw_data_dir: Path, days: int = 30) -> int:
    """
    Creates historical daily Bronze partitions: raw_data/YYYY-MM-DD/run_<timestamp>.json
    Ensures complete week-over-week analytical readiness.
    """
    total_records = 0
    now = datetime.now(timezone.utc)
    logger.info(f"Seeding {days} days of historical Bronze raw data partitions...")

    for day_offset in range(days, -1, -1):
        target_date = now - timedelta(days=day_offset)
        date_str = target_date.strftime("%Y-%m-%d")
        partition_dir = raw_data_dir / date_str
        partition_dir.mkdir(parents=True, exist_ok=True)

        run_id = f"run_{target_date.strftime('%Y%m%d')}_030000"
        filepath = partition_dir / f"{run_id}.json"

        # Slight variation in daily volume (weekday vs weekend)
        is_weekend = target_date.weekday() >= 5
        count = random.randint(15, 25) if is_weekend else random.randint(35, 55)
        records = generate_sample_job_records(count=count, day_offset=day_offset)

        payload = {
            "metadata": {
                "run_id": run_id,
                "source": "remotive_historical_seed",
                "ingested_at": target_date.isoformat(),
                "record_count": len(records),
                "is_seed": True,
            },
            "raw_records": records,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        total_records += len(records)

    logger.info(f"Historical seeding complete: {total_records} total raw records across {days + 1} daily partitions.")
    return total_records


if __name__ == "__main__":
    import yaml
    config_path = Path(__file__).resolve().parent.parent / "config.yaml"
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    raw_dir = Path(__file__).resolve().parent.parent / cfg["storage"]["raw_data_dir"]
    seed_historical_bronze_layer(raw_dir, days=30)
