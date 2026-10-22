"""
PipelineOps Alerting Module
Handles failure notification dispatching via Webhook, Email, or Console.
Ensures no pipeline fails silently at 3 AM.
"""

import json
import logging
import smtplib
import sys
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional
import urllib.request
import urllib.error

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("PipelineOps.Alerting")


class PipelineAlertManager:
    """Manages failure and success alerts across multiple notification channels."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        alert_cfg = self.config.get("alerting", {})
        self.enabled = alert_cfg.get("enabled", True)
        self.channel = alert_cfg.get("channel", "console")
        self.webhook_url = alert_cfg.get("webhook_url", "")
        self.email_cfg = alert_cfg.get("email", {})
        self.notify_on_failure = alert_cfg.get("notify_on_failure", True)
        self.notify_on_success = alert_cfg.get("notify_on_success", False)

    def notify_failure(
        self,
        run_id: str,
        stage: str,
        error_message: str,
        traceback_str: Optional[str] = None,
        duration_seconds: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Dispatch failure alert immediately when a pipeline run or quality check fails."""
        if not self.enabled or not self.notify_on_failure:
            logger.info("Alerting disabled; skipping failure alert.")
            return {"status": "skipped"}

        timestamp = datetime.now(timezone.utc).isoformat()
        alert_payload = {
            "alert_type": "PIPELINE_FAILURE",
            "pipeline": self.config.get("pipeline", {}).get("name", "pipelineops"),
            "run_id": run_id,
            "failed_stage": stage,
            "error_message": error_message,
            "traceback": traceback_str,
            "duration_seconds": round(duration_seconds, 2),
            "timestamp": timestamp,
            "metadata": metadata or {},
        }

        logger.error(
            f"[ALERT] PIPELINE FAILURE DETECTED in stage '{stage}' for run {run_id}: {error_message}"
        )

        results = {}
        # 1. Always log structured alert to console
        self._send_console_alert(alert_payload)
        results["console"] = "sent"

        # 2. Webhook (Slack / Discord / Teams)
        if self.webhook_url:
            results["webhook"] = self._send_webhook_alert(alert_payload)

        # 3. Email
        if self.channel == "email" and self.email_cfg.get("sender"):
            results["email"] = self._send_email_alert(alert_payload)

        return results

    def notify_success(
        self,
        run_id: str,
        records_ingested: int,
        records_transformed: int,
        duration_seconds: float,
        quality_score: float = 100.0,
    ) -> Dict[str, Any]:
        """Dispatch success alert if configured."""
        if not self.enabled or not self.notify_on_success:
            return {"status": "skipped"}

        timestamp = datetime.now(timezone.utc).isoformat()
        alert_payload = {
            "alert_type": "PIPELINE_SUCCESS",
            "pipeline": self.config.get("pipeline", {}).get("name", "pipelineops"),
            "run_id": run_id,
            "records_ingested": records_ingested,
            "records_transformed": records_transformed,
            "quality_score_pct": round(quality_score, 1),
            "duration_seconds": round(duration_seconds, 2),
            "timestamp": timestamp,
        }

        logger.info(f"[SUCCESS] Pipeline run {run_id} completed successfully in {duration_seconds:.2f}s.")
        if self.webhook_url:
            return {"webhook": self._send_webhook_alert(alert_payload)}
        return {"console": "logged"}

    def _send_console_alert(self, payload: Dict[str, Any]) -> None:
        formatted = json.dumps(payload, indent=2)
        logger.error(f"===== ALERT DISPATCH =====\n{formatted}\n==========================")

    def _send_webhook_alert(self, payload: Dict[str, Any]) -> str:
        """Send formatted alert payload to Slack/Discord/generic incoming webhook."""
        try:
            # Format payload nicely for Slack or generic incoming webhooks
            if "hooks.slack.com" in self.webhook_url:
                msg = {
                    "text": f"🚨 *[PipelineOps Alert]* Pipeline Run Failed!\n"
                            f"*Run ID:* `{payload.get('run_id')}`\n"
                            f"*Stage:* `{payload.get('failed_stage')}`\n"
                            f"*Error:* {payload.get('error_message')}\n"
                            f"*Duration:* {payload.get('duration_seconds')}s"
                }
            elif "discord.com" in self.webhook_url:
                msg = {
                    "content": f"🚨 **[PipelineOps Alert]** Failure in stage **{payload.get('failed_stage')}**\n"
                               f"Run ID: `{payload.get('run_id')}`\n"
                               f"Error: `{payload.get('error_message')}`"
                }
            else:
                msg = payload

            data = json.dumps(msg).encode("utf-8")
            req = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers={"Content-Type": "application/json", "User-Agent": "PipelineOps-AlertBot/1.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                return f"success_http_{response.status}"
        except Exception as e:
            logger.warning(f"Failed to post webhook alert: {e}")
            return f"error: {str(e)}"

    def _send_email_alert(self, payload: Dict[str, Any]) -> str:
        """Send alert email via SMTP."""
        try:
            sender = self.email_cfg.get("sender")
            recipient = self.email_cfg.get("recipient")
            host = self.email_cfg.get("smtp_server", "localhost")
            port = self.email_cfg.get("smtp_port", 587)
            pwd = self.email_cfg.get("password")

            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🚨 PipelineOps Failure Alert: {payload.get('failed_stage')}"
            msg["From"] = sender
            msg["To"] = recipient

            text = (
                f"PipelineOps Failure Alert\n\n"
                f"Run ID: {payload.get('run_id')}\n"
                f"Stage: {payload.get('failed_stage')}\n"
                f"Error: {payload.get('error_message')}\n"
                f"Timestamp: {payload.get('timestamp')}\n\n"
                f"Traceback:\n{payload.get('traceback')}\n"
            )
            msg.attach(MIMEText(text, "plain"))

            with smtplib.SMTP(host, port, timeout=10) as server:
                server.starttls()
                if pwd:
                    server.login(sender, pwd)
                server.sendmail(sender, recipient, msg.as_string())
            return "email_sent"
        except Exception as e:
            logger.warning(f"Failed to send email alert: {e}")
            return f"error: {str(e)}"
