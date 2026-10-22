"""
PipelineOps S3 Storage Adapter
Handles uploading Bronze raw data and Silver clean Parquet/CSV data to AWS S3
under a structured data lake prefix layout.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("PipelineOps.S3Uploader")


class S3LakeStorage:
    """Manages S3 data lake storage for Bronze (raw) and Silver (clean) layers."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        storage_cfg = self.config.get("storage", {})
        self.s3_cfg = storage_cfg.get("s3", {})
        self.enabled = self.s3_cfg.get("enabled", False)
        self.bucket = self.s3_cfg.get("bucket_name", "pipelineops-analytics-lake")
        self.bronze_prefix = self.s3_cfg.get("bronze_prefix", "bronze/")
        self.silver_prefix = self.s3_cfg.get("silver_prefix", "silver/")
        self.region = self.s3_cfg.get("region", "us-east-1")

    def upload_file(self, local_path: str, s3_key: str) -> bool:
        """Uploads a local file to S3 with server-side encryption AES-256."""
        if not self.enabled:
            logger.info(f"S3 integration is disabled; skipping upload for {local_path}.")
            return False

        try:
            import boto3
            from botocore.exceptions import ClientError

            s3_client = boto3.client(
                "s3",
                region_name=os.getenv("AWS_DEFAULT_REGION", self.region),
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            )

            logger.info(f"Uploading {local_path} -> s3://{self.bucket}/{s3_key}")
            s3_client.upload_file(
                local_path,
                self.bucket,
                s3_key,
                ExtraArgs={"ServerSideEncryption": "AES256"}
            )
            logger.info(f"Successfully uploaded to S3: s3://{self.bucket}/{s3_key}")
            return True

        except ImportError:
            logger.warning("boto3 is not installed; skipping S3 upload.")
            return False
        except Exception as e:
            logger.error(f"S3 upload failed for {local_path}: {e}")
            return False

    def sync_bronze_file(self, local_bronze_path: str) -> bool:
        """Syncs an immutable raw Bronze partition to S3."""
        filename = Path(local_bronze_path).name
        parent_date = Path(local_bronze_path).parent.name
        s3_key = f"{self.bronze_prefix}{parent_date}/{filename}"
        return self.upload_file(local_bronze_path, s3_key)

    def sync_silver_dataset(self, clean_parquet_path: str, clean_csv_path: Optional[str] = None) -> bool:
        """Syncs clean Silver dataset files to S3."""
        res = True
        if os.path.exists(clean_parquet_path):
            s3_key = f"{self.silver_prefix}{Path(clean_parquet_path).name}"
            res = self.upload_file(clean_parquet_path, s3_key) and res

        if clean_csv_path and os.path.exists(clean_csv_path):
            s3_key = f"{self.silver_prefix}{Path(clean_csv_path).name}"
            res = self.upload_file(clean_csv_path, s3_key) and res

        return res
